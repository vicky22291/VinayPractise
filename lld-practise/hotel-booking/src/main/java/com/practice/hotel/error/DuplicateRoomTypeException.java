package com.practice.hotel.error;

public class DuplicateRoomTypeException extends RuntimeException {

    public DuplicateRoomTypeException() {
        super("Room type names must be unique within a hotel, ignoring case and surrounding spaces");
    }
}
