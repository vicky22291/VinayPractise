package com.example.qabank.concurrency;

import com.example.qabank.domain.Vote;
import com.example.qabank.repository.inmemory.InMemoryVoteRepository;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.ConcurrentModificationException;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Deterministic demonstrations of why the naive version is wrong. Randomised stress runs that show
 * lost updates and exceptions live in {@link RaceConditionDemo}, because they cannot be asserted
 * reliably in a unit test.
 */
class NaiveVoteStoreRaceTest {
    private final UUID question = UUID.randomUUID();
    private final UUID sameUser = UUID.randomUUID();

    @Test
    void checkThenActLetsTheSameUserVoteTwice() throws Exception {
        // The barrier forces both requests to finish contains() before either calls add().
        CyclicBarrier bothChecked = new CyclicBarrier(2);
        AtomicBoolean armed = new AtomicBoolean(false);
        NaiveVoteStore store = new NaiveVoteStore(() -> {
            if (armed.get()) {
                await(bothChecked);
            }
        });
        store.add(question, UUID.randomUUID()); // create the list up front to isolate the check-then-act race
        armed.set(true);

        ExecutorService pool = Executors.newFixedThreadPool(2);
        try {
            Future<Boolean> first = pool.submit(() -> store.add(question, sameUser));
            Future<Boolean> second = pool.submit(() -> store.add(question, sameUser));

            // Both requests were told "vote accepted": a double vote.
            assertThat(first.get(5, TimeUnit.SECONDS)).isTrue();
            assertThat(second.get(5, TimeUnit.SECONDS)).isTrue();
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    void concurrentSetAddHasNoGapBetweenCheckAndAct() throws Exception {
        // Same two racing requests against the real repository. Set.add/putIfAbsent is the check,
        // so there is no window to widen: exactly one request wins.
        InMemoryVoteRepository repository = new InMemoryVoteRepository();
        CyclicBarrier start = new CyclicBarrier(2);
        ExecutorService pool = Executors.newFixedThreadPool(2);
        try {
            Future<Boolean> first = pool.submit(() -> { await(start); return repository.addIfAbsent(vote()); });
            Future<Boolean> second = pool.submit(() -> { await(start); return repository.addIfAbsent(vote()); });

            assertThat(first.get(5, TimeUnit.SECONDS) ^ second.get(5, TimeUnit.SECONDS)).isTrue();
            assertThat(repository.countByQuestionId(question)).isEqualTo(1);
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    void hashMapIteratorIsFailFast() {
        Map<UUID, Integer> map = new HashMap<>(Map.of(UUID.randomUUID(), 1, UUID.randomUUID(), 2));

        assertThatThrownBy(() -> map.keySet().forEach(k -> map.put(UUID.randomUUID(), 0)))
                .isInstanceOf(ConcurrentModificationException.class);
    }

    @Test
    void concurrentHashMapIteratorIsWeaklyConsistent() {
        Map<UUID, Integer> map = new ConcurrentHashMap<>(Map.of(UUID.randomUUID(), 1, UUID.randomUUID(), 2));

        assertThatCode(() -> map.keySet().forEach(k -> map.put(UUID.randomUUID(), 0))).doesNotThrowAnyException();
    }

    private Vote vote() {
        return new Vote(question, sameUser, Instant.now());
    }

    private static void await(CyclicBarrier barrier) {
        try {
            barrier.await(5, TimeUnit.SECONDS);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
