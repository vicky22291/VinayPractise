package com.practice.hotel.error;

public class IdempotencyKeyReusedException extends RuntimeException {

    public IdempotencyKeyReusedException(String idempotencyKey) {
        super("Idempotency-Key " + idempotencyKey + " was already used for a different request");
    }
}
