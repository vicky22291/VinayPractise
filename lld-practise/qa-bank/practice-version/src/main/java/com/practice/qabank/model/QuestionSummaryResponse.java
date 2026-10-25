package com.practice.qabank.model;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

// A list item: QuestionResponse's fields with answerCount in place of answers, so a page stays bounded. Answers stay on
// GET question. upvotes and downvotes are read from the votes when the item is built, as in QuestionResponse.
public record QuestionSummaryResponse(
        UUID id,
        String authorId,
        String content,
        List<String> tags,
        Instant createdAt,
        Instant updatedAt,
        int upvotes,
        int downvotes,
        int answerCount) {
}
