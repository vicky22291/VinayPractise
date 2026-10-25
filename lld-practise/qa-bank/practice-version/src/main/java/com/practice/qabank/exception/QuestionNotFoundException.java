package com.practice.qabank.exception;

import java.util.UUID;

public final class QuestionNotFoundException extends NotFoundException {

    private final UUID id;

    public QuestionNotFoundException(UUID id) {
        super("Question " + id + " not found");
        this.id = id;
    }

    public UUID id() {
        return id;
    }
}
