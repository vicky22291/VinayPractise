package com.practice.qabank.model;

import java.time.Instant;
import java.util.UUID;

// No questionId: the URL and Location already carry it, and this is also each entry of QuestionResponse.answers.
// upvotes and downvotes, like the question's, are read from the votes when the response is built.
public record AnswerResponse(
        UUID id, String authorId, String content, Instant createdAt, Instant updatedAt, int upvotes, int downvotes) {
}
