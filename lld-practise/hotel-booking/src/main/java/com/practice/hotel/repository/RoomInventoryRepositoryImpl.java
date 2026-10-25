package com.practice.hotel.repository;

import java.time.LocalDate;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.NavigableMap;
import java.util.TreeMap;

import org.springframework.stereotype.Repository;

import com.practice.hotel.domain.RoomInventory;

// Every method is synchronized: one lock means a booking and a count change never interleave.
@Repository
public class RoomInventoryRepositoryImpl implements RoomInventoryRepository {

    private final Map<String, NavigableMap<LocalDate, RoomInventory>> rowsByRoomType = new HashMap<>();

    @Override
    public synchronized void addRoomType(String hotelId, String roomTypeId, int totalRooms, LocalDate from, LocalDate to) {
        NavigableMap<LocalDate, RoomInventory> rows = rows(roomTypeId);
        from.datesUntil(to).forEach(date -> rows.put(date, RoomInventory.unbooked(hotelId, roomTypeId, date, totalRooms)));
    }

    @Override
    public synchronized boolean reserve(String roomTypeId, List<LocalDate> dates, int rooms) {
        if (fewestAvailable(roomTypeId, dates) < rooms) {
            return false;
        }
        NavigableMap<LocalDate, RoomInventory> rows = rows(roomTypeId);
        dates.forEach(date -> rows.put(date, rows.get(date).book(rooms)));
        return true;
    }

    @Override
    public synchronized Map<String, Integer> findAvailable(
            Collection<String> roomTypeIds, List<LocalDate> dates, int rooms) {
        Map<String, Integer> available = new HashMap<>();
        for (String roomTypeId : roomTypeIds) {
            int fewest = fewestAvailable(roomTypeId, dates);
            if (fewest >= rooms) {
                available.put(roomTypeId, fewest);
            }
        }
        return available;
    }

    @Override
    public synchronized boolean changeTotalRooms(Map<String, Integer> totals, LocalDate from) {
        for (Map.Entry<String, Integer> total : totals.entrySet()) {
            Collection<RoomInventory> rows = rows(total.getKey()).tailMap(from, true).values();
            if (rows.stream().anyMatch(row -> row.bookedRooms() > total.getValue())) {
                return false;
            }
        }
        totals.forEach((roomTypeId, total) ->
                rows(roomTypeId).tailMap(from, true).replaceAll((date, row) -> row.withTotalRooms(total)));
        return true;
    }

    // A date with no row counts as 0 available, so it can't be booked.
    private int fewestAvailable(String roomTypeId, List<LocalDate> dates) {
        NavigableMap<LocalDate, RoomInventory> rows = rows(roomTypeId);
        return dates.stream()
                .mapToInt(date -> rows.containsKey(date) ? rows.get(date).availableRooms() : 0)
                .min()
                .orElse(0);
    }

    private NavigableMap<LocalDate, RoomInventory> rows(String roomTypeId) {
        return rowsByRoomType.computeIfAbsent(roomTypeId, id -> new TreeMap<>());
    }
}
