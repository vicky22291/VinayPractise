package com.practice.hotel.api.dto;

import java.math.BigDecimal;

public record RoomTypeResponse(String id, String name, String description, int count, BigDecimal pricePerNight) {
}
