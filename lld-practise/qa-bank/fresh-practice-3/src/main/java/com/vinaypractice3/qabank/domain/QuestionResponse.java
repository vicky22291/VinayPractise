package com.vinaypractice3.qabank.domain;

import java.time.Instant;
import java.util.UUID;

public record QuestionResponse(
        UUID id,
        String authorId,
        String title,
        String description,
        Instant createdAt,
        Instant updatedAt,
        int upVotes
) {}
