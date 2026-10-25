package com.practice.hotel.mapper;

import com.practice.hotel.api.dto.CreateReservationRequest;
import com.practice.hotel.api.dto.ReservationResponse;
import com.practice.hotel.domain.Reservation;
import com.practice.hotel.service.CreateReservationCommand;
import com.practice.hotel.service.RequestContext;

public interface ReservationMapper {

    CreateReservationCommand toCommand(String hotelId, CreateReservationRequest request, RequestContext context);

    ReservationResponse toResponse(Reservation reservation);
}
