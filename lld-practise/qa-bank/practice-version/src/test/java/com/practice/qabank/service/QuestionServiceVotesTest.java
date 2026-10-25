package com.practice.qabank.service;

import static com.practice.qabank.domain.Vote.DOWN;
import static com.practice.qabank.domain.Vote.UP;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Queue;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.UnaryOperator;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.IdempotencyKey;
import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Operation;
import com.practice.qabank.domain.Question;
import com.practice.qabank.domain.Vote;
import com.practice.qabank.domain.VoteResult;
import com.practice.qabank.domain.Votes;
import com.practice.qabank.exception.AlreadyVotedException;
import com.practice.qabank.exception.AnswerNotFoundException;
import com.practice.qabank.exception.CannotVoteOwnException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.repository.IdempotencyRepositoryImpl;
import com.practice.qabank.repository.QuestionRepository;
import com.practice.qabank.repository.QuestionRepositoryImpl;

// QuestionService's vote methods. Tests that take a Target run once per method: QUESTION votes on the question, ANSWER
// on user-7's answer to it. Tests that take a Vote run once per direction, and those that take both run for all four
// pairs. Counts are read back from the stored question.
class QuestionServiceVotesTest {

    private static final int THREADS = 50;
    private static final Instant CREATED_AT = Instant.parse("2026-10-24T06:12:45.123Z");
    // Votes never read the clock; only the answer adds in the mixed concurrency test do.
    private static final Clock CLOCK = Clock.fixed(CREATED_AT, ZoneOffset.UTC);

    private final QuestionRepositoryImpl questions = new QuestionRepositoryImpl();
    private final IdempotencyRepositoryImpl idempotency = new IdempotencyRepositoryImpl();
    private final QuestionService service = new QuestionService(questions, idempotency, CLOCK);

    // A question by author-1 with two answers, saved straight into the store: one by user-7 and one by author-1.
    private final Answer answer = new Answer(UUID.randomUUID(), "user-7", "Use compute().", CREATED_AT, null, null);
    private final Answer ownAnswer = new Answer(UUID.randomUUID(), "author-1", "Use merge().", CREATED_AT, null, null);
    private final Question question = questions.save(new Question(UUID.randomUUID(), "author-1", "How?",
            List.of("java"), CREATED_AT, null, List.of(answer, ownAnswer), null));

    static Stream<Arguments> targetsAndVotes() {
        return Stream.of(Target.values())
                .flatMap(target -> Stream.of(Vote.values()).map(vote -> arguments(target, vote)));
    }

    // ---- Applied ----

    // A vote changes only votes: the stored question keeps everything else, updatedAt included. The other direction
    // stays at 0.
    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void votesByOtherUsersApplyAndCount(Target target, Vote vote) {
        IdempotentResult<VoteResult> first = vote(target, "user-8", "key-1", vote);
        IdempotentResult<VoteResult> second = vote(target, "user-9", "key-1", vote);

        assertThat(first.replayed()).isFalse();
        assertThat(first.value()).isEqualTo(new VoteResult(1));
        assertThat(second.replayed()).isFalse();
        assertThat(second.value()).isEqualTo(new VoteResult(2));
        assertThat(count(target, vote)).isEqualTo(2);
        assertThat(count(target, opposite(vote))).isZero();
        assertThat(stored(question.id())).usingRecursiveComparison().ignoringFieldsOfTypes(Votes.class)
                .isEqualTo(question);
    }

    // Pins each Vote's operations: the key is recorded under the endpoint's own operation, and not the other
    // direction's.
    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void recordsTheKeyUnderItsOwnOperation(Target target, Vote vote) {
        vote(target, "user-8", "key-1", vote);

        assertThat(isRecorded("user-8", target.operation(vote), idOf(target), "key-1")).isTrue();
        assertThat(isRecorded("user-8", target.operation(opposite(vote)), idOf(target), "key-1")).isFalse();
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void questionAuthorCanVoteOnAnotherUsersAnswer(Vote vote) {
        IdempotentResult<VoteResult> result =
                service.voteAnswer(question.id(), answer.id(), "author-1", "key-1", vote);

        assertThat(result.replayed()).isFalse();
        assertThat(result.value()).isEqualTo(new VoteResult(1));
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void oneKeyOnAQuestionAndItsAnswerAppliesBoth(Vote vote) {
        IdempotentResult<VoteResult> onQuestion = service.voteQuestion(question.id(), "user-8", "key-1", vote);
        IdempotentResult<VoteResult> onAnswer =
                service.voteAnswer(question.id(), answer.id(), "user-8", "key-1", vote);

        assertThat(onQuestion.replayed()).isFalse();
        assertThat(onAnswer.replayed()).isFalse();
        assertThat(count(Target.QUESTION, vote)).isEqualTo(1);
        assertThat(count(Target.ANSWER, vote)).isEqualTo(1);
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void oneKeyOnTwoQuestionsAppliesBoth(Vote vote) {
        Question other = saveQuestion("author-2");

        IdempotentResult<VoteResult> first = service.voteQuestion(question.id(), "user-8", "key-1", vote);
        IdempotentResult<VoteResult> second = service.voteQuestion(other.id(), "user-8", "key-1", vote);

        assertThat(first.replayed()).isFalse();
        assertThat(second.replayed()).isFalse();
        assertThat(second.value()).isEqualTo(new VoteResult(1));
        assertThat(count(Target.QUESTION, vote)).isEqualTo(1);
        assertThat(countOn(other.id(), other.id(), vote)).isEqualTo(1);
    }

    // Another operation's entry under the same user, target and key is a separate entry: no replay, and no
    // ClassCastException from the stored Answer.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void keyTheUserAnsweredWithStillVotes(Vote vote) {
        idempotency.getOrCreate(new IdempotencyKey("user-7", Operation.ADD_ANSWER, question.id(), "key-1"),
                Answer.class, () -> answer);

        IdempotentResult<VoteResult> result = service.voteQuestion(question.id(), "user-7", "key-1", vote);

        assertThat(result.replayed()).isFalse();
        assertThat(result.value()).isEqualTo(new VoteResult(1));
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void questionAndAnswerCountsAreIndependent(Vote vote) {
        service.voteQuestion(question.id(), "user-8", "key-1", vote);
        service.voteAnswer(question.id(), answer.id(), "user-8", "key-2", vote);
        IdempotentResult<VoteResult> secondOnAnswer =
                service.voteAnswer(question.id(), answer.id(), "user-9", "key-1", vote);

        assertThat(secondOnAnswer.value()).isEqualTo(new VoteResult(2));
        assertThat(count(Target.QUESTION, vote)).isEqualTo(1);
        assertThat(count(Target.ANSWER, vote)).isEqualTo(2);
        assertThat(countOn(question.id(), ownAnswer.id(), vote)).isZero();
    }

    // One vote per target, so a user may upvote a question and downvote its answer.
    @Test
    void upvoteOnAQuestionAndDownvoteOnItsAnswerBothApply() {
        IdempotentResult<VoteResult> up = service.voteQuestion(question.id(), "user-8", "key-1", UP);
        IdempotentResult<VoteResult> down = service.voteAnswer(question.id(), answer.id(), "user-8", "key-2", DOWN);

        assertThat(up.value()).isEqualTo(new VoteResult(1));
        assertThat(down.value()).isEqualTo(new VoteResult(1));
        assertThat(count(Target.QUESTION, UP)).isEqualTo(1);
        assertThat(count(Target.QUESTION, DOWN)).isZero();
        assertThat(count(Target.ANSWER, UP)).isZero();
        assertThat(count(Target.ANSWER, DOWN)).isEqualTo(1);
    }

    // ---- Replayed ----

    // The replay returns the stored count, not the live one.
    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void sameKeyReplaysTheStoredResult(Target target, Vote vote) {
        IdempotentResult<VoteResult> first = vote(target, "user-8", "key-1", vote);
        vote(target, "user-9", "key-1", vote);

        IdempotentResult<VoteResult> retry = vote(target, "user-8", "key-1", vote);

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(first.value());
        assertThat(retry.value()).isEqualTo(new VoteResult(1));
        assertThat(count(target, vote)).isEqualTo(2);
    }

    // The key holds no question id, so the voter's retry under a wrong questionId is still the replay, not a 404.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void answerVoteRetriedUnderAnotherQuestionIdReplays(Vote vote) {
        VoteResult first = service.voteAnswer(question.id(), answer.id(), "user-8", "key-1", vote).value();

        IdempotentResult<VoteResult> retry =
                service.voteAnswer(UUID.randomUUID(), answer.id(), "user-8", "key-1", vote);

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(first);
        assertThat(count(Target.ANSWER, vote)).isEqualTo(1);
    }

    // ---- Rejected, counts unchanged ----

    // Twice with the second key: a recorded key would make the retry a replay instead of a rejection.
    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void sameUserWithNewKeyThrowsAlreadyVotedAndRecordsNothing(Target target, Vote vote) {
        vote(target, "user-8", "key-1", vote);

        for (int attempt = 0; attempt < 2; attempt++) {
            assertThatThrownBy(() -> vote(target, "user-8", "key-2", vote))
                    .isInstanceOfSatisfying(AlreadyVotedException.class, e -> {
                        assertThat(e.held()).isEqualTo(vote);
                        assertThat(e.targetId()).isEqualTo(idOf(target));
                    })
                    .hasMessage("You already " + verb(vote) + "d " + target.noun() + " " + idOf(target));
        }
        assertThat(count(target, vote)).isEqualTo(1);
    }

    // Switching sides is rejected with the vote held, not the one tried.
    @ParameterizedTest(name = "{0} {1} first")
    @MethodSource("targetsAndVotes")
    void oppositeVoteThrowsAlreadyVotedHoldingTheFirstAndRecordsNothing(Target target, Vote first) {
        vote(target, "user-8", "key-1", first);

        for (int attempt = 0; attempt < 2; attempt++) {
            assertThatThrownBy(() -> vote(target, "user-8", "key-2", opposite(first)))
                    .isInstanceOfSatisfying(AlreadyVotedException.class, e -> {
                        assertThat(e.held()).isEqualTo(first);
                        assertThat(e.targetId()).isEqualTo(idOf(target));
                    })
                    .hasMessage("You already " + verb(first) + "d " + target.noun() + " " + idOf(target));
        }
        assertThat(count(target, first)).isEqualTo(1);
        assertThat(count(target, opposite(first))).isZero();
        assertThat(isRecorded("user-8", target.operation(opposite(first)), idOf(target), "key-2")).isFalse();
    }

    // An upvote and a downvote are separate operations, so the first vote's key doesn't replay its 201 for the other
    // direction: that supplier runs and gets the 409.
    @ParameterizedTest(name = "{0} {1} first")
    @MethodSource("targetsAndVotes")
    void firstVotesKeyReusedForTheOtherDirectionThrowsAlreadyVotedNotAReplay(Target target, Vote first) {
        vote(target, "user-8", "key-1", first);

        assertThatThrownBy(() -> vote(target, "user-8", "key-1", opposite(first)))
                .isInstanceOfSatisfying(AlreadyVotedException.class, e -> assertThat(e.held()).isEqualTo(first));
        assertThat(count(target, first)).isEqualTo(1);
        assertThat(count(target, opposite(first))).isZero();
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void authorCannotVoteOnOwnTargetAndRecordsNothing(Target target, Vote vote) {
        for (int attempt = 0; attempt < 2; attempt++) {
            assertThatThrownBy(() -> vote(target, authorOf(target), "key-1", vote))
                    .isInstanceOfSatisfying(CannotVoteOwnException.class, e -> {
                        assertThat(e.vote()).isEqualTo(vote);
                        assertThat(e.targetId()).isEqualTo(idOf(target));
                    })
                    .hasMessage("You can't " + verb(vote) + " your own " + target.noun() + " " + idOf(target));
        }
        assertThat(count(target, UP)).isZero();
        assertThat(count(target, DOWN)).isZero();
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void questionAuthorCannotVoteOnTheirOwnAnswer(Vote vote) {
        assertThatThrownBy(() -> service.voteAnswer(question.id(), ownAnswer.id(), "author-1", "key-1", vote))
                .isInstanceOfSatisfying(CannotVoteOwnException.class, e -> {
                    assertThat(e.vote()).isEqualTo(vote);
                    assertThat(e.targetId()).isEqualTo(ownAnswer.id());
                })
                .hasMessage("You can't " + verb(vote) + " your own answer " + ownAnswer.id());

        assertThat(countOn(question.id(), ownAnswer.id(), vote)).isZero();
        assertThat(isRecorded("author-1", Target.ANSWER.operation(vote), ownAnswer.id(), "key-1")).isFalse();
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void unknownQuestionThrowsQuestionNotFoundAndRecordsNothing(Target target, Vote vote) {
        UUID questionId = UUID.randomUUID();

        assertThatThrownBy(() -> target.vote(service, questionId, answer.id(), "user-8", "key-1", vote))
                .isInstanceOfSatisfying(QuestionNotFoundException.class, e -> assertThat(e.id()).isEqualTo(questionId))
                .hasMessage("Question " + questionId + " not found");

        assertThat(stored(question.id())).isSameAs(question);
        UUID keyTarget = target == Target.QUESTION ? questionId : answer.id();
        assertThat(isRecorded("user-8", target.operation(vote), keyTarget, "key-1")).isFalse();
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void unknownAnswerThrowsAnswerNotFoundAndRecordsNothing(Vote vote) {
        UUID answerId = UUID.randomUUID();

        assertAnswerNotFound(question.id(), answerId, vote);

        assertThat(stored(question.id())).isSameAs(question);
        assertThat(isRecorded("user-8", Target.ANSWER.operation(vote), answerId, "key-1")).isFalse();
    }

    // The key is the same under both question ids, so a recorded 404 would replay instead of applying.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void anotherQuestionsAnswerThrowsAnswerNotFoundAndTheKeyThenApplies(Vote vote) {
        Answer elsewhere = new Answer(UUID.randomUUID(), "user-7", "Elsewhere", CREATED_AT, null, null);
        Question other = questions.save(new Question(UUID.randomUUID(), "author-2", "Why?", List.of("java"),
                CREATED_AT, null, List.of(elsewhere), null));

        assertAnswerNotFound(question.id(), elsewhere.id(), vote);
        assertThat(countOn(other.id(), elsewhere.id(), vote)).isZero();

        IdempotentResult<VoteResult> result =
                service.voteAnswer(other.id(), elsewhere.id(), "user-8", "key-1", vote);
        assertThat(result.replayed()).isFalse();
        assertThat(result.value()).isEqualTo(new VoteResult(1));
    }

    private void assertAnswerNotFound(UUID questionId, UUID answerId, Vote vote) {
        assertThatThrownBy(() -> service.voteAnswer(questionId, answerId, "user-8", "key-1", vote))
                .isInstanceOfSatisfying(AnswerNotFoundException.class, e -> {
                    assertThat(e.questionId()).isEqualTo(questionId);
                    assertThat(e.answerId()).isEqualTo(answerId);
                })
                .hasMessage("Answer " + answerId + " not found on question " + questionId);
    }

    // ---- Failure ----

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void failedUpdatePropagatesAndRetryWithTheSameKeyApplies(Target target, Vote vote) {
        QuestionService failingOnce =
                new QuestionService(new FailingOnceQuestionRepository(questions), idempotency, CLOCK);

        assertThatThrownBy(() -> target.vote(failingOnce, question.id(), answer.id(), "user-8", "key-1", vote))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("store unavailable");
        assertThat(stored(question.id())).isSameAs(question);

        IdempotentResult<VoteResult> retry =
                target.vote(failingOnce, question.id(), answer.id(), "user-8", "key-1", vote);
        assertThat(retry.replayed()).isFalse();
        assertThat(retry.value()).isEqualTo(new VoteResult(1));
    }

    // ---- Concurrency ----

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void concurrentVotesByDifferentUsersAreAllCounted(Target target, Vote vote) throws Exception {
        List<Callable<IdempotentResult<VoteResult>>> calls = new ArrayList<>();
        // Not "user-": user-7 wrote the answer.
        for (int i = 0; i < THREADS; i++) {
            String user = "voter-" + i;
            calls.add(() -> vote(target, user, "key-1", vote));
        }

        List<IdempotentResult<VoteResult>> results = runTogether(calls);

        assertThat(results).allSatisfy(result -> {
            assertThat(result.replayed()).isFalse();
            assertThat(result.value().count()).isBetween(1, THREADS);
        });
        assertThat(count(target, vote)).isEqualTo(THREADS);
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void concurrentVotesByOneUserWithDifferentKeysCountOnce(Target target, Vote vote) throws Exception {
        Queue<IdempotentResult<VoteResult>> applied = new ConcurrentLinkedQueue<>();
        Queue<AlreadyVotedException> conflicts = new ConcurrentLinkedQueue<>();
        List<Callable<Void>> calls = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            String key = "key-" + i;
            calls.add(() -> {
                try {
                    applied.add(vote(target, "user-8", key, vote));
                } catch (AlreadyVotedException e) {
                    conflicts.add(e);
                }
                return null;
            });
        }

        runTogether(calls);

        assertThat(applied).hasSize(1);
        assertThat(applied.element().replayed()).isFalse();
        assertThat(applied.element().value()).isEqualTo(new VoteResult(1));
        assertThat(conflicts).hasSize(THREADS - 1).allSatisfy(e -> {
            assertThat(e.targetId()).isEqualTo(idOf(target));
            assertThat(e.held()).isEqualTo(vote);
        });
        assertThat(count(target, vote)).isEqualTo(1);
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("targetsAndVotes")
    void concurrentRetriesWithOneKeyCountOnce(Target target, Vote vote) throws Exception {
        List<Callable<IdempotentResult<VoteResult>>> retries = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            retries.add(() -> vote(target, "user-8", "key-1", vote));
        }

        List<IdempotentResult<VoteResult>> results = runTogether(retries);

        VoteResult first = results.get(0).value();
        assertThat(first).isEqualTo(new VoteResult(1));
        assertThat(results).allSatisfy(result -> assertThat(result.value()).isSameAs(first));
        assertThat(results).filteredOn(result -> !result.replayed()).hasSize(1);
        assertThat(count(target, vote)).isEqualTo(1);
    }

    // Half the keys upvote and half downvote: one vote lands, and every other call holds it in its 409.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void concurrentUpAndDownvotesByOneUserKeepOne(Target target) throws Exception {
        Queue<Map.Entry<Vote, IdempotentResult<VoteResult>>> applied = new ConcurrentLinkedQueue<>();
        Queue<AlreadyVotedException> conflicts = new ConcurrentLinkedQueue<>();
        List<Callable<Void>> calls = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            String key = "key-" + i;
            Vote vote = i % 2 == 0 ? UP : DOWN;
            calls.add(() -> {
                try {
                    applied.add(Map.entry(vote, vote(target, "user-8", key, vote)));
                } catch (AlreadyVotedException e) {
                    conflicts.add(e);
                }
                return null;
            });
        }

        runTogether(calls);

        assertThat(applied).hasSize(1);
        Vote winner = applied.element().getKey();
        assertThat(applied.element().getValue().value()).isEqualTo(new VoteResult(1));
        assertThat(conflicts).hasSize(THREADS - 1).allSatisfy(e -> assertThat(e.held()).isEqualTo(winner));
        assertThat(count(target, winner)).isEqualTo(1);
        assertThat(count(target, opposite(winner))).isZero();
    }

    // Votes on the question, votes on its answer and answer adds all change the one stored question. They apply one
    // after another, each on the previous result, so none is lost.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void concurrentVotesAndAnswerAddsOnOneQuestionAllLand(Vote vote) throws Exception {
        int each = THREADS / 3;
        List<Callable<Object>> calls = new ArrayList<>();
        for (int i = 0; i < each; i++) {
            String user = "voter-" + i;
            calls.add(() -> vote(Target.QUESTION, user, "key-1", vote));
            calls.add(() -> vote(Target.ANSWER, user, "key-1", vote));
            calls.add(() -> service.addAnswer(question.id(), new Answer(null, user, "Answer", null, null, null),
                    "key-1"));
        }

        runTogether(calls);

        assertThat(count(Target.QUESTION, vote)).isEqualTo(each);
        assertThat(count(Target.ANSWER, vote)).isEqualTo(each);
        assertThat(stored(question.id()).answers()).hasSize(2 + each);
    }

    private IdempotentResult<VoteResult> vote(Target target, String voterId, String key, Vote vote) {
        return target.vote(service, question.id(), answer.id(), voterId, key, vote);
    }

    // The target's count as stored now.
    private int count(Target target, Vote vote) {
        return countOn(question.id(), idOf(target), vote);
    }

    // targetId is the question itself or one of its answers.
    private int countOn(UUID questionId, UUID targetId, Vote vote) {
        Question stored = stored(questionId);
        Votes votes = stored.id().equals(targetId) ? stored.votes() : stored.answer(targetId).orElseThrow().votes();
        return votes.count(vote);
    }

    private Question stored(UUID questionId) {
        return questions.findById(questionId).orElseThrow();
    }

    private UUID idOf(Target target) {
        return target == Target.QUESTION ? question.id() : answer.id();
    }

    private String authorOf(Target target) {
        return target == Target.QUESTION ? question.authorId() : answer.authorId();
    }

    private Question saveQuestion(String authorId) {
        return questions.save(
                new Question(UUID.randomUUID(), authorId, "How?", List.of("java"), CREATED_AT, null, null, null));
    }

    // Probes the shared store: a recorded key replays, so the probe's own supplier doesn't run.
    private boolean isRecorded(String voterId, Operation operation, UUID targetId, String key) {
        IdempotencyKey stored = new IdempotencyKey(voterId, operation, targetId, key);
        return idempotency.getOrCreate(stored, VoteResult.class, () -> new VoteResult(-1)).replayed();
    }

    private static Vote opposite(Vote vote) {
        return vote == UP ? DOWN : UP;
    }

    // As the messages spell it.
    private static String verb(Vote vote) {
        return vote == UP ? "upvote" : "downvote";
    }

    // Every task waits on the start latch, so all of them are released together and really overlap.
    private static <T> List<T> runTogether(List<Callable<T>> tasks) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(tasks.size());
        CountDownLatch ready = new CountDownLatch(tasks.size());
        CountDownLatch start = new CountDownLatch(1);
        try {
            List<Future<T>> futures = new ArrayList<>();
            for (Callable<T> task : tasks) {
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();
                    return task.call();
                }));
            }
            assertThat(ready.await(5, TimeUnit.SECONDS)).isTrue();
            start.countDown();
            List<T> results = new ArrayList<>();
            for (Future<T> future : futures) {
                results.add(future.get(5, TimeUnit.SECONDS));
            }
            return results;
        } finally {
            pool.shutdownNow();
        }
    }

    // The two service methods. answerId is used only by ANSWER.
    enum Target {
        QUESTION,
        ANSWER;

        IdempotentResult<VoteResult> vote(QuestionService service, UUID questionId, UUID answerId, String voterId,
                String key, Vote vote) {
            return switch (this) {
                case QUESTION -> service.voteQuestion(questionId, voterId, key, vote);
                case ANSWER -> service.voteAnswer(questionId, answerId, voterId, key, vote);
            };
        }

        // Spelled out, not read from Vote, so the key cases pin Vote's operations.
        Operation operation(Vote vote) {
            return switch (this) {
                case QUESTION -> vote == UP ? Operation.UPVOTE_QUESTION : Operation.DOWNVOTE_QUESTION;
                case ANSWER -> vote == UP ? Operation.UPVOTE_ANSWER : Operation.DOWNVOTE_ANSWER;
            };
        }

        String noun() {
            return name().toLowerCase(Locale.ROOT);
        }
    }

    // The first update throws, as a store outage would; later calls go to the real repository.
    private static final class FailingOnceQuestionRepository implements QuestionRepository {

        private final QuestionRepository delegate;
        private final AtomicBoolean failed = new AtomicBoolean();

        FailingOnceQuestionRepository(QuestionRepository delegate) {
            this.delegate = delegate;
        }

        @Override
        public Question save(Question question) {
            return delegate.save(question);
        }

        @Override
        public Optional<Question> findById(UUID id) {
            return delegate.findById(id);
        }

        @Override
        public List<Question> findAll() {
            return delegate.findAll();
        }

        @Override
        public Optional<Question> update(UUID id, UnaryOperator<Question> change) {
            if (failed.compareAndSet(false, true)) {
                throw new IllegalStateException("store unavailable");
            }
            return delegate.update(id, change);
        }
    }
}
