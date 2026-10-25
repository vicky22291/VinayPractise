package com.practice.hotel.api.dto;

import java.math.BigDecimal;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;

// With an id, changes that room type (null fields stay as they are). Without an id, adds a new one.
public record RoomTypeChangeRequest(
        String id,
        @Pattern(regexp = "(?s).*\\S.*", message = "must not be blank") String name,
        @Pattern(regexp = "(?s).*\\S.*", message = "must not be blank") String description,
        @PositiveOrZero Integer count,
        @Positive BigDecimal pricePerNight) {

    @JsonIgnore
    @AssertTrue(message = "a new room type (no id) needs name, description, count and pricePerNight")
    public boolean isCompleteWhenNew() {
        return id != null || (name != null && description != null && count != null && pricePerNight != null);
    }

    @JsonIgnore
    @AssertTrue(message = "a change (with an id) needs at least one of name, description, count or pricePerNight")
    public boolean isAnyFieldSetWhenChanging() {
        return id == null || name != null || description != null || count != null || pricePerNight != null;
    }
}
