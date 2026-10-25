package com.practice.qabank.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;
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

class IdempotencyRepositoryImplTest {

    private static final int THREADS = 50;
    private static final UUID TARGET = UUID.fromString("3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11");
    private static final IdempotencyKey KEY = new IdempotencyKey("user-1", Operation.UPDATE_QUESTION, TARGET, "key-1");

    private final IdempotencyRepositoryImpl repository = new IdempotencyRepositoryImpl();
    private final AtomicInteger supplierCalls = new AtomicInteger();

    @Test
    void firstCallRunsTheSupplier() {
        Question question = question();

        IdempotentResult<Question> result = repository.getOrCreate(KEY, Question.class, counting(() -> question));

        assertThat(result.value()).isSameAs(question);
        assertThat(result.replayed()).isFalse();
        assertThat(supplierCalls).hasValue(1);
    }

    @Test
    void repeatReturnsStoredValueWithoutRunningTheSupplier() {
        Question original = question();
        repository.getOrCreate(KEY, Question.class, () -> original);

        IdempotentResult<Question> result = repository.getOrCreate(KEY, Question.class, counting(this::question));

        assertThat(result.value()).isSameAs(original);
        assertThat(result.replayed()).isTrue();
        assertThat(supplierCalls).hasValue(0);
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("keysDifferingInOneField")
    void keysDifferingInOneFieldAreIndependent(String name, IdempotencyKey first, IdempotencyKey second) {
        IdempotentResult<Question> firstResult = repository.getOrCreate(first, Question.class, this::question);

        IdempotentResult<Question> secondResult = repository.getOrCreate(second, Question.class, this::question);

        assertThat(secondResult.replayed()).isFalse();
        assertThat(secondResult.value()).isNotSameAs(firstResult.value());
    }

    static Stream<Arguments> keysDifferingInOneField() {
        UUID otherTarget = UUID.randomUUID();
        return Stream.of(
                arguments("userId", KEY, new IdempotencyKey("user-2", Operation.UPDATE_QUESTION, TARGET, "key-1")),
                arguments("operation", KEY, new IdempotencyKey("user-1", Operation.ADD_ANSWER, TARGET, "key-1")),
                arguments("targetId", KEY,
                        new IdempotencyKey("user-1", Operation.UPDATE_QUESTION, otherTarget, "key-1")),
                arguments("targetId null against a UUID",
                        new IdempotencyKey("user-1", Operation.UPDATE_QUESTION, null, "key-1"), KEY),
                arguments("key", KEY, new IdempotencyKey("user-1", Operation.UPDATE_QUESTION, TARGET, "key-2")));
    }

    @Test
    void nullTargetIdReplaysLikeAnyOtherKey() {
        IdempotencyKey createKey = new IdempotencyKey("user-1", Operation.CREATE_QUESTION, null, "key-1");
        Question original = question();
        repository.getOrCreate(createKey, Question.class, () -> original);

        IdempotentResult<Question> result = repository.getOrCreate(
                new IdempotencyKey("user-1", Operation.CREATE_QUESTION, null, "key-1"), Question.class, this::question);

        assertThat(result.replayed()).isTrue();
        assertThat(result.value()).isSameAs(original);
    }

    @Test
    void throwingSupplierRecordsNothing() {
        Question question = question();

        assertThatThrownBy(() -> repository.getOrCreate(KEY, Question.class, () -> {
            throw new IllegalStateException("save failed");
        })).isInstanceOf(IllegalStateException.class).hasMessage("save failed");

        IdempotentResult<Question> retry = repository.getOrCreate(KEY, Question.class, counting(() -> question));
        assertThat(retry.value()).isSameAs(question);
        assertThat(retry.replayed()).isFalse();
        assertThat(supplierCalls).hasValue(1);
    }

    @Test
    void readingAStoredValueAsAnotherTypeThrows() {
        repository.getOrCreate(KEY, Question.class, this::question);

        assertThatThrownBy(() -> repository.getOrCreate(KEY, Answer.class, () -> answer()))
                .isInstanceOf(ClassCastException.class);
    }

    @Test
    void storesAnswersInTheSameStore() {
        IdempotencyKey answerKey = new IdempotencyKey("user-1", Operation.ADD_ANSWER, TARGET, "key-1");
        Answer original = answer();
        repository.getOrCreate(answerKey, Answer.class, () -> original);

        IdempotentResult<Answer> result = repository.getOrCreate(answerKey, Answer.class, counting(this::answer));

        assertThat(result.value()).isSameAs(original);
        assertThat(result.replayed()).isTrue();
        assertThat(supplierCalls).hasValue(0);
    }

    @Test
    void concurrentCallsOnOneKeyRunTheSupplierOnce() throws Exception {
        // A slow supplier widens the race window, so a non-atomic check-then-create would run it many times.
        Supplier<Question> slowCreate = counting(() -> {
            sleep(20);
            return question();
        });

        ExecutorService pool = Executors.newFixedThreadPool(THREADS);
        CountDownLatch ready = new CountDownLatch(THREADS);
        CountDownLatch start = new CountDownLatch(1);
        List<IdempotentResult<Question>> results = new ArrayList<>();
        try {
            List<Future<IdempotentResult<Question>>> futures = new ArrayList<>();
            for (int i = 0; i < THREADS; i++) {
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();
                    return repository.getOrCreate(KEY, Question.class, slowCreate);
                }));
            }
            assertThat(ready.await(5, TimeUnit.SECONDS)).isTrue();
            start.countDown();
            for (Future<IdempotentResult<Question>> future : futures) {
                results.add(future.get(5, TimeUnit.SECONDS));
            }
        } finally {
            pool.shutdownNow();
        }

        assertThat(supplierCalls).hasValue(1);
        Question first = results.get(0).value();
        assertThat(results).hasSize(THREADS).allSatisfy(result -> assertThat(result.value()).isSameAs(first));
        assertThat(results).filteredOn(result -> !result.replayed()).hasSize(1);
    }

    private <T> Supplier<T> counting(Supplier<T> supplier) {
        return () -> {
            supplierCalls.incrementAndGet();
            return supplier.get();
        };
    }

    private Question question() {
        return new Question(UUID.randomUUID(), "user-1", "content", List.of(), Instant.now(), null, null, null);
    }

    private Answer answer() {
        return new Answer(UUID.randomUUID(), "user-1", "content", Instant.now(), null, null);
    }

    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        }
    }
}
