package com.practice.qabank.domain;

// A vote's direction. Each names its two operations, so the service builds the key without a switch, and an upvote
// and a downvote under one Idempotency-Key are separate entries.
public enum Vote {
    UP(Operation.UPVOTE_QUESTION, Operation.UPVOTE_ANSWER),
    DOWN(Operation.DOWNVOTE_QUESTION, Operation.DOWNVOTE_ANSWER);

    private final Operation questionOperation;
    private final Operation answerOperation;

    Vote(Operation questionOperation, Operation answerOperation) {
        this.questionOperation = questionOperation;
        this.answerOperation = answerOperation;
    }

    public Operation questionOperation() {
        return questionOperation;
    }

    public Operation answerOperation() {
        return answerOperation;
    }
}
