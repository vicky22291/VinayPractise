package com.practice.qabank.exception;

import java.util.UUID;

import com.practice.qabank.domain.Vote;

// One vote, up or down, per user per target. held() is the vote the caller already holds, whichever direction they
// tried, so the message and code tell them which one it is. Only a new key gets here: a retry with the vote's own key
// replays its 201.
public final class AlreadyVotedException extends RuntimeException {

    private final Vote held;
    private final UUID targetId;

    private AlreadyVotedException(String message, Vote held, UUID targetId) {
        super(message);
        this.held = held;
        this.targetId = targetId;
    }

    public static AlreadyVotedException question(Vote held, UUID questionId) {
        return new AlreadyVotedException("You already " + verb(held) + " question " + questionId, held, questionId);
    }

    public static AlreadyVotedException answer(Vote held, UUID answerId) {
        return new AlreadyVotedException("You already " + verb(held) + " answer " + answerId, held, answerId);
    }

    public Vote held() {
        return held;
    }

    public UUID targetId() {
        return targetId;
    }

    private static String verb(Vote held) {
        return switch (held) {
            case UP -> "upvoted";
            case DOWN -> "downvoted";
        };
    }
}
