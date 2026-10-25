package com.practice.hotel.error;

public class InvalidStayException extends RuntimeException {

    public InvalidStayException(String message) {
        super(message);
    }
}
