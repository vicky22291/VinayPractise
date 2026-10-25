package com.practice.qabank.domain;

import java.util.UUID;

// Scoped per caller, operation and target, so the same Idempotency-Key value from another user, for another write, or
// on another question or answer is a separate entry. targetId is null for create, which has no target yet.
public record IdempotencyKey(String userId, Operation operation, UUID targetId, String key) {
}
