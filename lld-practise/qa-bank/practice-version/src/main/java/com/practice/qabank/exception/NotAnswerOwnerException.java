package com.practice.qabank.exception;

import java.util.UUID;

// Thrown for the question's author too: only the answer's own author may edit it.
public final class NotAnswerOwnerException extends NotOwnerException {

    private final UUID questionId;
    private final UUID answerId;

    public NotAnswerOwnerException(UUID questionId, UUID answerId) {
        super("Only the author can update answer " + answerId);
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
