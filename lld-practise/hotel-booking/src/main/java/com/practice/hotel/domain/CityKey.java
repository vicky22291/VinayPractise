package com.practice.hotel.domain;

import java.util.Locale;

// A city as search compares it: trimmed and lowercased with Locale.ROOT, the same rule as RoomType.nameKey().
public record CityKey(String value) {

    public static CityKey of(String city) {
        return new CityKey(city.trim().toLowerCase(Locale.ROOT));
    }
}
