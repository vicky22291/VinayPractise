package com.example.qabank.domain;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

/** Immutable, so it can be shared across threads and indexes without copying or locking. */
public record Question(UUID id, UUID authorId, String title, String body, Instant createdAt) {
    public Question {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(authorId, "authorId");
        Objects.requireNonNull(title, "title");
        Objects.requireNonNull(body, "body");
        Objects.requireNonNull(createdAt, "createdAt");
    }

    public boolean isAuthoredBy(UUID userId) {
        return authorId.equals(userId);
    }
}
