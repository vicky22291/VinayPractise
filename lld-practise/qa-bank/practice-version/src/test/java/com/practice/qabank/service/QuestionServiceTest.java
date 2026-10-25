package com.practice.qabank.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.UnaryOperator;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.qabank.domain.IdempotencyKey;
import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Operation;
import com.practice.qabank.domain.Question;
import com.practice.qabank.domain.QuestionPage;
import com.practice.qabank.exception.NotQuestionOwnerException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.repository.IdempotencyRepositoryImpl;
import com.practice.qabank.repository.QuestionRepository;
import com.practice.qabank.repository.QuestionRepositoryImpl;

class QuestionServiceTest {

    private static final Instant NOW = Instant.parse("2026-10-24T06:12:45.123Z");
    private static final Clock CLOCK = Clock.fixed(NOW, ZoneOffset.UTC);
    // Questions saved directly for the update tests were created before the fixed clock's NOW.
    private static final Instant CREATED_AT = Instant.parse("2026-10-24T06:00:00Z");
    private static final int THREADS = 50;

    private final QuestionRepositoryImpl questions = spy(new QuestionRepositoryImpl());
    private final IdempotencyRepositoryImpl idempotency = new IdempotencyRepositoryImpl();
    private final QuestionService service = new QuestionService(questions, idempotency, CLOCK);
    // The last id savedAt used.
    private long lastId;

    @Test
    void newKeyCreatesAndStoresQuestion() {
        IdempotentResult<Question> result = service.create(draft("author-1", "How?", List.of("Java")), "key-1");

        Question question = result.value();
        assertThat(result.replayed()).isFalse();
        assertThat(question.id()).isNotNull();
        assertThat(question.createdAt()).isEqualTo(NOW);
        assertThat(question.updatedAt()).isNull();
        assertThat(question.answers()).isEmpty();
        assertThat(question.authorId()).isEqualTo("author-1");
        assertThat(question.content()).isEqualTo("How?");
        assertThat(question.tags()).containsExactly("java");
        assertThat(questions.findById(question.id())).containsSame(question);
    }

    @Test
    void eachNewKeyGetsItsOwnRandomId() {
        Question first = service.create(draft("author-1", "How?", List.of()), "key-1").value();
        Question second = service.create(draft("author-1", "How?", List.of()), "key-2").value();

        assertThat(second.id()).isNotEqualTo(first.id());
    }

    @Test
    void sameKeyReplaysOriginalAndStoresNothingNew() {
        Question original = service.create(draft("author-1", "How?", List.of("java")), "key-1").value();

        IdempotentResult<Question> retry =
                service.create(draft("author-1", "Something else?", List.of("kotlin")), "key-1");

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(original);
        assertThat(retry.value().content()).isEqualTo("How?");
        assertThat(retry.value().tags()).containsExactly("java");
        verify(questions, times(1)).save(any());
    }

    @Test
    void sameKeyFromTwoUsersCreatesTwoQuestions() {
        IdempotentResult<Question> first = service.create(draft("author-1", "How?", List.of()), "key-1");
        IdempotentResult<Question> second = service.create(draft("author-2", "How?", List.of()), "key-1");

        assertThat(first.replayed()).isFalse();
        assertThat(second.replayed()).isFalse();
        assertThat(second.value().id()).isNotEqualTo(first.value().id());
        assertThat(questions.findById(first.value().id())).isPresent();
        assertThat(questions.findById(second.value().id())).isPresent();
    }

    @Test
    void keyAlreadyUsedForAnotherOperationStillCreates() {
        Question updated = new Question(UUID.randomUUID(), "author-1", "Other", List.of(), NOW, NOW, null, null);
        idempotency.getOrCreate(new IdempotencyKey("author-1", Operation.UPDATE_QUESTION, updated.id(), "key-1"),
                Question.class, () -> updated);

        IdempotentResult<Question> result = service.create(draft("author-1", "How?", List.of()), "key-1");

        assertThat(result.replayed()).isFalse();
        assertThat(result.value()).isNotSameAs(updated);
        assertThat(questions.findById(result.value().id())).containsSame(result.value());
    }

    @Test
    void failedSavePropagatesAndDoesNotRecordKey() {
        QuestionService failing = new QuestionService(new FailingQuestionRepository(), idempotency, CLOCK);

        assertThatThrownBy(() -> failing.create(draft("author-1", "How?", List.of()), "key-1"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("store unavailable");

        // Same idempotency store, working question store: the retry must create, not replay.
        IdempotentResult<Question> retry = service.create(draft("author-1", "How?", List.of()), "key-1");
        assertThat(retry.replayed()).isFalse();
        assertThat(questions.findById(retry.value().id())).containsSame(retry.value());
    }

    @Test
    void getReturnsTheStoredQuestion() {
        Question created = service.create(draft("author-1", "How?", List.of("java")), "key-1").value();

        assertThat(service.get(created.id())).isSameAs(created);
    }

    @Test
    void getUnknownIdThrowsQuestionNotFound() {
        UUID id = UUID.randomUUID();

        assertThatThrownBy(() -> service.get(id))
                .isInstanceOfSatisfying(QuestionNotFoundException.class, e -> assertThat(e.id()).isEqualTo(id))
                .hasMessage("Question " + id + " not found");
    }

    // The oldest has the largest id of the first three, so createdAt decides before id does.
    @Test
    void listsNewestFirstWithTiesByIdDescending() {
        Question tiedLow = savedAt(1);
        Question tiedHigh = savedAt(1);
        Question oldest = savedAt(0);
        Question newest = savedAt(2);

        QuestionPage page = service.list(null, null, 10);

        assertThat(page.items()).containsExactly(newest, tiedHigh, tiedLow, oldest);
        assertThat(page.nextCursor()).isNull();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("pageSizes")
    void walkingThePagesYieldsEveryQuestionOnceInOrder(String name, int count, int limit) {
        List<Question> newestFirst = savedNewestFirst(count);

        List<QuestionPage> pages = walk(null, limit);

        assertThat(pages.stream().flatMap(page -> page.items().stream()).toList()).isEqualTo(newestFirst);
        assertThat(pages).hasSize(Math.max(1, (count + limit - 1) / limit));
        for (QuestionPage page : pages.subList(0, pages.size() - 1)) {
            assertThat(page.items()).hasSize(limit);
            assertThat(page.nextCursor()).isEqualTo(page.items().get(limit - 1).id());
        }
        assertThat(pages.get(pages.size() - 1).nextCursor()).isNull();
    }

    static Stream<Arguments> pageSizes() {
        return Stream.of(
                arguments("0 questions, limit 1", 0, 1),
                arguments("1 question, limit 1", 1, 1),
                arguments("5 questions, limit 1", 5, 1),
                arguments("5 questions, limit 2", 5, 2),
                arguments("5 questions, limit 5", 5, 5),
                arguments("5 questions, limit 6", 5, 6),
                arguments("21 questions, limit 20", 21, 20));
    }

    @Test
    void afterIsExclusive() {
        List<Question> newestFirst = savedNewestFirst(5);

        QuestionPage page = service.list(null, newestFirst.get(1).id(), 2);

        assertThat(page.items()).containsExactly(newestFirst.get(2), newestFirst.get(3));
        assertThat(page.nextCursor()).isEqualTo(newestFirst.get(3).id());
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("javaTags")
    void tagMatchesWholeTagsInAnyCase(String name, String tag) {
        Question both = savedAt(0, "java", "spring");
        savedAt(1, "kotlin");
        Question javaOnly = savedAt(2, "java");
        savedAt(3, "javascript");

        QuestionPage page = service.list(tag, null, 10);

        assertThat(page.items()).containsExactly(javaOnly, both);
        assertThat(page.nextCursor()).isNull();
    }

    static Stream<Arguments> javaTags() {
        return Stream.of(
                arguments("java", "java"),
                arguments("Java", "Java"),
                arguments("JAVA", "JAVA"));
    }

    @Test
    void unmatchedTagGivesEmptyLastPage() {
        savedAt(0, "java");

        QuestionPage page = service.list("rust", null, 10);

        assertThat(page.items()).isEmpty();
        assertThat(page.nextCursor()).isNull();
    }

    @Test
    void afterWithoutTheTagStillPlacesThePage() {
        Question older = savedAt(0, "java");
        Question cursor = savedAt(1, "kotlin");
        savedAt(2, "java");

        QuestionPage page = service.list("java", cursor.id(), 10);

        assertThat(page.items()).containsExactly(older);
        assertThat(page.nextCursor()).isNull();
    }

    @Test
    void unknownAfterThrowsBeforeReadingTheList() {
        UUID id = UUID.randomUUID();

        assertThatThrownBy(() -> service.list(null, id, 20))
                .isInstanceOfSatisfying(QuestionNotFoundException.class, e -> assertThat(e.id()).isEqualTo(id))
                .hasMessage("Question " + id + " not found");
        verify(questions, never()).findAll();
    }

    @Test
    void limitBelowOneThrows() {
        assertThatThrownBy(() -> service.list(null, null, 0)).isInstanceOf(IllegalArgumentException.class);
        verify(questions, never()).findAll();
    }

    @Test
    void editedQuestionKeepsItsPosition() {
        List<Question> newestFirst = savedNewestFirst(3);
        Question middle = newestFirst.get(1);
        Question edited =
                service.update(middle.id(), draft("author-1", "Edited?", List.of("kotlin")), "key-1").value();

        QuestionPage page = service.list(null, null, 10);

        assertThat(page.items()).containsExactly(newestFirst.get(0), edited, newestFirst.get(2));
        assertThat(page.items().get(1).content()).isEqualTo("Edited?");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("authorEdits")
    void updateByAuthorAppliesAndStores(String name, String content, List<String> tags, List<String> expectedTags,
            Instant expectedUpdatedAt) {
        Question original = saved("author-1");

        IdempotentResult<Question> result = service.update(original.id(), draft("author-1", content, tags), "key-1");

        Question question = result.value();
        assertThat(result.replayed()).isFalse();
        assertThat(question.id()).isEqualTo(original.id());
        assertThat(question.authorId()).isEqualTo("author-1");
        assertThat(question.content()).isEqualTo(content);
        assertThat(question.tags()).containsExactlyElementsOf(expectedTags);
        assertThat(question.createdAt()).isEqualTo(CREATED_AT);
        assertThat(question.updatedAt()).isEqualTo(expectedUpdatedAt);
        assertThat(questions.findById(original.id())).containsSame(question);
    }

    // The saved question has content "How?" and tags ["java"]. A no-op leaves updatedAt null.
    static Stream<Arguments> authorEdits() {
        return Stream.of(
                arguments("change", "Edited?", List.of("Kotlin"), List.of("kotlin"), NOW),
                arguments("no-op", "How?", List.of("java"), List.of("java"), null),
                arguments("no-op after tag normalization", "How?", List.of("JAVA", "java"), List.of("java"), null));
    }

    @Test
    void sameKeyReplaysFirstResultAndIgnoresNewBody() {
        Question original = saved("author-1");
        Question first =
                service.update(original.id(), draft("author-1", "Edited?", List.of("kotlin")), "key-1").value();

        IdempotentResult<Question> retry =
                service.update(original.id(), draft("author-1", "Something else?", List.of("scala")), "key-1");

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(first);
        assertThat(questions.findById(original.id())).containsSame(first);
        verify(questions, times(1)).update(any(), any());
    }

    @Test
    void sameKeyAfterNewerEditReplaysWithoutReverting() {
        Question original = saved("author-1");
        Question first = service.update(original.id(), draft("author-1", "Edit A", List.of()), "key-1").value();
        Question newer = service.update(original.id(), draft("author-1", "Edit B", List.of()), "key-2").value();

        IdempotentResult<Question> retry =
                service.update(original.id(), draft("author-1", "Edit A", List.of()), "key-1");

        assertThat(retry.replayed()).isTrue();
        assertThat(retry.value()).isSameAs(first);
        assertThat(questions.findById(original.id())).containsSame(newer);
    }

    @Test
    void sameKeyOnAnotherQuestionApplies() {
        Question firstQuestion = saved("author-1");
        Question secondQuestion = saved("author-1");
        service.update(firstQuestion.id(), draft("author-1", "Edited?", List.of()), "key-1");

        IdempotentResult<Question> result =
                service.update(secondQuestion.id(), draft("author-1", "Edited?", List.of()), "key-1");

        assertThat(result.replayed()).isFalse();
        assertThat(result.value().id()).isEqualTo(secondQuestion.id());
        assertThat(result.value().content()).isEqualTo("Edited?");
        assertThat(questions.findById(secondQuestion.id())).containsSame(result.value());
    }

    @Test
    void keyTheQuestionWasCreatedWithStillApplies() {
        Question created = service.create(draft("author-1", "How?", List.of("java")), "key-1").value();

        IdempotentResult<Question> result =
                service.update(created.id(), draft("author-1", "Edited?", List.of()), "key-1");

        assertThat(result.replayed()).isFalse();
        assertThat(result.value()).isNotSameAs(created);
        assertThat(result.value().content()).isEqualTo("Edited?");
        assertThat(questions.findById(created.id())).containsSame(result.value());
    }

    @Test
    void updateUnknownIdThrowsAndDoesNotRecordKey() {
        UUID id = UUID.randomUUID();

        assertThatThrownBy(() -> service.update(id, draft("author-1", "Edited?", List.of()), "key-1"))
                .isInstanceOfSatisfying(QuestionNotFoundException.class, e -> assertThat(e.id()).isEqualTo(id))
                .hasMessage("Question " + id + " not found");
        assertThat(questions.findById(id)).isEmpty();

        // Not recorded: once a question exists under that id, the retry with the same key applies.
        questions.save(new Question(id, "author-1", "How?", List.of("java"), CREATED_AT, null, null, null));
        IdempotentResult<Question> retry = service.update(id, draft("author-1", "Edited?", List.of()), "key-1");
        assertThat(retry.replayed()).isFalse();
        assertThat(retry.value().content()).isEqualTo("Edited?");
        assertThat(questions.findById(id)).containsSame(retry.value());
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("otherCallers")
    void updateByAnotherUserThrowsAndDoesNotRecordKey(String name, String callerId) {
        Question original = saved("author-1");

        // Twice with the same key: a recorded key would make the second call a replay instead of a rejection.
        for (int attempt = 0; attempt < 2; attempt++) {
            assertThatThrownBy(() -> service.update(original.id(), draft(callerId, "Edited?", List.of()), "key-1"))
                    .isInstanceOfSatisfying(NotQuestionOwnerException.class,
                            e -> assertThat(e.id()).isEqualTo(original.id()))
                    .hasMessage("Only the author can update question " + original.id());
        }
        assertThat(questions.findById(original.id())).containsSame(original);
        verify(questions, never()).update(any(), any());
    }

    static Stream<Arguments> otherCallers() {
        return Stream.of(
                arguments("another user", "author-2"),
                arguments("the author's id in another case", "AUTHOR-1"));
    }

    @Test
    void createReplayAfterEditReturnsTheOriginal() {
        Question created = service.create(draft("author-1", "How?", List.of("java")), "key-1").value();
        Question edited =
                service.update(created.id(), draft("author-1", "Edited?", List.of("kotlin")), "key-2").value();

        IdempotentResult<Question> replay = service.create(draft("author-1", "How?", List.of("java")), "key-1");

        assertThat(replay.replayed()).isTrue();
        assertThat(replay.value()).isSameAs(created);
        assertThat(replay.value().content()).isEqualTo("How?");
        assertThat(replay.value().tags()).containsExactly("java");
        assertThat(replay.value().updatedAt()).isNull();
        assertThat(questions.findById(created.id())).containsSame(edited);
    }

    @Test
    void concurrentRetriesOfOneEditWriteOnce() throws Exception {
        Question original = saved("author-1");
        List<Callable<IdempotentResult<Question>>> retries = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            retries.add(() -> service.update(original.id(), draft("author-1", "Edited?", List.of("kotlin")), "key-1"));
        }

        List<IdempotentResult<Question>> results = runTogether(retries);

        Question stored = questions.findById(original.id()).orElseThrow();
        assertThat(stored.content()).isEqualTo("Edited?");
        assertThat(results).allSatisfy(result -> assertThat(result.value()).isSameAs(stored));
        assertThat(results).filteredOn(result -> !result.replayed()).hasSize(1);
        verify(questions, times(1)).update(any(), any());
    }

    // Under the fixed clock every question here ties on createdAt, so the new ones land anywhere in the order, before
    // the pager's cursor too: the hardest case. Each creator returns its new id and the pager the ids it walked, so one
    // runTogether serves both.
    @Test
    void concurrentCreatesWhilePagingNeverRepeatOrMissEarlierQuestions() throws Exception {
        List<UUID> earlier = new ArrayList<>();
        for (int i = 0; i < 20; i++) {
            earlier.add(service.create(draft("author-1", "How?", List.of()), "key-" + i).value().id());
        }
        List<Callable<List<UUID>>> tasks = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            String key = "parallel-key-" + i;
            tasks.add(() -> List.of(service.create(draft("author-2", "How?", List.of()), key).value().id()));
        }
        tasks.add(() -> ids(walk(null, 3)));

        List<List<UUID>> results = runTogether(tasks);

        List<UUID> walked = results.get(THREADS);
        assertThat(walked).doesNotHaveDuplicates().containsAll(earlier);
        assertThat(walked).isSortedAccordingTo(Comparator.reverseOrder());
        List<UUID> all = new ArrayList<>(earlier);
        results.subList(0, THREADS).forEach(all::addAll);
        assertThat(all).containsAll(walked);
        assertThat(ids(walk(null, 3))).containsExactlyInAnyOrderElementsOf(all);
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

    // A stored question with content "How?" and tags ["java"], saved straight into the repository at CREATED_AT.
    private Question saved(String authorId) {
        return questions.save(
                new Question(UUID.randomUUID(), authorId, "How?", List.of("java"), CREATED_AT, null, null, null));
    }

    // A question by author-1, saved straight into the repository seconds after CREATED_AT. ids come from a counter, so
    // a later call always gets a larger id.
    private Question savedAt(int seconds, String... tags) {
        lastId++;
        return questions.save(new Question(new UUID(0, lastId), "author-1", "Question " + lastId, List.of(tags),
                CREATED_AT.plusSeconds(seconds), null, null, null));
    }

    // count questions, returned newest first. Each pair shares a createdAt and the later one has the larger id, so ties
    // fall on page boundaries too.
    private List<Question> savedNewestFirst(int count) {
        List<Question> newestFirst = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            newestFirst.add(0, savedAt(i / 2));
        }
        return newestFirst;
    }

    // Follows nextCursor as after until it's null. A walk of 1000 pages means the cursor isn't moving.
    private List<QuestionPage> walk(String tag, int limit) {
        List<QuestionPage> pages = new ArrayList<>();
        UUID after = null;
        do {
            QuestionPage page = service.list(tag, after, limit);
            pages.add(page);
            after = page.nextCursor();
            assertThat(pages).hasSizeLessThan(1000);
        } while (after != null);
        return pages;
    }

    private static List<UUID> ids(List<QuestionPage> pages) {
        return pages.stream().flatMap(page -> page.items().stream()).map(Question::id).toList();
    }

    private static Question draft(String authorId, String content, List<String> tags) {
        return new Question(null, authorId, content, tags, null, null, null, null);
    }

    private static final class FailingQuestionRepository implements QuestionRepository {

        @Override
        public Question save(Question question) {
            throw new IllegalStateException("store unavailable");
        }

        @Override
        public Optional<Question> findById(UUID id) {
            return Optional.empty();
        }

        @Override
        public List<Question> findAll() {
            return List.of();
        }

        @Override
        public Optional<Question> update(UUID id, UnaryOperator<Question> change) {
            throw new IllegalStateException("store unavailable");
        }
    }
}
