package com.practice.hotel.domain;

import java.math.BigDecimal;

// The changes to the room type with this id. A null field keeps the current value.
public record RoomTypeChanges(String id, String name, String description, Integer totalRooms, BigDecimal pricePerNight) {
}
