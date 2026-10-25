package com.practice.hotel.domain;

import java.time.Instant;

public record IdempotencyRecord(
        IdempotencyKey key,
        String requestHash,
        IdempotencyStatus status,
        String resourceId,
        Instant createdAt) {
}
