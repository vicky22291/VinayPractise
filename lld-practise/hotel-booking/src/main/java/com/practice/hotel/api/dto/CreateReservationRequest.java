package com.practice.hotel.api.dto;

import java.time.LocalDate;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

// Dates are yyyy-MM-dd; Jackson rejects any other form, naming the field. StayValidator checks the stay itself.
public record CreateReservationRequest(
        @NotBlank String roomTypeId,
        @NotNull LocalDate checkIn,
        @NotNull LocalDate checkOut,
        @NotNull @Positive Integer rooms) {
}
