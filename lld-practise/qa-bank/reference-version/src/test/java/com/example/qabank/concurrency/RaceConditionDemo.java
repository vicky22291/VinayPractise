package com.example.qabank.concurrency;

import com.example.qabank.domain.Vote;
import com.example.qabank.repository.inmemory.InMemoryVoteRepository;

import java.time.Instant;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Experiment, not a test: results are random, which is the point.
 * Each round, 100 threads add 1,000 distinct voters each to one question while a reader iterates.
 * Expected count is 100,000. Run from reference-version/ after ./mvnw test-compile:
 *   java -cp target/classes:target/test-classes com.example.qabank.concurrency.RaceConditionDemo
 */
public final class RaceConditionDemo {
    private static final int THREADS = 100;
    private static final int VOTES_PER_THREAD = 1_000;
    private static final int ROUNDS = 20;

    public static void main(String[] args) throws Exception {
        System.out.println("round | naive count | lost | writer exceptions | reader CMEs | safe count");
        for (int round = 1; round <= ROUNDS; round++) {
            runRound(round);
        }
    }

    private static void runRound(int round) throws Exception {
        UUID question = UUID.randomUUID();
        NaiveVoteStore naive = new NaiveVoteStore();
        InMemoryVoteRepository safe = new InMemoryVoteRepository();
        AtomicInteger writerExceptions = new AtomicInteger();
        AtomicInteger readerCmes = new AtomicInteger();
        AtomicBoolean writing = new AtomicBoolean(true);

        ExecutorService pool = Executors.newFixedThreadPool(THREADS + 1);
        CountDownLatch startGate = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(THREADS);
        for (int t = 0; t < THREADS; t++) {
            pool.submit(() -> {
                awaitQuietly(startGate);
                for (int i = 0; i < VOTES_PER_THREAD; i++) {
                    UUID voter = UUID.randomUUID();
                    try {
                        naive.add(question, voter);
                    } catch (RuntimeException e) { // typically ArrayIndexOutOfBoundsException from ArrayList.grow
                        writerExceptions.incrementAndGet();
                    }
                    safe.addIfAbsent(new Vote(question, voter, Instant.now()));
                }
                done.countDown();
            });
        }
        pool.submit(() -> { // a "list voters" request iterating while votes arrive
            awaitQuietly(startGate);
            while (writing.get()) {
                try {
                    for (UUID ignored : naive.voters(question)) {
                        Thread.onSpinWait();
                    }
                } catch (java.util.ConcurrentModificationException e) {
                    readerCmes.incrementAndGet();
                }
            }
        });
        startGate.countDown();
        done.await();
        writing.set(false);
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);

        int expected = THREADS * VOTES_PER_THREAD;
        int naiveCount = naive.count(question);
        System.out.printf("%5d | %11d | %4d | %17d | %11d | %10d%n", round, naiveCount, expected - naiveCount,
                writerExceptions.get(), readerCmes.get(), safe.countByQuestionId(question));
    }

    private static void awaitQuietly(CountDownLatch latch) {
        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
