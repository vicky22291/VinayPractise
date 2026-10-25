package com.practice.hotel.repository;

import java.util.Optional;

import com.practice.hotel.domain.Reservation;

public interface ReservationRepository {

    Reservation save(Reservation reservation);

    Optional<Reservation> findById(String reservationId);
}
