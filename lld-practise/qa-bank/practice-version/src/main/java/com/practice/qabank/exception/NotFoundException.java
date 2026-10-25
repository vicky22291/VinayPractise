package com.practice.qabank.exception;

// Base for every "this resource doesn't exist" error. It carries no HTTP status or error code, so the service stays
// free of web concerns; ApiExceptionHandler picks both with an exhaustive switch over the permitted subtypes.
public abstract sealed class NotFoundException extends RuntimeException
        permits QuestionNotFoundException, AnswerNotFoundException {

    protected NotFoundException(String message) {
        super(message);
    }
}
