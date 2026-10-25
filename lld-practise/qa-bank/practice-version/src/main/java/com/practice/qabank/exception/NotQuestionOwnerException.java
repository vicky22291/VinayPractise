package com.practice.qabank.exception;

import java.util.UUID;

public final class NotQuestionOwnerException extends NotOwnerException {

    private final UUID id;

    public NotQuestionOwnerException(UUID id) {
        super("Only the author can update question " + id);
        this.id = id;
    }

    public UUID id() {
        return id;
    }
}
