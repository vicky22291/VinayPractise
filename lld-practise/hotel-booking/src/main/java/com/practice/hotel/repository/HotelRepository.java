package com.practice.hotel.repository;

import java.util.List;
import java.util.Optional;
import java.util.function.UnaryOperator;

import com.practice.hotel.domain.CityKey;
import com.practice.hotel.domain.Hotel;

public interface HotelRepository {

    Hotel save(Hotel hotel);

    Optional<Hotel> findById(String hotelId);

    // Hotels whose cityKey() equals city, sorted by name ignoring case, then by id, so results never shuffle.
    List<Hotel> findByCity(CityKey city);

    // Applies change atomically to the latest stored hotel and stores the result; empty if there's no such hotel.
    // If change throws, the stored hotel stays as it was.
    Optional<Hotel> update(String hotelId, UnaryOperator<Hotel> change);
}
