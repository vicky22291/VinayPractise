package com.practice.hotel.api.dto;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

public record ReservationResponse(
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
