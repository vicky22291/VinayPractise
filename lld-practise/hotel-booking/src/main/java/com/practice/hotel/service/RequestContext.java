package com.practice.hotel.service;

import java.time.Instant;

import com.practice.hotel.error.InvalidIdempotencyKeyException;
import com.practice.hotel.error.UnauthorizedException;

public record RequestContext(String actorId, Instant requestTime, String idempotencyKey, String requestHash) {

    public static final int MAX_IDEMPOTENCY_KEY_LENGTH = 255;

    public RequestContext {
        if (actorId == null || actorId.isBlank()) {
            throw new UnauthorizedException();
        }
        if (idempotencyKey == null || idempotencyKey.isBlank() || idempotencyKey.length() > MAX_IDEMPOTENCY_KEY_LENGTH) {
            throw new InvalidIdempotencyKeyException(MAX_IDEMPOTENCY_KEY_LENGTH);
        }
    }
}
