package com.practice.hotel.service;

import java.time.LocalDate;

public record CreateReservationCommand(
        RequestContext context,
        String hotelId,
        String roomTypeId,
        LocalDate checkIn,
        LocalDate checkOut,
        int rooms) {
}
