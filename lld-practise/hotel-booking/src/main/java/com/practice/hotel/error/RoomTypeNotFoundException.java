package com.practice.hotel.error;

public class RoomTypeNotFoundException extends RuntimeException {

    public RoomTypeNotFoundException(String hotelId, String roomTypeId) {
        super("Hotel " + hotelId + " has no room type with id " + roomTypeId);
    }
}
