package com.practice.qabank.functional.journey;

import static com.practice.qabank.functional.RequestSpec.USER_ID;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;
import java.util.function.BiPredicate;

import com.practice.qabank.functional.journey.TestUser.Sent;

// Turns the Mix table of UserJourneys.md into one busy-day round of ops, with Random(seed) picking the actors, targets,
// directions and order. Every pick is by position, in the user pool or in the ledger's insertion order at round start,
// never by id value. Picks read only facts that don't depend on which request of a race won: who wrote what, who
// voted on or answered what, and which tags a question holds. So one seed plans the same day in both modes. A kind with
// no candidate throws; the profiles are sized so that it never happens.
final class MixPlanner {

    // A Mix row, and its ops per round before × m. A double-click is two ops, one per request.
    enum Kind {
        CREATE(1),
        ADD(3),
        VOTE(10),
        EDIT(1),
        GET(6),
        WALK(2),
        RETRY(2),
        RULE_BREAKER(2),
        DOUBLE_CLICK(2);

        private final int perRound;

        Kind(int perRound) {
            this.perRound = perRound;
        }

        int perRound() {
            return perRound;
        }
    }

    // What an op must get back: a status in statuses and, for a rejection, its error code. A double-click's two ops
    // share a pair number above 0 and allow 201 or 409 each, since either may win.
    record Outcome(Set<Integer> statuses, String error, int pair) {

        static Outcome status(int status) {
            return new Outcome(Set.of(status), null, 0);
        }

        static Outcome rejected(int status, String error) {
            return new Outcome(Set.of(status), error, 0);
        }
    }

    // One op. answerId null means the question itself. tags are a create's or question edit's tags, or a walk's tag,
    // and limit is a walk's page size. retried is the write a retry sends again, as its own user.
    record Op(Kind kind, String actor, String questionId, String answerId, Direction direction, List<String> tags,
            int limit, Sent retried, Outcome expected) {
    }

    // The 8 write operations a retry cycles through, as method and path with the ids left out.
    private static final List<String> RETRY_CYCLE = List.of(
            "POST /questions",
            "POST /questions/{id}/answers",
            "PUT /questions/{id}",
            "PUT /questions/{id}/answers/{id}",
            "POST /questions/{id}/upvotes",
            "POST /questions/{id}/downvotes",
            "POST /questions/{id}/answers/{id}/upvotes",
            "POST /questions/{id}/answers/{id}/downvotes");
    private static final String UUID_PATTERN = "[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}";

    private final Random random;
    private final Profile profile;
    private final List<String> users;
    private final String tag;
    private final String otherTag;
    // Turns taken so far, across rounds: each cycle carries on where the last round stopped.
    private int retries;
    private int ruleBreakers;
    private int doubleClicks;

    // The round being planned. used holds the (user, target) pairs that already vote or answer in it.
    private int round;
    private Ledger ledger;
    private final Set<String> used = new HashSet<>();
    private final Set<String> edited = new HashSet<>();

    // users is the day's pool, in a fixed order. Questions are created with tag, and edits add or drop otherTag.
    MixPlanner(long seed, Profile profile, List<String> users, String tag, String otherTag) {
        this.random = new Random(seed);
        this.profile = profile;
        this.users = List.copyOf(users);
        this.tag = tag;
        this.otherTag = otherTag;
    }

    // The Mix × m, in a seeded order. Everything is picked from the ledger as it is now, at round start.
    List<Op> plan(int round, Ledger ledger) {
        this.round = round;
        this.ledger = ledger;
        used.clear();
        edited.clear();
        List<Op> ops = new ArrayList<>();
        for (int i = 0; i < profile.scale(); i++) {
            ops.add(create());
            for (int j = 0; j < 3; j++) {
                ops.add(add());
            }
            for (int j = 0; j < 10; j++) {
                ops.add(vote());
            }
            ops.add(edit());
            for (int j = 0; j < 6; j++) {
                ops.add(get());
            }
            for (int j = 0; j < 2; j++) {
                ops.add(walk());
            }
            for (int j = 0; j < 2; j++) {
                ops.add(retry());
            }
            for (int j = 0; j < 2; j++) {
                ops.add(ruleBreaker());
            }
            ops.addAll(doubleClick());
        }
        Collections.shuffle(ops, random);
        return ops;
    }

    private Op create() {
        return op(Kind.CREATE, anyUser(), null, null, List.of(tag), Outcome.status(201));
    }

    private Op add() {
        Pick pick = pick("an answer", ledger.questionIds(), this::canAnswer);
        used.add(pick.key());
        return op(Kind.ADD, pick.user(), pick.target(), null, null, Outcome.status(201));
    }

    // Question 1 : answer 2, and UP 2 : DOWN 1.
    private Op vote() {
        Pick pick = pick("a vote", random.nextInt(3) == 0 ? ledger.questionIds() : ledger.answerIds(), this::canVote);
        used.add(pick.key());
        Direction direction = random.nextInt(3) < 2 ? Direction.UP : Direction.DOWN;
        return vote(Kind.VOTE, pick.user(), pick.target(), direction, Outcome.status(201));
    }

    // By the author, on a target not edited yet this round. A question keeps tag, and the seed says whether it holds
    // otherTag after, so retags join the mix.
    private Op edit() {
        boolean question = random.nextBoolean();
        Pick pick = pick("an edit", question ? ledger.questionIds() : ledger.answerIds(),
                (target, user) -> !edited.contains(target) && user.equals(ledger.authorOf(target)));
        edited.add(pick.target());
        if (question) {
            List<String> tags = random.nextBoolean() ? List.of(tag, otherTag) : List.of(tag);
            return op(Kind.EDIT, pick.user(), pick.target(), null, tags, Outcome.status(200));
        }
        return op(Kind.EDIT, pick.user(), ledger.questionOf(pick.target()), pick.target(), null,
                Outcome.status(200));
    }

    // GET question or GET answer, 1 : 1.
    private Op get() {
        List<String> targets = random.nextBoolean() ? ledger.questionIds() : ledger.answerIds();
        String target = targets.get(random.nextInt(targets.size()));
        String questionId = ledger.questionOf(target);
        return questionId == null
                ? op(Kind.GET, anyUser(), target, null, null, Outcome.status(200))
                : op(Kind.GET, anyUser(), questionId, target, null, Outcome.status(200));
    }

    // tag or otherTag, 1 : 1, with a limit from 1 to 10.
    private Op walk() {
        String walked = random.nextBoolean() ? tag : otherTag;
        return new Op(Kind.WALK, anyUser(), null, null, null, List.of(walked), 1 + random.nextInt(10), null,
                Outcome.status(200));
    }

    // The next write operation in the cycle, and one write of it accepted before this round, sent again as its user.
    private Op retry() {
        String operation = RETRY_CYCLE.get(retries++ % RETRY_CYCLE.size());
        List<Sent> candidates = ledger.writes().stream().filter(sent -> operation(sent).equals(operation)).toList();
        if (candidates.isEmpty()) {
            throw new IllegalStateException("No accepted " + operation + " to retry in round " + round);
        }
        Sent sent = candidates.get(random.nextInt(candidates.size()));
        return new Op(Kind.RETRY, sent.request().header(USER_ID), null, null, null, null, 0, sent,
                Outcome.status(sent.first().status()));
    }

    // In turn: self-vote, repeat vote, second answer, non-owner edit. Each is built from the ledger at round start so
    // it fails whatever else runs this round.
    private Op ruleBreaker() {
        return switch (ruleBreakers++ % 4) {
            case 0 -> selfVote();
            case 1 -> repeatVote();
            case 2 -> secondAnswer();
            default -> nonOwnerEdit();
        };
    }

    private Op selfVote() {
        Pick pick = pick("a self-vote", random.nextBoolean() ? ledger.questionIds() : ledger.answerIds(),
                (target, user) -> user.equals(ledger.authorOf(target)));
        Direction direction = random.nextBoolean() ? Direction.UP : Direction.DOWN;
        return vote(Kind.RULE_BREAKER, pick.user(), pick.target(), direction,
                Outcome.rejected(403, direction.ownCode()));
    }

    // In either direction, under a new key. The 409 names the vote already held.
    private Op repeatVote() {
        List<String> targets = new ArrayList<>(ledger.questionIds());
        targets.addAll(ledger.answerIds());
        Pick pick = pick("a repeat vote", targets, (target, user) -> ledger.voteOf(target, user) != null);
        used.add(pick.key());
        Direction direction = random.nextBoolean() ? Direction.UP : Direction.DOWN;
        Direction held = ledger.voteOf(pick.target(), pick.user());
        return vote(Kind.RULE_BREAKER, pick.user(), pick.target(), direction,
                Outcome.rejected(409, held.alreadyCode()));
    }

    private Op secondAnswer() {
        Pick pick = pick("a second answer", ledger.questionIds(), ledger::hasAnswered);
        used.add(pick.key());
        return op(Kind.RULE_BREAKER, pick.user(), pick.target(), null, null,
                Outcome.rejected(409, "ANSWER_ALREADY_EXISTS"));
    }

    // A question or an answer, 1 : 1, by anyone but its author.
    private Op nonOwnerEdit() {
        boolean question = random.nextBoolean();
        Pick pick = pick("a non-owner edit", question ? ledger.questionIds() : ledger.answerIds(),
                (target, user) -> !user.equals(ledger.authorOf(target)));
        if (question) {
            return op(Kind.RULE_BREAKER, pick.user(), pick.target(), null, List.of(tag),
                    Outcome.rejected(403, "NOT_QUESTION_OWNER"));
        }
        return op(Kind.RULE_BREAKER, pick.user(), ledger.questionOf(pick.target()), pick.target(), null,
                Outcome.rejected(403, "NOT_ANSWER_OWNER"));
    }

    // One user, two conflicting writes under two keys, in turn: an up and a down vote on one target, or two answers to
    // one question. The pair can't vote or answer anywhere else this round.
    private List<Op> doubleClick() {
        int pair = ++doubleClicks;
        Outcome expected = new Outcome(Set.of(201, 409), null, pair);
        if (pair % 2 == 1) {
            Pick pick = pick("a double-click vote",
                    random.nextInt(3) == 0 ? ledger.questionIds() : ledger.answerIds(), this::canVote);
            used.add(pick.key());
            return List.of(vote(Kind.DOUBLE_CLICK, pick.user(), pick.target(), Direction.UP, expected),
                    vote(Kind.DOUBLE_CLICK, pick.user(), pick.target(), Direction.DOWN, expected));
        }
        Pick pick = pick("a double-click answer", ledger.questionIds(), this::canAnswer);
        used.add(pick.key());
        Op answer = op(Kind.DOUBLE_CLICK, pick.user(), pick.target(), null, null, expected);
        return List.of(answer, answer);
    }

    private boolean canAnswer(String questionId, String user) {
        return !ledger.hasAnswered(questionId, user) && !used.contains(new Pick(questionId, user).key());
    }

    private boolean canVote(String targetId, String user) {
        return !user.equals(ledger.authorOf(targetId)) && ledger.voteOf(targetId, user) == null
                && !used.contains(new Pick(targetId, user).key());
    }

    // A target at a random position, then a random user who fits it. From there it tries each target in turn, so it
    // fails only when no pair fits at all.
    private Pick pick(String what, List<String> targets, BiPredicate<String, String> fits) {
        if (targets.isEmpty()) {
            throw new IllegalStateException("No target for " + what + " in round " + round);
        }
        int start = random.nextInt(targets.size());
        for (int i = 0; i < targets.size(); i++) {
            String target = targets.get((start + i) % targets.size());
            List<String> candidates = users.stream().filter(user -> fits.test(target, user)).toList();
            if (!candidates.isEmpty()) {
                return new Pick(target, candidates.get(random.nextInt(candidates.size())));
            }
        }
        throw new IllegalStateException("No candidate for " + what + " in round " + round);
    }

    private String anyUser() {
        return users.get(random.nextInt(users.size()));
    }

    // Any op but a vote, a walk or a retry.
    private Op op(Kind kind, String actor, String questionId, String answerId, List<String> tags, Outcome expected) {
        return new Op(kind, actor, questionId, answerId, null, tags, 0, null, expected);
    }

    // targetId is a question or an answer: the ledger knows an answer's question.
    private Op vote(Kind kind, String actor, String targetId, Direction direction, Outcome expected) {
        String questionId = ledger.questionOf(targetId);
        return questionId == null
                ? new Op(kind, actor, targetId, null, direction, null, 0, null, expected)
                : new Op(kind, actor, questionId, targetId, direction, null, 0, null, expected);
    }

    private static String operation(Sent sent) {
        return sent.method() + " " + sent.path().replaceAll(UUID_PATTERN, "{id}");
    }

    private record Pick(String target, String user) {

        String key() {
            return user + " " + target;
        }
    }
}
