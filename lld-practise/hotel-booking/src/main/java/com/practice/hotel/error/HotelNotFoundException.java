package com.practice.hotel.error;

public class HotelNotFoundException extends RuntimeException {

    private final String hotelId;

    public HotelNotFoundException(String hotelId) {
        super("No hotel with id " + hotelId);
        this.hotelId = hotelId;
    }

    public String hotelId() {
        return hotelId;
    }
}
