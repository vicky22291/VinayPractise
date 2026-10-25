package com.practice.hotel.api.dto;

import java.math.BigDecimal;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;

public record RoomTypeRequest(
        @NotBlank String name,
        @NotBlank String description,
        @NotNull @PositiveOrZero Integer count,
        @NotNull @Positive BigDecimal pricePerNight) {
}
