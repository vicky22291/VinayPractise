package com.example.qabank.service;

import com.example.qabank.exception.DuplicateVoteException;
import com.example.qabank.repository.inmemory.InMemoryQuestionRepository;
import com.example.qabank.repository.inmemory.InMemoryVoteRepository;
import com.example.qabank.support.SequentialIdGenerator;
import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.IntFunction;

import static org.assertj.core.api.Assertions.assertThat;

class UpvoteConcurrencyTest {
    private static final int THREADS = 100;
    private static final UUID AUTHOR = UUID.randomUUID();

    private final QuestionService service = new DefaultQuestionService(
            new InMemoryQuestionRepository(), new InMemoryVoteRepository(), Clock.systemUTC(), new SequentialIdGenerator());

    @Test
    void sameUserVotingFromHundredThreadsCountsExactlyOnce() throws Exception {
        UUID questionId = service.create(AUTHOR, "A question under contention", "body").question().id();
        UUID voter = UUID.randomUUID();

        Outcomes outcomes = runAtOnce(i -> () -> service.upvote(questionId, voter));

        assertThat(outcomes.successes).isEqualTo(1);
        assertThat(outcomes.duplicates).isEqualTo(THREADS - 1);
        assertThat(service.get(questionId).upvotes()).isEqualTo(1);
    }

    @Test
    void hundredDifferentUsersVotingAtOnceAreAllCounted() throws Exception {
        UUID questionId = service.create(AUTHOR, "A question under contention", "body").question().id();

        Outcomes outcomes = runAtOnce(i -> () -> service.upvote(questionId, UUID.randomUUID()));

        assertThat(outcomes.successes).isEqualTo(THREADS);
        assertThat(service.get(questionId).upvotes()).isEqualTo(THREADS);
    }

    /** Parks every task behind one start gate, then releases them together to maximise overlap. */
    private Outcomes runAtOnce(IntFunction<Callable<Integer>> taskFactory) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(THREADS);
        CountDownLatch ready = new CountDownLatch(THREADS);
        CountDownLatch startGate = new CountDownLatch(1);
        List<Future<Boolean>> results = new ArrayList<>();
        try {
            for (int i = 0; i < THREADS; i++) {
                Callable<Integer> task = taskFactory.apply(i);
                results.add(pool.submit(() -> {
                    ready.countDown();
                    startGate.await();
                    try {
                        task.call();
                        return true;
                    } catch (DuplicateVoteException e) {
                        return false;
                    }
                }));
            }
            assertThat(ready.await(5, TimeUnit.SECONDS)).isTrue();
            startGate.countDown();

            Outcomes outcomes = new Outcomes();
            for (Future<Boolean> result : results) {
                if (result.get(5, TimeUnit.SECONDS)) {
                    outcomes.successes++;
                } else {
                    outcomes.duplicates++;
                }
            }
            return outcomes;
        } finally {
            pool.shutdownNow();
        }
    }

    private static final class Outcomes {
        int successes;
        int duplicates;
    }
}
