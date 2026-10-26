package com.vinaypractice1.qabank.model;

import java.util.UUID;

public record QuestionResponse(
        UUID id,
        String title,
        String content,
        String authorId
) {}
