package com.vinaypractice3.qabank.services.question.model;

import jakarta.annotation.Nonnull;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentSkipListSet;

public record Question(
        UUID id,
        String authorId,
        String title,
        String description,
        Instant createdAt,
        Instant updatedAt,
        Set<String> upVotes
) {
    public Question withIdAndCreatedAt (@Nonnull final UUID id, @Nonnull final Instant createdAt) {
        return new Question(id, authorId, title, description, createdAt, createdAt, new ConcurrentSkipListSet<>());
    }
}
