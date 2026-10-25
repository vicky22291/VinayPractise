package com.practice.qabank.domain;

// Every write that takes an Idempotency-Key. Part of the stored key, so a key reused for another write never replays.
public enum Operation {
    CREATE_QUESTION,
    UPDATE_QUESTION,
    ADD_ANSWER,
    UPDATE_ANSWER,
    UPVOTE_QUESTION,
    UPVOTE_ANSWER,
    DOWNVOTE_QUESTION,
    DOWNVOTE_ANSWER
}
