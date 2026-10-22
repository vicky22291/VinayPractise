package com.example.qabank.web;

import com.example.qabank.domain.Question;
import com.example.qabank.domain.QuestionView;

import java.time.Instant;
import java.util.UUID;

public record QuestionResponse(UUID id, UUID authorId, String title, String body, Instant createdAt, int upvotes) {
    static QuestionResponse from(QuestionView view) {
        Question q = view.question();
        return new QuestionResponse(q.id(), q.authorId(), q.title(), q.body(), q.createdAt(), view.upvotes());
    }
}
