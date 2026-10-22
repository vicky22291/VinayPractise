package com.example.qabank.repository;

import org.springframework.stereotype.Repository;

import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class InMemoryVoteRepository implements VoteRepository {
    // questionId -> voter ids. computeIfAbsent creates each set exactly once, and the concurrent
    // set's add() is an atomic check-and-insert, so two racing votes by one user cannot both win.
    private final Map<UUID, Set<UUID>> votersByQuestion = new ConcurrentHashMap<>();

    @Override
    public boolean add(UUID questionId, UUID userId) {
        return votersByQuestion.computeIfAbsent(questionId, id -> ConcurrentHashMap.newKeySet()).add(userId);
    }

    @Override
    public int count(UUID questionId) {
        // Derived from the voter set, so the count can never drift from the votes.
        return votersByQuestion.getOrDefault(questionId, Set.of()).size();
    }
}
