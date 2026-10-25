package com.practice.qabank.domain;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

// Lives inside Question.answers, so it holds no questionId. updatedAt is null until the first real edit. Its votes live
// here too, so a vote on it is a change to its question.
public record Answer(UUID id, String authorId, String content, Instant createdAt, Instant updatedAt, Votes votes) {

    public Answer {
        votes = votes == null ? Votes.NONE : votes;
    }

    public Answer withIdAndCreatedAt(UUID id, Instant createdAt) {
        return new Answer(Objects.requireNonNull(id, "id"), authorId, content,
                Objects.requireNonNull(createdAt, "createdAt"), updatedAt, votes);
    }

    // Exact comparison, no trimming. A no-op returns this instance, so callers can tell nothing changed.
    public Answer withEdit(String content, Instant now) {
        if (Objects.equals(this.content, content)) {
            return this;
        }
        return new Answer(id, authorId, content, createdAt, now, votes);
    }

    // A vote isn't an edit, so updatedAt doesn't move.
    public Answer withVote(String voterId, Vote vote) {
        return new Answer(id, authorId, content, createdAt, updatedAt, votes.with(voterId, vote));
    }
}
