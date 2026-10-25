package com.practice.qabank.model;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

// upvotes and downvotes aren't stored in Question: QuestionMapper reads them from the votes when the response is
// built.
public record QuestionResponse(
        UUID id,
        String authorId,
        String content,
        List<String> tags,
        Instant createdAt,
        Instant updatedAt,
        int upvotes,
        int downvotes,
        List<AnswerResponse> answers) {
}
