package com.example.qabank.exception;

import java.util.UUID;

public class DuplicateVoteException extends RuntimeException {
    public DuplicateVoteException(UUID questionId) {
        super("Already upvoted question " + questionId);
    }
}
