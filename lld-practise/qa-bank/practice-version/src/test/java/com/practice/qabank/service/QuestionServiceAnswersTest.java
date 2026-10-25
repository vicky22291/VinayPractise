package com.practice.qabank.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
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
import java.util.function.Function;
import java.util.function.UnaryOperator;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.IdempotencyKey;
import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Operation;
import com.practice.qabank.domain.Question;
import com.practice.qabank.exception.AnswerAlreadyExistsException;
import com.practice.qabank.exception.AnswerNotFoundException;
import com.practice.qabank.exception.NotAnswerOwnerException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.repository.IdempotencyRepositoryImpl;
import com.practice.qabank.repository.QuestionRepository;
import com.practice.qabank.repository.QuestionRepositoryImpl;

// QuestionService's answer methods. Its question methods are tested in QuestionServiceTest.
class QuestionServiceAnswersTest {

    private static final int THREADS = 50;
    private static final Instant CREATED_AT = Instant.parse("2026-10-24T06:12:45.123Z");
    private static final Instant EDITED_AT = Instant.parse("2026-10-24T06:15:00Z");
    private static final Instant NOW = Instant.parse("2026-10-24T06:20:02.481Z");
    private static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);

    private final QuestionRepositoryImpl questions = new QuestionRepositoryImpl();
    private final IdempotencyRepositoryImpl idempotency = new IdempotencyRepositoryImpl();
    private final QuestionService service = new QuestionService(questions, idempotency, CLOCK);

    @Test
    void newKeyAppendsAnswerLastAndLeavesTheQuestionAsItWas() {
        Answer earlier = new Answer(UUID.randomUUID(), "user-0", "Earlier", CREATED_AT, null, null);
        Question question = questions.save(new Question(UUID.randomUUID(), "author-1", "How?", List.of("java"),
                CREATED_AT, EDITED_AT, List.of(earlier), null));

        IdempotentResult<Answer> result = service.addAnswer(question.id(), draft("user-7", "Use compute()."), "key-1");

        Answer answer = result.value();
        assertThat(result.replayed()).isFalse();
        assertThat(answer.id()).isNotNull().isNotEqualTo(earlier.id());
        assertThat(answer.authorId()).isEqualTo("user-7");
        assertThat(answer.content()).isEqualTo("Use compute().");
        assertThat(answer.createdAt()).isEqualTo(NOW);
        assertThat(answer.updatedAt()).isNull();
        Question stored = stored(question.id());
        assertThat(stored.answers()).containsExactly(earlier, answer);
        assertThat(stored.answers().get(1)).isSameAs(answer);
        assertThat(stored.updatedAt()).isEqualTo(EDITED_AT);
        assertThat(stored).usingRecursiveComparison().ignoringFields("answers").isEqualTo(question);
    }

    @Test
    void sameKeyReplaysOriginalAndAppendsNothing() {
        Question question = saveQuestion("author-1");
        Answer original = service.addAnswer(question.id(), draft("user-7", "First"), "key-1").value();
        Question afterFirst = stored(question.id());

        IdempotentResult<Answer> retry = service.addAnswer(question.id(), draft("user-7", "Something else"), "key-1");

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(original);
        assertThat(retry.value().content()).isEqualTo("First");
        assertThat(stored(question.id())).isSameAs(afterFirst);
        assertThat(afterFirst.answers()).containsExactly(original);
    }

    @Test
    void sameUserAndKeyOnTwoQuestionsAddsTwoAnswers() {
        Question first = saveQuestion("author-1");
        Question second = saveQuestion("author-2");

        IdempotentResult<Answer> onFirst = service.addAnswer(first.id(), draft("user-7", "Answer"), "key-1");
        IdempotentResult<Answer> onSecond = service.addAnswer(second.id(), draft("user-7", "Answer"), "key-1");

        assertThat(onFirst.replayed()).isFalse();
        assertThat(onSecond.replayed()).isFalse();
        assertThat(onSecond.value().id()).isNotEqualTo(onFirst.value().id());
        assertThat(stored(first.id()).answers()).containsExactly(onFirst.value());
        assertThat(stored(second.id()).answers()).containsExactly(onSecond.value());
    }

    @Test
    void keyTheUserCreatedTheQuestionWithStillAdds() {
        Question question = saveQuestion("user-7");
        idempotency.getOrCreate(new IdempotencyKey("user-7", Operation.CREATE_QUESTION, null, "key-1"),
                Question.class, () -> question);

        IdempotentResult<Answer> result = service.addAnswer(question.id(), draft("user-7", "Self answer"), "key-1");

        assertThat(result.replayed()).isFalse();
        assertThat(stored(question.id()).answers()).containsExactly(result.value());
    }

    @Test
    void sameKeyFromTwoUsersAddsTwoAnswers() {
        Question question = saveQuestion("author-1");

        IdempotentResult<Answer> first = service.addAnswer(question.id(), draft("user-7", "Answer"), "key-1");
        IdempotentResult<Answer> second = service.addAnswer(question.id(), draft("user-8", "Answer"), "key-1");

        assertThat(first.replayed()).isFalse();
        assertThat(second.replayed()).isFalse();
        assertThat(second.value().id()).isNotEqualTo(first.value().id());
        assertThat(stored(question.id()).answers()).containsExactly(first.value(), second.value());
    }

    @Test
    void sameUserWithNewKeyThrowsAnswerAlreadyExistsAndRecordsNothing() {
        Question question = saveQuestion("author-1");
        Answer first = service.addAnswer(question.id(), draft("user-7", "First"), "key-1").value();
        Question afterFirst = stored(question.id());

        assertThatThrownBy(() -> service.addAnswer(question.id(), draft("user-7", "Second"), "key-2"))
                .isInstanceOfSatisfying(AnswerAlreadyExistsException.class, e -> {
                    assertThat(e.questionId()).isEqualTo(question.id());
                    assertThat(e.answerId()).isEqualTo(first.id());
                })
                .hasMessage("Question " + question.id() + " already has answer " + first.id() + " by this user");

        assertThat(stored(question.id())).isSameAs(afterFirst);
        assertThat(isRecorded("user-7", question.id(), "key-2")).isFalse();
    }

    @Test
    void unknownQuestionThrowsQuestionNotFoundAndRecordsNothing() {
        UUID id = UUID.randomUUID();

        assertThatThrownBy(() -> service.addAnswer(id, draft("user-7", "Answer"), "key-1"))
                .isInstanceOfSatisfying(QuestionNotFoundException.class, e -> assertThat(e.id()).isEqualTo(id))
                .hasMessage("Question " + id + " not found");

        assertThat(isRecorded("user-7", id, "key-1")).isFalse();
    }

    @Test
    void failedUpdatePropagatesAndRetryWithTheSameKeyAdds() {
        Question question = saveQuestion("author-1");
        QuestionService failingOnce =
                new QuestionService(new FailingOnceQuestionRepository(questions), idempotency, CLOCK);

        assertThatThrownBy(() -> failingOnce.addAnswer(question.id(), draft("user-7", "Answer"), "key-1"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("store unavailable");
        assertThat(stored(question.id())).isSameAs(question);

        IdempotentResult<Answer> retry = failingOnce.addAnswer(question.id(), draft("user-7", "Answer"), "key-1");
        assertThat(retry.replayed()).isFalse();
        assertThat(stored(question.id()).answers()).containsExactly(retry.value());
    }

    @Test
    void questionAuthorCanAnswer() {
        Question question = saveQuestion("author-1");

        IdempotentResult<Answer> result = service.addAnswer(question.id(), draft("author-1", "Self answer"), "key-1");

        assertThat(result.value().authorId()).isEqualTo("author-1");
        assertThat(stored(question.id()).answers()).containsExactly(result.value());
    }

    @Test
    void concurrentAddsByDifferentUsersAreAllStored() throws Exception {
        Question question = saveQuestion("author-1");
        List<Callable<IdempotentResult<Answer>>> adds = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            String user = "user-" + i;
            adds.add(() -> service.addAnswer(question.id(), draft(user, "Answer by " + user), "key-1"));
        }

        List<IdempotentResult<Answer>> results = runTogether(adds);

        assertThat(results).allSatisfy(result -> assertThat(result.replayed()).isFalse());
        List<Answer> added = results.stream().map(IdempotentResult::value).toList();
        assertThat(stored(question.id()).answers()).hasSize(THREADS).containsExactlyInAnyOrderElementsOf(added);
    }

    @Test
    void concurrentAddsByOneUserWithDifferentKeysCreateOne() throws Exception {
        Question question = saveQuestion("author-1");
        Queue<IdempotentResult<Answer>> created = new ConcurrentLinkedQueue<>();
        Queue<AnswerAlreadyExistsException> conflicts = new ConcurrentLinkedQueue<>();
        List<Callable<Void>> adds = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            String key = "key-" + i;
            adds.add(() -> {
                try {
                    created.add(service.addAnswer(question.id(), draft("user-7", "Answer " + key), key));
                } catch (AnswerAlreadyExistsException e) {
                    conflicts.add(e);
                }
                return null;
            });
        }

        runTogether(adds);

        assertThat(created).hasSize(1);
        IdempotentResult<Answer> winner = created.element();
        assertThat(winner.replayed()).isFalse();
        assertThat(conflicts).hasSize(THREADS - 1)
                .allSatisfy(e -> assertThat(e.answerId()).isEqualTo(winner.value().id()));
        assertThat(stored(question.id()).answers()).containsExactly(winner.value());
    }

    @Test
    void concurrentRetriesWithOneKeyCreateOne() throws Exception {
        Question question = saveQuestion("author-1");
        List<Callable<IdempotentResult<Answer>>> adds = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            adds.add(() -> service.addAnswer(question.id(), draft("user-7", "Answer"), "key-1"));
        }

        List<IdempotentResult<Answer>> results = runTogether(adds);

        Answer first = results.get(0).value();
        assertThat(results).allSatisfy(result -> assertThat(result.value()).isSameAs(first));
        assertThat(results).filteredOn(result -> !result.replayed()).hasSize(1);
        assertThat(stored(question.id()).answers()).containsExactly(first);
    }

    @Test
    void getAfterAddReturnsTheStoredAnswer() {
        Question question = saveQuestion("author-1");
        service.addAnswer(question.id(), draft("user-8", "Earlier"), "key-1");
        Answer added = service.addAnswer(question.id(), draft("user-7", "Use compute()."), "key-1").value();

        Answer found = service.getAnswer(question.id(), added.id());

        assertThat(found).isSameAs(added).isSameAs(stored(question.id()).answers().get(1));
    }

    @Test
    void getWithUnknownQuestionThrowsQuestionNotFound() {
        UUID questionId = UUID.randomUUID();

        assertThatThrownBy(() -> service.getAnswer(questionId, UUID.randomUUID()))
                .isInstanceOfSatisfying(QuestionNotFoundException.class, e -> assertThat(e.id()).isEqualTo(questionId))
                .hasMessage("Question " + questionId + " not found");
    }

    @Test
    void getWithUnknownAnswerIdThrowsAnswerNotFound() {
        Question question = saveQuestion("author-1");
        service.addAnswer(question.id(), draft("user-7", "Answer"), "key-1");
        UUID answerId = UUID.randomUUID();

        assertAnswerNotFound(question.id(), answerId);
    }

    // An answer is found only under its own question.
    @Test
    void getWithAnotherQuestionsAnswerIdThrowsAnswerNotFound() {
        Question question = saveQuestion("author-1");
        Question other = saveQuestion("author-2");
        service.addAnswer(question.id(), draft("user-7", "Answer"), "key-1");
        Answer elsewhere = service.addAnswer(other.id(), draft("user-7", "Answer"), "key-2").value();

        assertAnswerNotFound(question.id(), elsewhere.id());
    }

    private void assertAnswerNotFound(UUID questionId, UUID answerId) {
        assertThatThrownBy(() -> service.getAnswer(questionId, answerId))
                .isInstanceOfSatisfying(AnswerNotFoundException.class, e -> {
                    assertThat(e.questionId()).isEqualTo(questionId);
                    assertThat(e.answerId()).isEqualTo(answerId);
                })
                .hasMessage("Answer " + answerId + " not found on question " + questionId);
    }

    // Promised in UpdateQuestion.md: question edits and answer adds on one question both survive, because each change
    // builds on the question computeIfPresent hands it.
    @Test
    void questionEditsRacingAnswerAddsKeepBoth() throws Exception {
        Question question = saveQuestion("author-1");
        int each = THREADS / 2;
        List<String> edits = IntStream.range(0, each).mapToObj(i -> "edit-" + i).toList();
        List<Callable<IdempotentResult<?>>> tasks = new ArrayList<>();
        for (String edit : edits) {
            Question editDraft = new Question(null, "author-1", edit, List.of("java"), null, null, null, null);
            tasks.add(() -> service.update(question.id(), editDraft, "key-" + edit));
        }
        for (int i = 0; i < each; i++) {
            String user = "user-" + i;
            tasks.add(() -> service.addAnswer(question.id(), draft(user, "Answer by " + user), "key-1"));
        }

        List<IdempotentResult<?>> results = runTogether(tasks);

        List<Answer> added =
                results.subList(each, results.size()).stream().map(result -> (Answer) result.value()).toList();
        Question stored = stored(question.id());
        assertThat(stored.content()).isIn(edits);
        assertThat(stored.answers()).hasSize(each).containsExactlyInAnyOrderElementsOf(added);
    }

    // ---- Update answer ----

    @ParameterizedTest(name = "{0}")
    @MethodSource("answerEdits")
    void updateByAnswerAuthorAppliesAndStores(String name, String content, Instant expectedUpdatedAt) {
        Answer other = existingAnswer("user-8", "Use merge().");
        Answer original = existingAnswer("user-7", "Use compute().");
        Question question = saveAnswered("author-1", other, original);

        IdempotentResult<Answer> result =
                service.updateAnswer(question.id(), original.id(), draft("user-7", content), "key-1");

        Answer answer = result.value();
        assertThat(result.replayed()).isFalse();
        assertThat(answer.id()).isEqualTo(original.id());
        assertThat(answer.authorId()).isEqualTo("user-7");
        assertThat(answer.content()).isEqualTo(content);
        assertThat(answer.createdAt()).isEqualTo(CREATED_AT);
        assertThat(answer.updatedAt()).isEqualTo(expectedUpdatedAt);
        Question stored = stored(question.id());
        assertThat(stored.answers()).containsExactly(other, answer);
        assertThat(stored.answers().get(0)).isSameAs(other);
        assertThat(stored.answers().get(1)).isSameAs(answer);
        assertThat(stored.updatedAt()).isEqualTo(EDITED_AT);
        assertThat(stored).usingRecursiveComparison().ignoringFields("answers").isEqualTo(question);
    }

    // The saved answer has content "Use compute()." and updatedAt null. A no-op leaves updatedAt null.
    static Stream<Arguments> answerEdits() {
        return Stream.of(
                arguments("change", "Use compute() or merge().", NOW),
                arguments("no-op", "Use compute().", null));
    }

    @Test
    void sameKeyReplaysFirstEditAndIgnoresNewContent() {
        Answer original = existingAnswer("user-7", "Use compute().");
        Question question = saveAnswered("author-1", original);
        Answer first = service.updateAnswer(question.id(), original.id(), draft("user-7", "Edit A"), "key-1").value();
        Question afterFirst = stored(question.id());

        IdempotentResult<Answer> retry =
                service.updateAnswer(question.id(), original.id(), draft("user-7", "Edit B"), "key-1");

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(first);
        assertThat(retry.value().content()).isEqualTo("Edit A");
        assertThat(stored(question.id())).isSameAs(afterFirst);
    }

    @Test
    void sameKeyAfterNewerEditReplaysWithoutReverting() {
        Answer original = existingAnswer("user-7", "Use compute().");
        Question question = saveAnswered("author-1", original);
        Answer first = service.updateAnswer(question.id(), original.id(), draft("user-7", "Edit A"), "key-1").value();
        Answer newer = service.updateAnswer(question.id(), original.id(), draft("user-7", "Edit B"), "key-2").value();

        IdempotentResult<Answer> retry =
                service.updateAnswer(question.id(), original.id(), draft("user-7", "Edit A"), "key-1");

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(first);
        assertThat(stored(question.id()).answers()).containsExactly(newer);
        assertThat(stored(question.id()).answers().get(0)).isSameAs(newer);
    }

    // The key holds no question id, so the author's retry under a wrong questionId is still the replay, not a 404.
    @Test
    void sameKeyUnderAnotherQuestionIdStillReplays() {
        Answer original = existingAnswer("user-7", "Use compute().");
        Question question = saveAnswered("author-1", original);
        Answer first = service.updateAnswer(question.id(), original.id(), draft("user-7", "Edited"), "key-1").value();

        IdempotentResult<Answer> retry =
                service.updateAnswer(UUID.randomUUID(), original.id(), draft("user-7", "Edited"), "key-1");

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(first);
    }

    @Test
    void sameKeyOnAnotherAnswerApplies() {
        Answer onFirst = existingAnswer("user-7", "First");
        Answer onSecond = existingAnswer("user-7", "Second");
        Question first = saveAnswered("author-1", onFirst);
        Question second = saveAnswered("author-2", onSecond);
        service.updateAnswer(first.id(), onFirst.id(), draft("user-7", "Edited"), "key-1");

        IdempotentResult<Answer> result =
                service.updateAnswer(second.id(), onSecond.id(), draft("user-7", "Edited"), "key-1");

        assertThat(result.replayed()).isFalse();
        assertThat(result.value().id()).isEqualTo(onSecond.id());
        assertThat(result.value().content()).isEqualTo("Edited");
        assertThat(stored(second.id()).answers()).containsExactly(result.value());
    }

    @Test
    void keyTheAnswerWasAddedWithStillApplies() {
        Question question = saveQuestion("author-1");
        Answer added = service.addAnswer(question.id(), draft("user-7", "First"), "key-1").value();

        IdempotentResult<Answer> result =
                service.updateAnswer(question.id(), added.id(), draft("user-7", "Edited"), "key-1");

        assertThat(result.replayed()).isFalse();
        assertThat(result.value()).isNotSameAs(added);
        assertThat(result.value().content()).isEqualTo("Edited");
        assertThat(stored(question.id()).answers()).containsExactly(result.value());
    }

    @Test
    void updateUnknownQuestionThrowsAndDoesNotRecordKey() {
        UUID questionId = UUID.randomUUID();
        Answer original = existingAnswer("user-7", "Use compute().");

        assertThatThrownBy(() -> service.updateAnswer(questionId, original.id(), draft("user-7", "Edited"), "key-1"))
                .isInstanceOfSatisfying(QuestionNotFoundException.class, e -> assertThat(e.id()).isEqualTo(questionId))
                .hasMessage("Question " + questionId + " not found");
        assertThat(questions.findById(questionId)).isEmpty();

        // Not recorded: once a question with that answer exists under the id, the retry with the same key applies.
        questions.save(new Question(questionId, "author-1", "How?", List.of("java"), CREATED_AT, null,
                List.of(original), null));
        IdempotentResult<Answer> retry =
                service.updateAnswer(questionId, original.id(), draft("user-7", "Edited"), "key-1");
        assertThat(retry.replayed()).isFalse();
        assertThat(retry.value().content()).isEqualTo("Edited");
        assertThat(stored(questionId).answers()).containsExactly(retry.value());
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("missingAnswers")
    void updateUnknownAnswerThrowsAndDoesNotRecordKey(String name, Function<Answer, UUID> pickAnswerId) {
        Question question = saveAnswered("author-1", existingAnswer("user-7", "Use compute()."));
        Answer elsewhere = existingAnswer("user-7", "Elsewhere");
        Question other = saveAnswered("author-2", elsewhere);
        UUID answerId = pickAnswerId.apply(elsewhere);

        assertThatThrownBy(() -> service.updateAnswer(question.id(), answerId, draft("user-7", "Edited"), "key-1"))
                .isInstanceOfSatisfying(AnswerNotFoundException.class, e -> {
                    assertThat(e.questionId()).isEqualTo(question.id());
                    assertThat(e.answerId()).isEqualTo(answerId);
                })
                .hasMessage("Answer " + answerId + " not found on question " + question.id());

        assertThat(stored(question.id())).isSameAs(question);
        assertThat(stored(other.id())).isSameAs(other);
        assertThat(isEditRecorded("user-7", answerId, "key-1")).isFalse();
    }

    // The function gets an answer by the same user on another question.
    static Stream<Arguments> missingAnswers() {
        return Stream.of(
                arguments("unknown answer id", answerIdOf(elsewhere -> UUID.randomUUID())),
                arguments("another question's answer", answerIdOf(Answer::id)));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("nonAnswerAuthors")
    void updateByAnotherUserThrowsAndDoesNotRecordKey(String name, String callerId) {
        Answer original = existingAnswer("user-7", "Use compute().");
        Question question = saveAnswered("author-1", original);

        // Twice with the same key: a recorded key would make the second call a replay instead of a rejection.
        for (int attempt = 0; attempt < 2; attempt++) {
            assertThatThrownBy(
                    () -> service.updateAnswer(question.id(), original.id(), draft(callerId, "Edited"), "key-1"))
                    .isInstanceOfSatisfying(NotAnswerOwnerException.class, e -> {
                        assertThat(e.questionId()).isEqualTo(question.id());
                        assertThat(e.answerId()).isEqualTo(original.id());
                    })
                    .hasMessage("Only the author can update answer " + original.id());
        }
        assertThat(stored(question.id())).isSameAs(question);
        assertThat(isEditRecorded(callerId, original.id(), "key-1")).isFalse();
    }

    static Stream<Arguments> nonAnswerAuthors() {
        return Stream.of(
                arguments("another user", "user-8"),
                arguments("the question's author", "author-1"),
                arguments("the answer author's id in another case", "USER-7"));
    }

    @Test
    void addReplayAfterEditReturnsTheOriginal() {
        Question question = saveQuestion("author-1");
        Answer added = service.addAnswer(question.id(), draft("user-7", "First"), "key-1").value();
        Answer edited = service.updateAnswer(question.id(), added.id(), draft("user-7", "Edited"), "key-2").value();

        IdempotentResult<Answer> replay = service.addAnswer(question.id(), draft("user-7", "First"), "key-1");

        assertThat(replay.replayed()).isTrue();
        assertThat(replay.value()).isSameAs(added);
        assertThat(replay.value().content()).isEqualTo("First");
        assertThat(replay.value().updatedAt()).isNull();
        assertThat(stored(question.id()).answers()).containsExactly(edited);
    }

    @Test
    void concurrentEditsRacingAddsKeepEveryAnswer() throws Exception {
        Answer original = existingAnswer("user-7", "Use compute().");
        Question question = saveAnswered("author-1", original);
        int each = THREADS / 2;
        List<String> edits = IntStream.range(0, each).mapToObj(i -> "edit-" + i).toList();
        List<Callable<IdempotentResult<Answer>>> tasks = new ArrayList<>();
        for (String edit : edits) {
            tasks.add(() -> service.updateAnswer(question.id(), original.id(), draft("user-7", edit), "key-" + edit));
        }
        for (int i = 0; i < each; i++) {
            String user = "other-" + i;
            tasks.add(() -> service.addAnswer(question.id(), draft(user, "Answer by " + user), "key-1"));
        }

        List<IdempotentResult<Answer>> results = runTogether(tasks);

        List<Answer> added = results.subList(each, results.size()).stream().map(IdempotentResult::value).toList();
        List<Answer> stored = stored(question.id()).answers();
        assertThat(stored).hasSize(each + 1);
        assertThat(stored.get(0).id()).isEqualTo(original.id());
        assertThat(stored.get(0).content()).isIn(edits);
        assertThat(stored.subList(1, stored.size())).containsExactlyInAnyOrderElementsOf(added);
    }

    // The race above, made deterministic: another user's answer lands between the edit's lookup and its atomic change.
    // Building from q keeps it; building from the looked-up question would drop it.
    @Test
    void answerAddedBetweenLookupAndEditIsKept() {
        Answer original = existingAnswer("user-7", "Use compute().");
        Answer late = existingAnswer("user-8", "Use merge().");
        QuestionRepositoryImpl interleaving = new QuestionRepositoryImpl() {
            private boolean interleaved;

            @Override
            public Optional<Question> update(UUID id, UnaryOperator<Question> change) {
                if (!interleaved) {
                    interleaved = true;
                    super.update(id, q -> q.withAnswer(late));
                }
                return super.update(id, change);
            }
        };
        Question question = interleaving.save(new Question(UUID.randomUUID(), "author-1", "How?", List.of("java"),
                CREATED_AT, null, List.of(original), null));
        QuestionService editing = new QuestionService(interleaving, idempotency, CLOCK);

        Answer edited = editing.updateAnswer(question.id(), original.id(), draft("user-7", "Edited"), "key-1").value();

        assertThat(edited.content()).isEqualTo("Edited");
        assertThat(interleaving.findById(question.id()).orElseThrow().answers()).containsExactly(edited, late);
    }

    @Test
    void concurrentRetriesOfOneEditApplyOnce() throws Exception {
        Answer original = existingAnswer("user-7", "Use compute().");
        Question question = saveAnswered("author-1", original);
        List<Callable<IdempotentResult<Answer>>> retries = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            retries.add(() -> service.updateAnswer(question.id(), original.id(), draft("user-7", "Edited"), "key-1"));
        }

        List<IdempotentResult<Answer>> results = runTogether(retries);

        Answer stored = stored(question.id()).answer(original.id()).orElseThrow();
        assertThat(stored.content()).isEqualTo("Edited");
        assertThat(results).allSatisfy(result -> assertThat(result.value()).isSameAs(stored));
        assertThat(results).filteredOn(result -> !result.replayed()).hasSize(1);
    }

    // A question by questionAuthor, last edited at EDITED_AT, holding these answers, saved straight into the store.
    private Question saveAnswered(String questionAuthor, Answer... answers) {
        return questions.save(new Question(UUID.randomUUID(), questionAuthor, "How?", List.of("java"), CREATED_AT,
                EDITED_AT, List.of(answers), null));
    }

    // Probes the shared store for an edit key, as isRecorded does for adds.
    private boolean isEditRecorded(String userId, UUID answerId, String key) {
        IdempotencyKey stored = new IdempotencyKey(userId, Operation.UPDATE_ANSWER, answerId, key);
        Answer probe = new Answer(answerId, userId, "probe", NOW, null, null);
        return idempotency.getOrCreate(stored, Answer.class, () -> probe).replayed();
    }

    private static Answer existingAnswer(String authorId, String content) {
        return new Answer(UUID.randomUUID(), authorId, content, CREATED_AT, null, null);
    }

    // Gives a lambda its target type inside arguments(...).
    private static Function<Answer, UUID> answerIdOf(Function<Answer, UUID> pick) {
        return pick;
    }

    private Question saveQuestion(String authorId) {
        return questions.save(
                new Question(UUID.randomUUID(), authorId, "How?", List.of("java"), CREATED_AT, null, null, null));
    }

    private Question stored(UUID questionId) {
        return questions.findById(questionId).orElseThrow();
    }

    // Probes the shared store: a recorded key replays, so the probe's own supplier doesn't run.
    private boolean isRecorded(String userId, UUID questionId, String key) {
        IdempotencyKey stored = new IdempotencyKey(userId, Operation.ADD_ANSWER, questionId, key);
        Answer probe = new Answer(UUID.randomUUID(), userId, "probe", NOW, null, null);
        return idempotency.getOrCreate(stored, Answer.class, () -> probe).replayed();
    }

    private static Answer draft(String authorId, String content) {
        return new Answer(null, authorId, content, null, null, null);
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
