package com.practice.hotel.service;

import java.time.Instant;
import java.time.LocalDate;

// A date that wasn't sent is null. requestTime gives today for the stay rules.
public record HotelSearchQuery(String city, LocalDate checkIn, LocalDate checkOut, int rooms, Instant requestTime) {
}
