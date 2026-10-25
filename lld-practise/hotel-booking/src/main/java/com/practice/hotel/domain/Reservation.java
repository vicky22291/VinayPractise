package com.practice.hotel.domain;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

// pricePerNight is copied from the room type at booking time, so a later price change doesn't touch it.
public record Reservation(
        String id,
        String hotelId,
        String roomTypeId,
        String guestId,
        LocalDate checkIn,
        LocalDate checkOut,
        int rooms,
        BigDecimal pricePerNight,
        BigDecimal totalPrice,
        Instant createdAt) {
}
