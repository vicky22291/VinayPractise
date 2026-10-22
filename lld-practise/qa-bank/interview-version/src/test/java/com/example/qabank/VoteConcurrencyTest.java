package com.example.qabank;

import com.example.qabank.exception.DuplicateVoteException;
import com.example.qabank.repository.InMemoryQuestionRepository;
import com.example.qabank.repository.InMemoryVoteRepository;
import com.example.qabank.service.QuestionService;
import com.example.qabank.service.QuestionServiceImpl;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;

class VoteConcurrencyTest {
    private static final int THREADS = 100;

    private final QuestionService service =
            new QuestionServiceImpl(new InMemoryQuestionRepository(), new InMemoryVoteRepository());

    @Test
    void hundredDifferentUsersVotingAtOnceAreAllCounted() throws Exception {
        UUID questionId = service.create(UUID.randomUUID(), "A title long enough", "body").question().id();
        assertThat(successfulVotes(questionId, UUID::randomUUID)).isEqualTo(THREADS);
        assertThat(service.get(questionId).upvotes()).isEqualTo(THREADS);
    }

    @Test
    void sameUserVotingHundredTimesAtOnceCountsOnce() throws Exception {
        UUID questionId = service.create(UUID.randomUUID(), "A title long enough", "body").question().id();
        UUID voter = UUID.randomUUID();
        assertThat(successfulVotes(questionId, () -> voter)).isEqualTo(1);
        assertThat(service.get(questionId).upvotes()).isEqualTo(1);
    }

    private int successfulVotes(UUID questionId, Supplier<UUID> voters) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(THREADS);
        CountDownLatch startGate = new CountDownLatch(1);
        List<Future<Boolean>> results = new ArrayList<>();
        try {
            for (int i = 0; i < THREADS; i++) {
                UUID voter = voters.get();
                results.add(pool.submit(() -> {
                    startGate.await();
                    try {
                        service.upvote(questionId, voter);
                        return true;
                    } catch (DuplicateVoteException e) {
                        return false; // the correct outcome for every losing duplicate
                    }
                }));
            }
            startGate.countDown(); // release every thread at once to maximise contention
            int successes = 0;
            for (Future<Boolean> result : results) {
                successes += result.get() ? 1 : 0;
            }
            return successes;
        } finally {
            pool.shutdownNow();
        }
    }
}
