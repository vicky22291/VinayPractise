package com.example.qabank.repository.inmemory;

import com.example.qabank.domain.Vote;
import com.example.qabank.repository.VoteRepository;
import org.springframework.stereotype.Repository;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Repository
public class InMemoryVoteRepository implements VoteRepository {
    // questionId -> (voterId -> vote). Equivalent to a UNIQUE(question_id, user_id) constraint:
    // computeIfAbsent creates each inner map exactly once, and putIfAbsent on a ConcurrentHashMap
    // is an atomic check-and-insert, so two racing votes by one user cannot both succeed.
    private final ConcurrentMap<UUID, ConcurrentMap<UUID, Vote>> votesByQuestion = new ConcurrentHashMap<>();

    @Override
    public boolean addIfAbsent(Vote vote) {
        return votesByQuestion
                .computeIfAbsent(vote.questionId(), id -> new ConcurrentHashMap<>())
                .putIfAbsent(vote.voterId(), vote) == null;
    }

    @Override
    public int countByQuestionId(UUID questionId) {
        // Derived from the stored votes rather than a separate counter, so it can never drift.
        Map<UUID, Vote> votes = votesByQuestion.get(questionId);
        return votes == null ? 0 : votes.size();
    }
}
