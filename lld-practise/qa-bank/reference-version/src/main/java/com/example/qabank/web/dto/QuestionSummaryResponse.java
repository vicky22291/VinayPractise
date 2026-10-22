package com.example.qabank.web.dto;

import com.example.qabank.domain.Question;
import com.example.qabank.domain.QuestionView;

import java.time.Instant;
import java.util.UUID;

/** List item without the body: a 100-item page of 30k-char bodies would be ~3 MB. */
public record QuestionSummaryResponse(UUID id, UUID authorId, String title, Instant createdAt, int upvotes) {
    public static QuestionSummaryResponse from(QuestionView view) {
        Question q = view.question();
        return new QuestionSummaryResponse(q.id(), q.authorId(), q.title(), q.createdAt(), view.upvotes());
    }
}
