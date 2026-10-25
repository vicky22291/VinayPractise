package com.practice.qabank.exception;

import java.util.UUID;

// One answer per user per question. The message names the existing answer, so the client knows where to PUT instead.
public final class AnswerAlreadyExistsException extends RuntimeException {

    private final UUID questionId;
    private final UUID answerId;

    public AnswerAlreadyExistsException(UUID questionId, UUID answerId) {
        super("Question " + questionId + " already has answer " + answerId + " by this user");
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
