package com.practice.hotel.mapper;

import org.springframework.stereotype.Component;

import com.practice.hotel.api.dto.CreateReservationRequest;
import com.practice.hotel.api.dto.ReservationResponse;
import com.practice.hotel.domain.Reservation;
import com.practice.hotel.service.CreateReservationCommand;
import com.practice.hotel.service.RequestContext;

@Component
public class ReservationMapperImpl implements ReservationMapper {

    @Override
    public CreateReservationCommand toCommand(String hotelId, CreateReservationRequest request, RequestContext context) {
        return new CreateReservationCommand(
                context,
                hotelId,
                request.roomTypeId().trim(),
                request.checkIn(),
                request.checkOut(),
                request.rooms());
    }

    @Override
    public ReservationResponse toResponse(Reservation reservation) {
        return new ReservationResponse(
                reservation.id(),
                reservation.hotelId(),
                reservation.roomTypeId(),
                reservation.guestId(),
                reservation.checkIn(),
                reservation.checkOut(),
                reservation.rooms(),
                reservation.pricePerNight(),
                reservation.totalPrice(),
                reservation.createdAt());
    }
}
