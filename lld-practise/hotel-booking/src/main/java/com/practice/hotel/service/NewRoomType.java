package com.practice.hotel.service;

import java.math.BigDecimal;

public record NewRoomType(String name, String description, int totalRooms, BigDecimal pricePerNight) {
}
