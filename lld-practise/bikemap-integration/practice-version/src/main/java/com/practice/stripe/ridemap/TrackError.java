package com.practice.stripe.ridemap;

/** A missing or malformed ride file. */
public class TrackError extends RuntimeException {
    public TrackError(String message) {
        super(message);
    }

    public TrackError(String message, Throwable cause) {
        super(message, cause);
    }
}
