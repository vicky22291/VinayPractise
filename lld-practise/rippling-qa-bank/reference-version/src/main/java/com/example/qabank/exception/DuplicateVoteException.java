package com.example.qabank.exception;

import java.util.UUID;

public class DuplicateVoteException extends RuntimeException {
    public DuplicateVoteException(UUID questionId, UUID voterId) {
        super("User " + voterId + " already upvoted question " + questionId);
    }
}
