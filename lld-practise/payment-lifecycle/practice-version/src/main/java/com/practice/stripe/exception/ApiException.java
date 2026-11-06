package com.practice.stripe.exception;

/** A deliberate domain rejection that the HTTP adapter can translate. */
public class ApiException extends RuntimeException {
    private final int status;
    public ApiException(int status, String message) { super(message); this.status = status; }
    public int status() { return status; }
    public static ApiException invalid(String message) { return new ApiException(400, message); }
    public static ApiException missing(String message) { return new ApiException(404, message); }
    public static ApiException conflict(String message) { return new ApiException(409, message); }
}
