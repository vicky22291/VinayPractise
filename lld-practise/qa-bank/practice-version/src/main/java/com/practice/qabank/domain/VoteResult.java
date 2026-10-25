package com.practice.qabank.domain;

// What a vote produced: the target's count in the vote's direction, including this vote. It's also the idempotency
// store's value, so a replay returns this count, not the live one.
public record VoteResult(int count) {
}
