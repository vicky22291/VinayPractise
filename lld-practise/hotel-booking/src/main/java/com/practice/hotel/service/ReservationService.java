package com.practice.hotel.service;

import com.practice.hotel.domain.Reservation;

public interface ReservationService {

    Reservation create(CreateReservationCommand command);
}
