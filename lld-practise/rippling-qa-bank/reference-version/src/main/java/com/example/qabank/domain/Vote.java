package com.example.qabank.domain;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

/** Mirrors the future votes(question_id, user_id, created_at) table; (questionId, voterId) is unique. */
public record Vote(UUID questionId, UUID voterId, Instant createdAt) {
    public Vote {
        Objects.requireNonNull(questionId, "questionId");
        Objects.requireNonNull(voterId, "voterId");
        Objects.requireNonNull(createdAt, "createdAt");
    }
}
