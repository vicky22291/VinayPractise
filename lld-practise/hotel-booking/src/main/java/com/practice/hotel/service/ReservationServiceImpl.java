package com.practice.hotel.service;

import java.math.BigDecimal;
import java.util.UUID;

import org.springframework.stereotype.Service;

import com.practice.hotel.domain.Hotel;
import com.practice.hotel.domain.OperationType;
import com.practice.hotel.domain.Reservation;
import com.practice.hotel.domain.RoomType;
import com.practice.hotel.domain.Stay;
import com.practice.hotel.error.RoomTypeNotFoundException;
import com.practice.hotel.error.RoomsNotAvailableException;
import com.practice.hotel.repository.ReservationRepository;
import com.practice.hotel.repository.RoomInventoryRepository;

@Service
public class ReservationServiceImpl implements ReservationService {

    private final HotelService hotelService;
    private final IdempotencyService idempotencyService;
    private final RoomInventoryRepository roomInventoryRepository;
    private final ReservationRepository reservationRepository;

    public ReservationServiceImpl(HotelService hotelService, IdempotencyService idempotencyService,
            RoomInventoryRepository roomInventoryRepository, ReservationRepository reservationRepository) {
        this.hotelService = hotelService;
        this.idempotencyService = idempotencyService;
        this.roomInventoryRepository = roomInventoryRepository;
        this.reservationRepository = reservationRepository;
    }

    @Override
    public Reservation create(CreateReservationCommand command) {
        String reservationId = idempotencyService.execute(OperationType.CREATE_RESERVATION, command.context(), () -> {
            Hotel hotel = hotelService.get(command.hotelId());
            RoomType roomType = hotel.findRoomType(command.roomTypeId())
                    .orElseThrow(() -> new RoomTypeNotFoundException(hotel.id(), command.roomTypeId()));
            Stay stay = StayValidator.requireValidStay(
                    command.checkIn(), command.checkOut(), command.context().requestTime());
            if (!roomInventoryRepository.reserve(roomType.id(), stay.nights(), command.rooms())) {
                throw new RoomsNotAvailableException(roomType.id(), command.rooms());
            }
            // Nothing gives the rooms back if this throws, so only save, which can't fail, comes after reserve.
            return reservationRepository.save(newReservation(command, roomType, stay)).id();
        });
        // Saved by the action above, or by the first request with this key.
        return reservationRepository.findById(reservationId).orElseThrow();
    }

    private static Reservation newReservation(CreateReservationCommand command, RoomType roomType, Stay stay) {
        BigDecimal totalPrice = roomType.pricePerNight()
                .multiply(BigDecimal.valueOf(stay.nightCount()))
                .multiply(BigDecimal.valueOf(command.rooms()));
        return new Reservation(UUID.randomUUID().toString(), command.hotelId(), roomType.id(),
                command.context().actorId(), stay.checkIn(), stay.checkOut(), command.rooms(), roomType.pricePerNight(),
                totalPrice, command.context().requestTime());
    }
}
