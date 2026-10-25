package com.practice.qabank.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentHashMap;
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
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.qabank.domain.Question;

class QuestionRepositoryImplTest {

    private static final int THREADS = 50;

    private final QuestionRepositoryImpl repository = new QuestionRepositoryImpl();

    @Test
    void saveThenFindByIdReturnsIt() {
        Question question = question("first");

        Question saved = repository.save(question);

        assertThat(saved).isSameAs(question);
        assertThat(repository.findById(question.id())).containsSame(question);
    }

    @Test
    void findByUnknownIdIsEmpty() {
        assertThat(repository.findById(UUID.randomUUID())).isEmpty();
    }

    @Test
    void savingAnExistingIdThrowsAndKeepsTheOriginal() {
        Question original = question("original");
        Question sameId = new Question(original.id(), "author-2", "other", List.of(), Instant.now(), null, null, null);
        repository.save(original);

        assertThatThrownBy(() -> repository.save(sameId)).isInstanceOf(IllegalStateException.class);
        assertThat(repository.findById(original.id())).containsSame(original);
    }

    @Test
    void concurrentSavesAreAllStored() throws Exception {
        List<Question> questions = questions();

        List<Callable<Question>> saves = new ArrayList<>();
        for (Question question : questions) {
            saves.add(() -> repository.save(question));
        }

        runTogether(saves);

        assertThat(questions)
                .allSatisfy(question -> assertThat(repository.findById(question.id())).containsSame(question));
    }

    @Test
    void concurrentSaveThenFindFindsEveryOne() throws Exception {
        List<Question> questions = questions();

        List<Callable<Optional<Question>>> saveThenFind = new ArrayList<>();
        for (Question question : questions) {
            saveThenFind.add(() -> {
                repository.save(question);
                return repository.findById(question.id());
            });
        }

        List<Optional<Question>> found = runTogether(saveThenFind);

        for (int i = 0; i < THREADS; i++) {
            assertThat(found.get(i)).containsSame(questions.get(i));
        }
    }

    @Test
    void findAllIsEmptyWhenNothingIsStored() {
        assertThat(repository.findAll()).isEmpty();
    }

    @Test
    void findAllHoldsEachQuestionOnceAndTheNewInstanceAfterUpdate() {
        Question first = repository.save(question("first"));
        Question original = repository.save(question("original"));
        Question changed = withContent(original, "changed");
        repository.update(original.id(), current -> changed);

        assertThat(repository.findAll()).containsExactlyInAnyOrder(first, changed).doesNotContain(original);
    }

    @Test
    void findAllIsAnUnmodifiableSnapshot() {
        Question first = repository.save(question("first"));

        List<Question> snapshot = repository.findAll();
        repository.save(question("second"));

        assertThat(snapshot).containsExactly(first);
        assertThatThrownBy(() -> snapshot.add(question("third"))).isInstanceOf(UnsupportedOperationException.class);
    }

    // The reader notes which saves have returned before each findAll; the snapshot must hold all of them, and no id
    // twice. Its last pass starts after every save has returned, so it sees all of them.
    @Test
    void findAllDuringConcurrentSavesHoldsEveryFinishedSaveOnce() throws Exception {
        List<Question> questions = questions();
        Set<UUID> saved = ConcurrentHashMap.newKeySet();
        List<Callable<Void>> tasks = new ArrayList<>();
        for (Question question : questions) {
            tasks.add(() -> {
                repository.save(question);
                saved.add(question.id());
                return null;
            });
        }
        tasks.add(() -> {
            boolean last;
            do {
                last = saved.size() == THREADS;
                Set<UUID> before = Set.copyOf(saved);
                List<UUID> ids = repository.findAll().stream().map(Question::id).toList();
                assertThat(ids).doesNotHaveDuplicates().containsAll(before);
            } while (!last);
            return null;
        });

        runTogether(tasks);

        assertThat(repository.findAll()).containsExactlyInAnyOrderElementsOf(questions);
    }

    @Test
    void updateStoresAndReturnsTheChangedQuestion() {
        Question original = repository.save(question("original"));
        Question changed = withContent(original, "changed");

        Optional<Question> result = repository.update(original.id(), current -> changed);

        assertThat(result).containsSame(changed);
        assertThat(repository.findById(original.id())).containsSame(changed);
    }

    @Test
    void updatePassesTheStoredQuestionToTheChange() {
        Question original = repository.save(question("original"));
        List<Question> seen = new ArrayList<>();

        repository.update(original.id(), current -> {
            seen.add(current);
            return current;
        });

        assertThat(seen).containsExactly(original);
    }

    @Test
    void updateOfUnknownIdIsEmptyAndDoesNotRunTheChange() {
        UUID id = UUID.randomUUID();
        AtomicBoolean called = new AtomicBoolean();

        Optional<Question> result = repository.update(id, current -> {
            called.set(true);
            return current;
        });

        assertThat(result).isEmpty();
        assertThat(called).isFalse();
        assertThat(repository.findById(id)).isEmpty();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("badChanges")
    void updateRejectsABadResultAndKeepsTheEntry(String name, UnaryOperator<Question> change) {
        Question original = repository.save(question("original"));

        assertThatThrownBy(() -> repository.update(original.id(), change)).isInstanceOf(IllegalStateException.class);
        assertThat(repository.findById(original.id())).containsSame(original);
    }

    static Stream<Arguments> badChanges() {
        UnaryOperator<Question> returnsNull = current -> null;
        UnaryOperator<Question> changesId = current -> new Question(UUID.randomUUID(), current.authorId(),
                current.content(), current.tags(), current.createdAt(), current.updatedAt(), current.answers(), null);
        return Stream.of(
                arguments("returns null", returnsNull),
                arguments("returns another id", changesId));
    }

    @Test
    void updateThatThrowsKeepsTheEntry() {
        Question original = repository.save(question("original"));

        assertThatThrownBy(() -> repository.update(original.id(), current -> {
            throw new IllegalArgumentException("rule broken");
        })).isInstanceOf(IllegalArgumentException.class).hasMessage("rule broken");
        assertThat(repository.findById(original.id())).containsSame(original);
    }

    @Test
    void concurrentUpdatesAreNotLost() throws Exception {
        Question original = repository.save(question(""));
        List<Callable<Optional<Question>>> appends = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            appends.add(() -> repository.update(
                    original.id(), current -> withContent(current, current.content() + "x")));
        }

        runTogether(appends);

        assertThat(repository.findById(original.id())).hasValueSatisfying(
                question -> assertThat(question.content()).hasSize(THREADS));
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

    private static List<Question> questions() {
        List<Question> questions = new ArrayList<>();
        for (int i = 0; i < THREADS; i++) {
            questions.add(question("question " + i));
        }
        return questions;
    }

    private static Question question(String content) {
        return new Question(UUID.randomUUID(), "author-1", content, List.of("java"), Instant.now(), null, null, null);
    }

    private static Question withContent(Question question, String content) {
        return new Question(question.id(), question.authorId(), content, question.tags(), question.createdAt(),
                question.updatedAt(), question.answers(), null);
    }
}
