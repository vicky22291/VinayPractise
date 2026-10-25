package com.practice.hotel.api.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonInclude;

// availableRoomTypes is null, and so left out of the JSON, when the search has no dates.
public record HotelSummaryResponse(
        String id,
        String name,
        String city,
        String details,
        @JsonInclude(JsonInclude.Include.NON_NULL) List<AvailableRoomTypeResponse> availableRoomTypes) {
}
