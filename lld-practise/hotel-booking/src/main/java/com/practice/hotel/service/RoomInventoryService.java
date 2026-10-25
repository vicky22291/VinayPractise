package com.practice.hotel.service;

import java.time.LocalDate;
import java.util.List;

import com.practice.hotel.domain.Hotel;
import com.practice.hotel.domain.RoomType;

// Keeps the inventory rows in step with a hotel's room types.
public interface RoomInventoryService {

    // Adds rows for each room type, for every date a valid stay can include, starting today.
    void addRoomTypes(String hotelId, List<RoomType> roomTypes, LocalDate today);

    // Adds rows for the room types `after` adds, and sets the new total from today on for each count it changes.
    // Throws RoomCountBelowReservedException, changing nothing, if a new total is below the rooms booked on one of
    // those dates.
    void syncRoomTypes(Hotel before, Hotel after, LocalDate today);
}
