package com.practice.hotel.repository;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.UnaryOperator;

import org.springframework.stereotype.Repository;

import com.practice.hotel.domain.CityKey;
import com.practice.hotel.domain.Hotel;

@Repository
public class HotelRepositoryImpl implements HotelRepository {

    private static final Comparator<Hotel> BY_NAME_THEN_ID =
            Comparator.comparing(Hotel::name, String.CASE_INSENSITIVE_ORDER).thenComparing(Hotel::id);

    private final ConcurrentHashMap<String, Hotel> hotels = new ConcurrentHashMap<>();

    @Override
    public Hotel save(Hotel hotel) {
        hotels.put(hotel.id(), hotel);
        return hotel;
    }

    @Override
    public Optional<Hotel> findById(String hotelId) {
        return Optional.ofNullable(hotels.get(hotelId));
    }

    // A scan of the current hotels, so a city change by update shows up with no index to keep in sync.
    @Override
    public List<Hotel> findByCity(CityKey city) {
        return hotels.values().stream()
                .filter(hotel -> hotel.cityKey().equals(city))
                .sorted(BY_NAME_THEN_ID)
                .toList();
    }

    @Override
    public Optional<Hotel> update(String hotelId, UnaryOperator<Hotel> change) {
        return Optional.ofNullable(hotels.computeIfPresent(hotelId, (id, hotel) -> change.apply(hotel)));
    }
}
