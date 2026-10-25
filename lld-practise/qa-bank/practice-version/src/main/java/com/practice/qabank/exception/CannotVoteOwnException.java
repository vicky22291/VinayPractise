package com.practice.qabank.exception;

import java.util.UUID;

import com.practice.qabank.domain.Vote;

// Nobody can vote on a question or answer they wrote. vote() is the direction tried, so the handler picks the code
// from it; the factories pick the message instead of a subclass per target.
public final class CannotVoteOwnException extends RuntimeException {

    private final Vote vote;
    private final UUID targetId;

    private CannotVoteOwnException(String message, Vote vote, UUID targetId) {
        super(message);
        this.vote = vote;
        this.targetId = targetId;
    }

    public static CannotVoteOwnException question(Vote vote, UUID questionId) {
        return new CannotVoteOwnException("You can't " + verb(vote) + " your own question " + questionId, vote,
                questionId);
    }

    public static CannotVoteOwnException answer(Vote vote, UUID answerId) {
        return new CannotVoteOwnException("You can't " + verb(vote) + " your own answer " + answerId, vote, answerId);
    }

    public Vote vote() {
        return vote;
    }

    public UUID targetId() {
        return targetId;
    }

    private static String verb(Vote vote) {
        return switch (vote) {
            case UP -> "upvote";
            case DOWN -> "downvote";
        };
    }
}
