package com.practice.hotel.api.dto;

import java.math.BigDecimal;

// available is the number of rooms free on the worst night of the stay.
public record AvailableRoomTypeResponse(String id, String name, BigDecimal pricePerNight, int available) {
}
