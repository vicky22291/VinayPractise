package com.practice.hotel.error;

public class InvalidIdempotencyKeyException extends RuntimeException {

    public InvalidIdempotencyKeyException(int maxLength) {
        super("Idempotency-Key header must not be blank or longer than " + maxLength + " characters");
    }
}
