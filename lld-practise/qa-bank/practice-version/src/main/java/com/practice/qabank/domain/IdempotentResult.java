package com.practice.qabank.domain;

// replayed is true when the key was already used and value is the stored outcome of that first call.
public record IdempotentResult<T>(T value, boolean replayed) {
}
