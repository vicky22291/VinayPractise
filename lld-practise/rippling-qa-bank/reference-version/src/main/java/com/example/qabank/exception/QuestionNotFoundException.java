package com.example.qabank.exception;

import java.util.UUID;

public class QuestionNotFoundException extends RuntimeException {
    public QuestionNotFoundException(UUID questionId) {
        super("Question " + questionId + " not found");
    }
}
