package com.example.qabank.concurrency;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Deliberately broken: HashMap + ArrayList with a check-then-act duplicate check.
 * Lives in test code only, to demonstrate what the real repository avoids.
 */
final class NaiveVoteStore {
    private final Map<UUID, List<UUID>> votersByQuestion = new HashMap<>();
    private final Runnable betweenCheckAndAct;

    NaiveVoteStore() {
        this(() -> { });
    }

    /** @param betweenCheckAndAct test hook that widens the race window between contains() and add(). */
    NaiveVoteStore(Runnable betweenCheckAndAct) {
        this.betweenCheckAndAct = betweenCheckAndAct;
    }

    boolean add(UUID questionId, UUID userId) {
        List<UUID> voters = votersByQuestion.computeIfAbsent(questionId, id -> new ArrayList<>());
        if (voters.contains(userId)) {   // check
            return false;
        }
        betweenCheckAndAct.run();
        voters.add(userId);              // act: another thread may have acted since our check
        return true;
    }

    int count(UUID questionId) {
        return votersByQuestion.getOrDefault(questionId, List.of()).size();
    }

    List<UUID> voters(UUID questionId) {
        return votersByQuestion.getOrDefault(questionId, List.of());
    }
}
