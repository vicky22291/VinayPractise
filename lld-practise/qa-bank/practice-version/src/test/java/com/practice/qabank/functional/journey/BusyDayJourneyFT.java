package com.practice.qabank.functional.journey;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.qabank.functional.ApiClient;
import com.practice.qabank.functional.ApiResponse;
import com.practice.qabank.functional.journey.MixPlanner.Kind;
import com.practice.qabank.functional.journey.MixPlanner.Op;
import com.practice.qabank.functional.journey.MixPlanner.Outcome;
import com.practice.qabank.functional.journey.TestUser.Sent;

// The busy day journey (UserJourneys.md) against a running app (see qabank.baseUrl). A pool of users calls every API in
// rounds that MixPlanner draws from the seed, with retries of earlier writes, rule-breakers and double-clicks mixed in.
// SEQUENTIAL sends one op at a time and checks each response exactly against the ledger. CONCURRENT sends each round
// at once, checks statuses, replays and walks, then folds the 2xx in plan order. Both compare every question with the
// ledger at each round's barrier, and every answer and both tag lists at the end. Every failure names the seed, so
// -Djourney.seed=<s> replays the same day in both modes.
@Tag("journey")
class BusyDayJourneyFT {

    // How a round's ops run.
    enum Mode {
        SEQUENTIAL,
        CONCURRENT
    }

    // One seed per run, so both modes of a profile plan the same day.
    private static final long SEED = Long.getLong("journey.seed", System.nanoTime());
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final Set<Kind> WRITES =
            EnumSet.of(Kind.CREATE, Kind.ADD, Kind.VOTE, Kind.EDIT, Kind.RULE_BREAKER, Kind.DOUBLE_CLICK);
    private static final int END_LIMIT = 7;

    private final ApiClient api = new ApiClient();
    private final Ledger ledger = new Ledger();
    private final Map<String, TestUser> users = new LinkedHashMap<>();
    // Each question's body at the last barrier, for the end's GET answer checks.
    private final Map<String, Map<String, Object>> lastSeen = new HashMap<>();
    // SEQUENTIAL: the first op of each double-click in plan order, and its response.
    private final Map<Integer, Op> pairFirst = new HashMap<>();
    private final Map<Integer, ApiResponse> pairFirstResponse = new HashMap<>();
    private Profile profile;
    private Mode mode;
    private String tag;
    private String otherTag;
    // Where the day is: every failure starts with it.
    private String where = "";

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("profilesAndModes")
    @Timeout(120)
    void busyDay(Profile profile, Mode mode) {
        this.profile = profile;
        this.mode = mode;
        tag = TestUser.freshTag();
        otherTag = TestUser.freshTag();
        for (int i = 0; i < profile.users(); i++) {
            TestUser user = TestUser.fresh(api);
            users.put(user.id(), user);
        }
        System.out.printf("BusyDayJourneyFT seed=%d profile=%s mode=%s%n", SEED, profile, mode);
        try {
            day();
        } catch (AssertionError | Exception e) {
            throw new AssertionError(where + ": " + e.getMessage(), e);
        }
    }

    static Stream<Arguments> profilesAndModes() {
        return Stream.of(Profile.values())
                .flatMap(profile -> Stream.of(Mode.values()).map(mode -> arguments(profile, mode)));
    }

    private void day() throws Exception {
        warmUp();
        MixPlanner planner = new MixPlanner(SEED, profile, List.copyOf(users.keySet()), tag, otherTag);
        for (int round = 1; round <= profile.rounds(); round++) {
            at(round, "plan");
            List<Op> ops = planner.plan(round, ledger);
            checkPlan(ops);
            if (mode == Mode.SEQUENTIAL) {
                runSequential(round, ops);
            } else {
                runConcurrent(round, ops);
            }
            barrier(round);
        }
        end();
    }

    // One call at a time: 3m users each ask a question, and 2 others answer each one. Then a retagging PUT question, a
    // PUT answer, and a vote on each of the 4 endpoints, so every retry and rule-breaker has a candidate from round 1.
    private void warmUp() {
        List<TestUser> pool = List.copyOf(users.values());
        int questions = 3 * profile.scale();
        for (int i = 0; i < questions; i++) {
            TestUser asker = pool.get(i);
            at(0, "warm-up, question " + i);
            Map<String, Object> asked = warm(asker, asker.ask(content("Busy day question"), tag), 201);
            ledger.recordQuestion(asked);
            String questionId = (String) asked.get("id");
            for (int j = 0; j < 2; j++) {
                TestUser answerer = pool.get(questions + 2 * i + j);
                Map<String, Object> added =
                        warm(answerer, answerer.answer(questionId, content("Busy day answer")), 201);
                ledger.recordAnswer(questionId, added, 0);
            }
        }
        String first = ledger.questionIds().get(0);
        String second = ledger.questionIds().get(1);
        List<String> answers = ledger.answerIds();
        at(0, "warm-up, edits and votes");
        TestUser questionAuthor = users.get(ledger.authorOf(first));
        ApiResponse retagged = questionAuthor.editQuestion(first, content("Busy day edit"), tag, otherTag);
        ledger.recordEdit(warm(questionAuthor, retagged, 200));
        TestUser answerAuthor = users.get(ledger.authorOf(answers.get(0)));
        ApiResponse edited = answerAuthor.editAnswer(first, answers.get(0), content("Busy day edit"));
        ledger.recordEdit(warm(answerAuthor, edited, 200));
        TestUser voter = pool.get(pool.size() - 1);
        warmVote(voter, Direction.UP, first, null);
        warmVote(voter, Direction.DOWN, second, null);
        warmVote(voter, Direction.UP, first, answers.get(0));
        warmVote(voter, Direction.DOWN, first, answers.get(1));
    }

    private void warmVote(TestUser voter, Direction direction, String questionId, String answerId) {
        warm(voter, voter.vote(direction, questionId, answerId), 201);
        ledger.recordVote(answerId == null ? questionId : answerId, voter.id(), direction);
    }

    // Asserts the status and keeps the write for retries. Returns the body.
    private Map<String, Object> warm(TestUser user, ApiResponse response, int status) {
        assertThat(response.status()).as(response.body()).isEqualTo(status);
        ledger.recordWrite(sentOf(user, response));
        return body(response);
    }

    // Exactly the Mix counts per kind, × m, and two ops per double-click, so a planner bug can't quietly leave out the
    // conflicts.
    private void checkPlan(List<Op> ops) {
        Map<Kind, Long> counts = ops.stream()
                .collect(Collectors.groupingBy(Op::kind, () -> new EnumMap<>(Kind.class), Collectors.counting()));
        for (Kind kind : Kind.values()) {
            assertThat(counts.getOrDefault(kind, 0L)).as("%s ops in the plan", kind)
                    .isEqualTo((long) kind.perRound() * profile.scale());
        }
        Map<Integer, Long> pairs = ops.stream()
                .filter(op -> op.expected().pair() != 0)
                .collect(Collectors.groupingBy(op -> op.expected().pair(), Collectors.counting()));
        assertThat(pairs.values()).as("ops per double-click").containsOnly(2L);
    }

    // Each op, then its fold, then its check against the ledger with it folded in.
    private void runSequential(int round, List<Op> ops) {
        for (int i = 0; i < ops.size(); i++) {
            Op op = ops.get(i);
            at(round, i, op);
            Object result = execute(op);
            fold(round, op, result);
            checkOp(op, result);
        }
    }

    // Every op at once. The checks run against the ledger as it was at round start, and then the 2xx are folded in
    // plan order. A double-click's winner is folded in place of the pair's first op, so the ledger's order, and with
    // it the next round's plan, doesn't depend on which request won.
    private void runConcurrent(int round, List<Op> ops) throws Exception {
        at(round, "all " + ops.size() + " ops at once");
        List<Callable<Object>> calls = ops.stream().<Callable<Object>>map(op -> () -> execute(op)).toList();
        List<Object> results = Concurrently.run(calls);
        checkRound(round, ops, results);
        Set<Integer> folded = new HashSet<>();
        for (int i = 0; i < ops.size(); i++) {
            int pair = ops.get(i).expected().pair();
            if (pair == 0) {
                fold(round, ops.get(i), results.get(i));
            } else if (folded.add(pair)) {
                int winner = winner(pairOf(ops, pair), results);
                fold(round, ops.get(winner), results.get(winner));
            }
        }
    }

    // A walk returns its pages, and every other op its one response.
    private Object execute(Op op) {
        TestUser user = users.get(op.actor());
        return switch (op.kind()) {
            case WALK -> user.walk(op.tags().get(0), op.limit());
            case GET -> op.answerId() == null
                    ? user.getQuestion(op.questionId())
                    : user.getAnswer(op.questionId(), op.answerId());
            case RETRY -> user.retry(op.retried());
            default -> write(user, op);
        };
    }

    // Every other kind is one write, and its fields say which: a direction is a vote, no question is a create, tags
    // are a question edit, an answer is an answer edit, and anything else adds an answer.
    private ApiResponse write(TestUser user, Op op) {
        if (op.direction() != null) {
            return user.vote(op.direction(), op.questionId(), op.answerId());
        }
        if (op.questionId() == null) {
            return user.ask(content("Busy day question"), op.tags().toArray(String[]::new));
        }
        if (op.tags() != null) {
            return user.editQuestion(op.questionId(), content("Busy day edit"), op.tags().toArray(String[]::new));
        }
        if (op.answerId() != null) {
            return user.editAnswer(op.questionId(), op.answerId(), content("Busy day edit"));
        }
        return user.answer(op.questionId(), content("Busy day answer"));
    }

    // Records a 2xx write in the ledger. Replays and reads are never folded, and a double-click's winner isn't kept for
    // retries, since which one wins differs between modes.
    private void fold(int round, Op op, Object result) {
        if (!WRITES.contains(op.kind()) || !(result instanceof ApiResponse response) || response.status() / 100 != 2) {
            return;
        }
        Map<String, Object> body = body(response);
        if (op.direction() != null) {
            ledger.recordVote(targetOf(op), op.actor(), op.direction());
        } else if (op.questionId() == null) {
            ledger.recordQuestion(body);
        } else if (op.tags() != null || op.answerId() != null) {
            ledger.recordEdit(body);
        } else {
            ledger.recordAnswer(op.questionId(), body, round);
        }
        if (op.expected().pair() == 0) {
            ledger.recordWrite(sentOf(users.get(op.actor()), response));
        }
    }

    // SEQUENTIAL, right after the op is folded: every response is exact.
    private void checkOp(Op op, Object result) {
        if (op.kind() == Kind.WALK) {
            List<Map<String, Object>> items = TestUser.items(pages(result), op.limit());
            assertThat(items).as("walk").isEqualTo(ledger.expectedList(op.tags().get(0)));
            return;
        }
        ApiResponse response = (ApiResponse) result;
        int pair = op.expected().pair();
        if (pair != 0 && pairFirst.containsKey(pair)) {
            checkLoser(pairFirst.get(pair), pairFirstResponse.get(pair), response);
            return;
        }
        if (pair != 0) {
            pairFirst.put(pair, op);
            pairFirstResponse.put(pair, response);
            assertThat(response.status()).as("first of double-click: %s", response.body()).isEqualTo(201);
        } else {
            checkStatus(op, response);
        }
        if (op.kind() == Kind.RETRY) {
            checkRetry(op, response);
        } else if (op.kind() == Kind.GET) {
            Map<String, Object> expected = op.answerId() == null
                    ? ledger.expectedQuestion(op.questionId())
                    : ledger.expectedAnswer(op.answerId());
            assertThat(body(response)).as("GET").isEqualTo(expected);
        } else if (response.status() / 100 == 2) {
            checkWrite(op, response);
        }
    }

    // A 2xx write's body: a vote's count, or the question or answer with the ledger's counts and answers.
    private void checkWrite(Op op, ApiResponse response) {
        Map<String, Object> body = body(response);
        if (op.direction() != null) {
            int count = ledger.count(targetOf(op), op.direction());
            assertThat(body).as("vote body").isEqualTo(Map.of(op.direction().countField(), count));
            return;
        }
        String id = (String) body.get("id");
        boolean question = op.questionId() == null || op.tags() != null;
        assertThat(body).as("write body")
                .isEqualTo(question ? ledger.expectedQuestion(id) : ledger.expectedAnswer(id));
    }

    // CONCURRENT, after every op has returned and before the fold, so the ledger still shows round start. A walk holds
    // every question that keeps its tag through the round: all of them for tag, and for otherTag those that held it
    // and weren't edited this round.
    private void checkRound(int round, List<Op> ops, List<Object> results) {
        Set<String> retagged = ops.stream()
                .filter(op -> op.kind() == Kind.EDIT && op.tags() != null)
                .map(Op::questionId)
                .collect(Collectors.toSet());
        List<String> keepTag = ledger.questionIds();
        List<String> keepOtherTag = keepTag.stream()
                .filter(id -> ledger.tagsOf(id).contains(otherTag) && !retagged.contains(id))
                .toList();
        for (int i = 0; i < ops.size(); i++) {
            Op op = ops.get(i);
            at(round, i, op);
            if (op.kind() == Kind.WALK) {
                List<Map<String, Object>> items = TestUser.items(pages(results.get(i)), op.limit());
                for (int j = 1; j < items.size(); j++) {
                    assertThat(Ledger.NEWEST_FIRST.compare(items.get(j - 1), items.get(j)))
                            .as("item %d before item %d, newest first and no duplicates", j - 1, j).isNegative();
                }
                assertThat(items).extracting(item -> (String) item.get("id"))
                        .containsAll(op.tags().get(0).equals(tag) ? keepTag : keepOtherTag);
            } else if (op.expected().pair() == 0) {
                ApiResponse response = (ApiResponse) results.get(i);
                checkStatus(op, response);
                if (op.kind() == Kind.RETRY) {
                    checkRetry(op, response);
                }
            }
        }
        Set<Integer> pairs = ops.stream().map(op -> op.expected().pair()).filter(pair -> pair != 0)
                .collect(Collectors.toSet());
        for (int pair : pairs) {
            List<Integer> both = pairOf(ops, pair);
            at(round, "double-click " + pair + " at ops " + both + ": " + describe(ops.get(both.get(0))));
            int winner = winner(both, results);
            int loser = both.get(0) == winner ? both.get(1) : both.get(0);
            ApiResponse won = (ApiResponse) results.get(winner);
            assertThat(won.status()).as("winner of double-click: %s", won.body()).isEqualTo(201);
            checkLoser(ops.get(winner), won, (ApiResponse) results.get(loser));
        }
    }

    // GET every question of the day: the ledger's counts on it and its answers, and its answers in order. SEQUENTIAL
    // expects the ledger's order exactly. CONCURRENT expects each round's answers in any order, after earlier rounds'.
    private void barrier(int round) {
        for (String questionId : ledger.questionIds()) {
            at(round, "barrier, GET question " + questionId);
            Map<String, Object> question = read(users.values().iterator().next().getQuestion(questionId));
            List<String> ids = answerIds(question);
            assertThat(ledger.checkAnswerOrder(questionId, ids)).as("answer order").isEmpty();
            Map<String, Object> expected = ledger.expectedQuestion(questionId);
            assertThat(question).as("GET question")
                    .isEqualTo(mode == Mode.SEQUENTIAL ? expected : inOrder(expected, ids));
            lastSeen.put(questionId, question);
        }
    }

    // Every answer equals its entry in the last barrier's GET question and the ledger. Both tag lists are exact.
    @SuppressWarnings("unchecked")
    private void end() {
        TestUser reader = users.values().iterator().next();
        for (String answerId : ledger.answerIds()) {
            String questionId = ledger.questionOf(answerId);
            at("end", "GET answer " + answerId + " of question " + questionId);
            Map<String, Object> entry = ((List<Map<String, Object>>) lastSeen.get(questionId).get("answers"))
                    .stream().filter(answer -> answerId.equals(answer.get("id"))).findFirst().orElseThrow();
            assertThat(read(reader.getAnswer(questionId, answerId))).as("GET answer")
                    .isEqualTo(entry).isEqualTo(ledger.expectedAnswer(answerId));
        }
        for (String walked : List.of(tag, otherTag)) {
            at("end", "walk tag=" + walked);
            List<Map<String, Object>> items = TestUser.items(reader.walk(walked, END_LIMIT), END_LIMIT);
            assertThat(items).as("walk").isEqualTo(ledger.expectedList(walked));
        }
    }

    private static void checkStatus(Op op, ApiResponse response) {
        assertThat(response.status()).as(response.body()).isIn(op.expected().statuses());
        if (op.expected().error() != null) {
            assertThat(response.json("$.error")).as(response.body()).isEqualTo(op.expected().error());
        }
    }

    // The original status, Location and body byte for byte, marked as a replay. Every body is built from the stored
    // result, counts included, so a create replay still has no answers and no votes.
    private static void checkRetry(Op op, ApiResponse retry) {
        ApiResponse first = op.retried().first();
        assertThat(retry.status()).as(retry.body()).isEqualTo(first.status());
        assertThat(retry.header("Location")).as("Location").isEqualTo(first.header("Location"));
        assertThat(retry.header(REPLAYED)).as(REPLAYED).contains("true");
        assertThat(retry.body()).as("replayed body").isEqualTo(first.body());
    }

    // The losing request of a double-click: 409, with the code naming the vote held, or the message naming the answer.
    private static void checkLoser(Op winner, ApiResponse won, ApiResponse lost) {
        assertThat(lost.status()).as("loser of double-click: %s", lost.body()).isEqualTo(409);
        if (winner.direction() != null) {
            assertThat(lost.json("$.error")).as(lost.body()).isEqualTo(winner.direction().alreadyCode());
        } else {
            assertThat(lost.json("$.error")).as(lost.body()).isEqualTo("ANSWER_ALREADY_EXISTS");
            assertThat((String) lost.json("$.message")).contains((String) won.json("$.id"));
        }
    }

    // The positions of a double-click's two ops, in plan order.
    private static List<Integer> pairOf(List<Op> ops, int pair) {
        return IntStream.range(0, ops.size()).filter(i -> ops.get(i).expected().pair() == pair).boxed().toList();
    }

    // The one op of the pair that got a 2xx.
    private static int winner(List<Integer> pair, List<Object> results) {
        List<Integer> won = pair.stream().filter(i -> ((ApiResponse) results.get(i)).status() / 100 == 2).toList();
        assertThat(won).as("double-click ops with a 2xx: %s", pair.stream()
                .map(i -> ((ApiResponse) results.get(i)).body()).toList()).hasSize(1);
        return won.get(0);
    }

    // expected with its answers in the order of ids, once checkAnswerOrder has passed.
    @SuppressWarnings("unchecked")
    private static Map<String, Object> inOrder(Map<String, Object> expected, List<String> ids) {
        Map<String, Object> byId = ((List<Map<String, Object>>) expected.get("answers")).stream()
                .collect(Collectors.toMap(answer -> (String) answer.get("id"), answer -> answer));
        Map<String, Object> reordered = new LinkedHashMap<>(expected);
        reordered.put("answers", ids.stream().map(byId::get).toList());
        return reordered;
    }

    // The Sent that got this response: TestUser keeps every write with the response it first got.
    private static Sent sentOf(TestUser user, ApiResponse response) {
        return user.sent().stream().filter(sent -> sent.first() == response).findFirst().orElseThrow();
    }

    private static String targetOf(Op op) {
        return op.answerId() != null ? op.answerId() : op.questionId();
    }

    private void at(Object round, String step) {
        where = "seed=" + SEED + ", profile=" + profile + ", mode=" + mode + ", round=" + round + ", " + step;
    }

    private void at(int round, int index, Op op) {
        at(round, "op=" + index + " " + describe(op));
    }

    private static String describe(Op op) {
        List<String> parts = new ArrayList<>(List.of(op.kind().name(), "by " + op.actor()));
        if (op.retried() != null) {
            parts.add(op.retried().method() + " " + op.retried().path());
        }
        if (op.direction() != null) {
            parts.add(op.direction().name());
        }
        if (op.questionId() != null) {
            parts.add("question " + op.questionId());
        }
        if (op.answerId() != null) {
            parts.add("answer " + op.answerId());
        }
        if (op.tags() != null) {
            parts.add("tags " + op.tags());
        }
        if (op.kind() == Kind.WALK) {
            parts.add("limit " + op.limit());
        }
        Outcome expected = op.expected();
        parts.add("expecting " + expected.statuses() + (expected.error() == null ? "" : " " + expected.error())
                + (expected.pair() == 0 ? "" : " in double-click " + expected.pair()));
        return String.join(" ", parts);
    }

    @SuppressWarnings("unchecked")
    private static List<String> answerIds(Map<String, Object> question) {
        return ((List<Map<String, Object>>) question.get("answers")).stream()
                .map(answer -> (String) answer.get("id"))
                .toList();
    }

    private static Map<String, Object> read(ApiResponse response) {
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return body(response);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> body(ApiResponse response) {
        return (Map<String, Object>) response.json("$");
    }

    @SuppressWarnings("unchecked")
    private static List<ApiResponse> pages(Object walk) {
        return (List<ApiResponse>) walk;
    }

    private static String content(String prefix) {
        return prefix + " " + UUID.randomUUID();
    }
}
