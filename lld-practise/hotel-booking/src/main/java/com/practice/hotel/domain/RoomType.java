package com.practice.hotel.domain;

import java.math.BigDecimal;
import java.util.Locale;

public record RoomType(String id, String name, String description, int totalRooms, BigDecimal pricePerNight) {

    public String nameKey() {
        return name.trim().toLowerCase(Locale.ROOT);
    }

    // Applies the non-null fields of changes; the id never changes.
    public RoomType withChanges(RoomTypeChanges changes) {
        return new RoomType(
                id,
                changes.name() == null ? name : changes.name(),
                changes.description() == null ? description : changes.description(),
                changes.totalRooms() == null ? totalRooms : changes.totalRooms(),
                changes.pricePerNight() == null ? pricePerNight : changes.pricePerNight());
    }
}
