package com.practice.hotel.error;

public class RoomCountBelowReservedException extends RuntimeException {

    public RoomCountBelowReservedException() {
        super("A room type's count can't drop below the rooms booked on a date from today on");
    }
}
