package com.practice.hotel.service;

import com.practice.hotel.domain.RoomType;

// available is the number of rooms free on the worst night of the stay.
public record AvailableRoomType(RoomType roomType, int available) {
}
