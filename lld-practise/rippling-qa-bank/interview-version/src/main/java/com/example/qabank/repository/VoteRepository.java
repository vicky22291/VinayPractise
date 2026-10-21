package com.example.qabank.repository;

import java.util.UUID;

public interface VoteRepository {
    /** @return false if this user had already voted on the question. */
    boolean add(UUID questionId, UUID userId);

    int count(UUID questionId);
}
