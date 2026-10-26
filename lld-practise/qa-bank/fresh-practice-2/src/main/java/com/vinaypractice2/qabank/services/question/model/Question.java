package com.vinaypractice2.qabank.services.question.model;

import com.google.common.base.Preconditions;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

public record Question(
        UUID id,
        String title,
        String description,
        String authorId,
        Instant createdAt,
        Instant updatedAt
) {
    public Question withIdAndCreatedAt(final UUID id, final Instant createdAt) {
        Preconditions.checkArgument(Objects.nonNull(id), "id cannot be null");
        Preconditions.checkArgument(Objects.nonNull(createdAt), "createdAt cannot be null");
        return new Question(id, title, description, authorId, createdAt, createdAt);
    }
}
