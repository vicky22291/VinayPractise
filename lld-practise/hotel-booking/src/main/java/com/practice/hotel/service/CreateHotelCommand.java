package com.practice.hotel.service;

import java.util.List;

public record CreateHotelCommand(
        RequestContext context,
        String name,
        String city,
        String details,
        List<NewRoomType> roomTypes) {
}
