package com.practice.hotel.service;

import java.util.List;

import com.practice.hotel.domain.Hotel;

// availableRoomTypes is null when the search has no dates.
public record HotelSearchResult(Hotel hotel, List<AvailableRoomType> availableRoomTypes) {
}
