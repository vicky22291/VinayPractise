package com.practice.hotel.domain;

import java.time.LocalDate;

// One row per room type and date. availableRooms is always totalRooms - bookedRooms; it's stored so search can filter on
// it directly.
public record RoomInventory(
        String hotelId, String roomTypeId, LocalDate date, int totalRooms, int bookedRooms, int availableRooms) {

    public static RoomInventory unbooked(String hotelId, String roomTypeId, LocalDate date, int totalRooms) {
        return new RoomInventory(hotelId, roomTypeId, date, totalRooms, 0, totalRooms);
    }

    public RoomInventory book(int rooms) {
        return new RoomInventory(hotelId, roomTypeId, date, totalRooms, bookedRooms + rooms, availableRooms - rooms);
    }

    public RoomInventory withTotalRooms(int newTotal) {
        return new RoomInventory(hotelId, roomTypeId, date, newTotal, bookedRooms, newTotal - bookedRooms);
    }
}
