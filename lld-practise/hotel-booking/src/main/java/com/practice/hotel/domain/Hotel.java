package com.practice.hotel.domain;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.IntStream;

public record Hotel(
        String id,
        String ownerId,
        String name,
        String city,
        String details,
        Instant createdAt,
        Instant updatedAt,
        List<RoomType> roomTypes) {

    public Hotel {
        roomTypes = List.copyOf(roomTypes);
    }

    // Derived from city on every call, so a city change is seen at once.
    public CityKey cityKey() {
        return CityKey.of(city);
    }

    public boolean hasDuplicateRoomTypeNames() {
        return roomTypes.stream().map(RoomType::nameKey).distinct().count() < roomTypes.size();
    }

    // Applies the non-null fields of changes and sets updatedAt to at.
    public Hotel withChanges(HotelChanges changes, Instant at) {
        return new Hotel(
                id,
                ownerId,
                changes.name() == null ? name : changes.name(),
                changes.city() == null ? city : changes.city(),
                changes.details() == null ? details : changes.details(),
                createdAt,
                at,
                roomTypes);
    }

    // Replaces the room type with the same id in place, or appends it if the id is new, and sets updatedAt to at.
    public Hotel withRoomType(RoomType roomType, Instant at) {
        List<RoomType> updated = new ArrayList<>(roomTypes);
        int index = indexOfRoomType(roomType.id());
        if (index < 0) {
            updated.add(roomType);
        } else {
            updated.set(index, roomType);
        }
        return new Hotel(id, ownerId, name, city, details, createdAt, at, updated);
    }

    public Optional<RoomType> findRoomType(String roomTypeId) {
        int index = indexOfRoomType(roomTypeId);
        return index < 0 ? Optional.empty() : Optional.of(roomTypes.get(index));
    }

    private int indexOfRoomType(String roomTypeId) {
        return IntStream.range(0, roomTypes.size())
                .filter(i -> roomTypes.get(i).id().equals(roomTypeId))
                .findFirst()
                .orElse(-1);
    }
}
