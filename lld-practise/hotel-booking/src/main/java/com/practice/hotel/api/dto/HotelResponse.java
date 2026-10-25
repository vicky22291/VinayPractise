package com.practice.hotel.api.dto;

import java.time.Instant;
import java.util.List;

public record HotelResponse(
        String id,
        String name,
        String city,
        String details,
        Instant createdAt,
        Instant updatedAt,
        List<RoomTypeResponse> roomTypes) {
}
