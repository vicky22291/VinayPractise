package com.practice.hotel.api.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.validation.Valid;
import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

// Send only what changes: an absent or null field stays as it is. The @Pattern lets null through but fails blank text.
public record UpdateHotelRequest(
        @Pattern(regexp = "(?s).*\\S.*", message = "must not be blank") String name,
        @Pattern(regexp = "(?s).*\\S.*", message = "must not be blank") String city,
        String details,
        @Size(min = 1, message = "must not be empty") List<@NotNull @Valid RoomTypeChangeRequest> roomTypes) {

    @JsonIgnore
    @AssertTrue(message = "at least one of name, city, details or roomTypes must be sent")
    public boolean isAnyFieldSet() {
        return name != null || city != null || details != null || roomTypes != null;
    }
}
