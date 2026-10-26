package com.vinaypractice2.qabank.domain;

import java.time.Instant;
import java.util.UUID;

public record QuestionResponse(
        UUID id,
        String title,
        String description,
        String authorId,
        Instant createdAt,
        Instant updatedAt
) {}
