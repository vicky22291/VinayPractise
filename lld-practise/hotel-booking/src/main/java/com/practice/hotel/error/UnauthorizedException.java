package com.practice.hotel.error;

public class UnauthorizedException extends RuntimeException {

    public UnauthorizedException() {
        super("X-Admin-Id or X-Guest-Id header must not be blank");
    }
}
