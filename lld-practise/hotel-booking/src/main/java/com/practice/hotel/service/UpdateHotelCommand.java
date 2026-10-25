package com.practice.hotel.service;

import java.util.List;

import com.practice.hotel.domain.HotelChanges;
import com.practice.hotel.domain.RoomTypeChanges;

public record UpdateHotelCommand(
        RequestContext context,
        String hotelId,
        HotelChanges changes,
        List<RoomTypeChanges> roomTypeChanges,
        List<NewRoomType> newRoomTypes) {
}
