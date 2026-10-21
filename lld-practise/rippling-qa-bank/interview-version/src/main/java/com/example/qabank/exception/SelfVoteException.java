package com.example.qabank.exception;

import java.util.UUID;

public class SelfVoteException extends RuntimeException {
    public SelfVoteException(UUID questionId) {
        super("Authors cannot upvote their own question " + questionId);
    }
}
