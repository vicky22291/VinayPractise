package com.practice.hotel.service;

import static com.practice.hotel.domain.IdempotencyStatus.COMPLETED;
import static com.practice.hotel.domain.IdempotencyStatus.IN_PROGRESS;
import static com.practice.hotel.domain.OperationType.CREATE_HOTEL;
import static com.practice.hotel.domain.OperationType.UPDATE_HOTEL;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Named.named;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.hotel.domain.IdempotencyKey;
import com.practice.hotel.domain.IdempotencyRecord;
import com.practice.hotel.error.IdempotencyInProgressException;
import com.practice.hotel.error.IdempotencyKeyReusedException;
import com.practice.hotel.repository.IdempotencyRepository;
import com.practice.hotel.repository.IdempotencyRepositoryImpl;

class IdempotencyServiceImplTest {

    private static final Instant NOW = Instant.parse("2026-10-24T09:15:02.123Z");
    private static final RequestContext CONTEXT = new RequestContext("admin-1", NOW, "key-1", "hash-1");
    private static final IdempotencyKey KEY = new IdempotencyKey(CREATE_HOTEL, "key-1");

    private final IdempotencyRepository repository = new IdempotencyRepositoryImpl();
    private final IdempotencyService service = new IdempotencyServiceImpl(repository);
    private final AtomicInteger runs = new AtomicInteger();

    @Test
    void runsActionOnceForNewKey() {
        assertThat(service.execute(CREATE_HOTEL, CONTEXT, action("hotel-1"))).isEqualTo("hotel-1");

        assertThat(runs).hasValue(1);
        // claim hands back the stored record when the key is taken
        assertThat(repository.claim(new IdempotencyRecord(KEY, "probe", IN_PROGRESS, null, NOW)))
                .contains(new IdempotencyRecord(KEY, "hash-1", COMPLETED, "hotel-1", NOW));
    }

    @Test
    void replaysCompletedKey() {
        service.execute(CREATE_HOTEL, CONTEXT, action("hotel-1"));

        assertThat(service.execute(CREATE_HOTEL, CONTEXT, action("hotel-2"))).isEqualTo("hotel-1");
        assertThat(runs).hasValue(1);
    }

    @Test
    void rejectsDifferentHash() {
        service.execute(CREATE_HOTEL, CONTEXT, action("hotel-1"));
        RequestContext otherRequest = new RequestContext("admin-1", NOW, "key-1", "hash-2");

        assertThatThrownBy(() -> service.execute(CREATE_HOTEL, otherRequest, action("hotel-2")))
                .isInstanceOf(IdempotencyKeyReusedException.class);
    }

    @Test
    void rejectsKeyInProgress() {
        repository.claim(new IdempotencyRecord(KEY, "hash-1", IN_PROGRESS, null, NOW));

        assertThatThrownBy(() -> service.execute(CREATE_HOTEL, CONTEXT, action("hotel-1")))
                .isInstanceOf(IdempotencyInProgressException.class);
    }

    static Stream<Arguments> failures() {
        return Stream.of(
                Arguments.of(named("RuntimeException", new IllegalStateException("save failed"))),
                Arguments.of(named("Error", new StackOverflowError())));
    }

    @ParameterizedTest
    @MethodSource("failures")
    void releasesKeyWhenActionFails(Throwable failure) {
        assertThatThrownBy(() -> service.execute(CREATE_HOTEL, CONTEXT, () -> {
            if (failure instanceof Error error) {
                throw error;
            }
            throw (RuntimeException) failure;
        })).isSameAs(failure);

        assertThat(service.execute(CREATE_HOTEL, CONTEXT, action("hotel-1"))).isEqualTo("hotel-1");
        assertThat(runs).hasValue(1);
    }

    @Test
    void scopesKeyByOperation() {
        assertThat(service.execute(CREATE_HOTEL, CONTEXT, action("hotel-1"))).isEqualTo("hotel-1");
        assertThat(service.execute(UPDATE_HOTEL, CONTEXT, action("hotel-2"))).isEqualTo("hotel-2");
        assertThat(runs).hasValue(2);
    }

    @Test
    void parallelCallsRunActionOnce() throws Exception {
        int threads = 20;
        CyclicBarrier start = new CyclicBarrier(threads);
        Callable<String> call = () -> {
            start.await();
            try {
                return service.execute(CREATE_HOTEL, CONTEXT, action("hotel-1"));
            } catch (IdempotencyInProgressException e) {
                return "409";
            }
        };

        List<String> results = new ArrayList<>();
        try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
            for (Future<String> result : pool.invokeAll(Collections.nCopies(threads, call))) {
                results.add(result.get());
            }
        }

        assertThat(runs).hasValue(1);
        assertThat(results).hasSize(threads).contains("hotel-1").isSubsetOf("hotel-1", "409");
    }

    private Supplier<String> action(String resourceId) {
        return () -> {
            runs.incrementAndGet();
            return resourceId;
        };
    }
}
