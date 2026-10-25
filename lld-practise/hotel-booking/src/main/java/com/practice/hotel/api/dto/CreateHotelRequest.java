package com.practice.hotel.api.dto;

import java.util.List;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

public record CreateHotelRequest(
        @NotBlank String name,
        @NotBlank String city,
        String details,
        @NotEmpty List<@NotNull @Valid RoomTypeRequest> roomTypes) {
}
