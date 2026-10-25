package com.practice.hotel.error;

public class RoomsNotAvailableException extends RuntimeException {

    public RoomsNotAvailableException(String roomTypeId, int rooms) {
        super("Room type " + roomTypeId + " has fewer than " + rooms + " rooms free on a night of the stay");
    }
}
