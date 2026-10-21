package com.example.qabank.domain;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

/** A position in the newest-first ordering. id breaks ties between equal timestamps. */
public record PageCursor(Instant createdAt, UUID id) {
    public PageCursor {
        Objects.requireNonNull(createdAt, "createdAt");
        Objects.requireNonNull(id, "id");
    }

    public static PageCursor of(Question question) {
        return new PageCursor(question.createdAt(), question.id());
    }
}
