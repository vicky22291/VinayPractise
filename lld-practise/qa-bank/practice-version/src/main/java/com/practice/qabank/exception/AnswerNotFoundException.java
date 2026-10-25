package com.practice.qabank.exception;

import java.util.UUID;

// Also thrown when the answer exists but belongs to another question: an answer is found only under its own question.
public final class AnswerNotFoundException extends NotFoundException {

    private final UUID questionId;
    private final UUID answerId;

    public AnswerNotFoundException(UUID questionId, UUID answerId) {
        super("Answer " + answerId + " not found on question " + questionId);
        this.questionId = questionId;
        this.answerId = answerId;
    }

    public UUID questionId() {
        return questionId;
    }

    public UUID answerId() {
        return answerId;
    }
}
