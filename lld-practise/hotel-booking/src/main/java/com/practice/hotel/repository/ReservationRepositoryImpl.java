package com.practice.hotel.repository;

import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Repository;

import com.practice.hotel.domain.Reservation;

@Repository
public class ReservationRepositoryImpl implements ReservationRepository {

    private final ConcurrentHashMap<String, Reservation> reservations = new ConcurrentHashMap<>();

    @Override
    public Reservation save(Reservation reservation) {
        reservations.put(reservation.id(), reservation);
        return reservation;
    }

    @Override
    public Optional<Reservation> findById(String reservationId) {
        return Optional.ofNullable(reservations.get(reservationId));
    }
}
