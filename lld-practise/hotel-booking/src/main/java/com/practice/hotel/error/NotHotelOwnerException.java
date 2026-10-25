package com.practice.hotel.error;

public class NotHotelOwnerException extends RuntimeException {

    public NotHotelOwnerException(String hotelId) {
        super("Only the owner can update hotel " + hotelId);
    }
}
