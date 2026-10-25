package com.practice.hotel.repository;

import java.time.LocalDate;
import java.util.Collection;
import java.util.List;
import java.util.Map;

// One RoomInventory row per room type and date. A date with no row can't be booked.
public interface RoomInventoryRepository {

    // Adds a row for each date from `from` (included) to `to` (excluded), with every room available.
    void addRoomType(String hotelId, String roomTypeId, int totalRooms, LocalDate from, LocalDate to);

    // If every date has a row with at least `rooms` available, books them on each date and returns true. Otherwise
    // changes nothing and returns false.
    boolean reserve(String roomTypeId, List<LocalDate> dates, int rooms);

    // roomTypeId to the fewest rooms available over the dates, for the room types with at least `rooms` available on
    // every date. A room type that is short on any date, or has no row for one, is left out.
    Map<String, Integer> findAvailable(Collection<String> roomTypeIds, List<LocalDate> dates, int rooms);

    // Sets each room type's new total on its rows from `from` on. If any of those rows has more rooms booked than the
    // new total, changes nothing and returns false.
    boolean changeTotalRooms(Map<String, Integer> totals, LocalDate from);
}
