package com.practice.qabank.exception;

// Base for "the caller isn't the author" errors. Like NotFoundException, it carries no HTTP status or error code;
// ApiExceptionHandler maps each permitted subtype to 403 and its own code.
public abstract sealed class NotOwnerException extends RuntimeException
        permits NotQuestionOwnerException, NotAnswerOwnerException {

    protected NotOwnerException(String message) {
        super(message);
    }
}
