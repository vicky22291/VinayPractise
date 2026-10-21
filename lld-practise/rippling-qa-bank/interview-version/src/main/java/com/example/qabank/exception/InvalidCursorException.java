package com.example.qabank.exception;

import java.util.UUID;

public class InvalidCursorException extends RuntimeException {
    public InvalidCursorException(UUID cursor) {
        super("Unknown cursor " + cursor);
    }
}
