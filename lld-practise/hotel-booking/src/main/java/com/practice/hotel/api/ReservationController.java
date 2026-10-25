package com.practice.hotel.api;

import java.time.Instant;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.practice.hotel.api.dto.CreateReservationRequest;
import com.practice.hotel.api.dto.ReservationResponse;
import com.practice.hotel.domain.Reservation;
import com.practice.hotel.mapper.ReservationMapper;
import com.practice.hotel.service.RequestContext;
import com.practice.hotel.service.ReservationService;

@RestController
@RequestMapping("/api/v1/hotels/{hotelId}/reservations")
public class ReservationController {

    private final ReservationService reservationService;
    private final ReservationMapper reservationMapper;
    private final RequestContextFactory requestContextFactory;

    public ReservationController(ReservationService reservationService, ReservationMapper reservationMapper,
            RequestContextFactory requestContextFactory) {
        this.reservationService = reservationService;
        this.reservationMapper = reservationMapper;
        this.requestContextFactory = requestContextFactory;
    }

    // No Location header, because there's no Get reservation API yet.
    @PostMapping
    public ResponseEntity<ReservationResponse> create(
            @RequestAttribute(RequestTimeFilter.REQUEST_TIME_ATTRIBUTE) Instant requestTime,
            @RequestHeader("X-Guest-Id") String guestId,
            @RequestHeader("Idempotency-Key") String idempotencyKey,
            @PathVariable String hotelId,
            @Valid @RequestBody CreateReservationRequest request,
            HttpServletRequest httpRequest) {
        RequestContext context = requestContextFactory.create(
                guestId, requestTime, idempotencyKey, httpRequest.getRequestURI(), request);
        Reservation reservation = reservationService.create(reservationMapper.toCommand(hotelId, request, context));
        return ResponseEntity.status(HttpStatus.CREATED).body(reservationMapper.toResponse(reservation));
    }
}
