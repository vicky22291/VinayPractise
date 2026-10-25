package com.practice.hotel.domain;

// The hotel fields an update sends. A null field keeps the current value.
public record HotelChanges(String name, String city, String details) {
}
