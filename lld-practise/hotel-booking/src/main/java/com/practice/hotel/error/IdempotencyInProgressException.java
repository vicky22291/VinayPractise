package com.practice.hotel.error;

public class IdempotencyInProgressException extends RuntimeException {

    public IdempotencyInProgressException(String idempotencyKey) {
        super("The first request with Idempotency-Key " + idempotencyKey + " is still running");
    }
}
