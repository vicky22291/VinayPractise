package com.example.qabank.repository;

import com.example.qabank.domain.Vote;

import java.util.UUID;

public interface VoteRepository {
    /** Atomically stores the vote unless this voter already voted on the question. @return true if stored. */
    boolean addIfAbsent(Vote vote);

    int countByQuestionId(UUID questionId);
}
