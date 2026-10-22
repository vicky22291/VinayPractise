package com.example.qabank.web;

public class InvalidCursorException extends RuntimeException {
    public InvalidCursorException(String cursor) {
        super("Invalid cursor: " + cursor);
    }
}
