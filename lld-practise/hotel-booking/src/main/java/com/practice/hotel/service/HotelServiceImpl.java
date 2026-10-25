package com.practice.hotel.service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Service;

import com.practice.hotel.domain.CityKey;
import com.practice.hotel.domain.Hotel;
import com.practice.hotel.domain.OperationType;
import com.practice.hotel.domain.RoomType;
import com.practice.hotel.domain.RoomTypeChanges;
import com.practice.hotel.domain.Stay;
import com.practice.hotel.error.DuplicateRoomTypeException;
import com.practice.hotel.error.HotelNotFoundException;
import com.practice.hotel.error.NotHotelOwnerException;
import com.practice.hotel.error.RoomTypeNotFoundException;
import com.practice.hotel.repository.HotelRepository;
import com.practice.hotel.repository.RoomInventoryRepository;

@Service
public class HotelServiceImpl implements HotelService {

    private final HotelRepository hotelRepository;
    private final IdempotencyService idempotencyService;
    private final RoomInventoryService roomInventoryService;
    private final RoomInventoryRepository roomInventoryRepository;

    public HotelServiceImpl(HotelRepository hotelRepository, IdempotencyService idempotencyService,
            RoomInventoryService roomInventoryService, RoomInventoryRepository roomInventoryRepository) {
        this.hotelRepository = hotelRepository;
        this.idempotencyService = idempotencyService;
        this.roomInventoryService = roomInventoryService;
        this.roomInventoryRepository = roomInventoryRepository;
    }

    @Override
    public Hotel create(CreateHotelCommand command) {
        String hotelId = idempotencyService.execute(OperationType.CREATE_HOTEL, command.context(), () -> {
            Hotel hotel = newHotel(command);
            requireUniqueRoomTypeNames(hotel);
            roomInventoryService.addRoomTypes(hotel.id(), hotel.roomTypes(),
                    StayValidator.today(command.context().requestTime()));
            return hotelRepository.save(hotel).id();
        });
        return get(hotelId);
    }

    @Override
    public Hotel get(String hotelId) {
        return hotelRepository.findById(hotelId).orElseThrow(() -> new HotelNotFoundException(hotelId));
    }

    @Override
    public List<HotelSearchResult> search(HotelSearchQuery query) {
        // Runs first, so a bad stay fails even in a city with no hotels.
        Stay stay = query.checkIn() == null && query.checkOut() == null
                ? null
                : StayValidator.requireValidStay(query.checkIn(), query.checkOut(), query.requestTime());
        List<Hotel> hotels = hotelRepository.findByCity(CityKey.of(query.city()));
        if (stay == null) {
            return hotels.stream().map(hotel -> new HotelSearchResult(hotel, null)).toList();
        }
        // One call covers every room type of every hotel found.
        List<String> roomTypeIds = hotels.stream().flatMap(hotel -> hotel.roomTypes().stream()).map(RoomType::id).toList();
        Map<String, Integer> available = roomInventoryRepository.findAvailable(roomTypeIds, stay.nights(), query.rooms());
        return hotels.stream()
                .map(hotel -> new HotelSearchResult(hotel, availableRoomTypes(hotel, available)))
                .filter(result -> !result.availableRoomTypes().isEmpty())
                .toList();
    }

    // The room types findAvailable kept, in the hotel's room type order.
    private static List<AvailableRoomType> availableRoomTypes(Hotel hotel, Map<String, Integer> available) {
        return hotel.roomTypes().stream()
                .filter(roomType -> available.containsKey(roomType.id()))
                .map(roomType -> new AvailableRoomType(roomType, available.get(roomType.id())))
                .toList();
    }

    @Override
    public Hotel update(UpdateHotelCommand command) {
        // Before the claim, so a missing hotel or a non-owner never claims a key. Safe because ownerId never changes.
        requireOwnedHotel(command.hotelId(), command.context());
        String hotelId = idempotencyService.execute(OperationType.UPDATE_HOTEL, command.context(), () -> {
            // Ids are generated outside the change, which depends only on the hotel it receives.
            List<RoomType> newRoomTypes = command.newRoomTypes().stream().map(HotelServiceImpl::newRoomType).toList();
            return hotelRepository.update(command.hotelId(), hotel -> applyChanges(hotel, command, newRoomTypes))
                    .orElseThrow(() -> new HotelNotFoundException(command.hotelId()))
                    .id();
        });
        return get(hotelId);
    }

    // The change for HotelRepository.update: it runs on the latest hotel while it is locked, and throws to abort.
    private Hotel applyChanges(Hotel hotel, UpdateHotelCommand command, List<RoomType> newRoomTypes) {
        Instant at = command.context().requestTime();
        Hotel updated = hotel.withChanges(command.changes(), at);
        for (RoomTypeChanges changes : command.roomTypeChanges()) {
            updated = updated.withRoomType(requireRoomType(updated, changes.id()).withChanges(changes), at);
        }
        for (RoomType roomType : newRoomTypes) {
            updated = updated.withRoomType(roomType, at);
        }
        requireUniqueRoomTypeNames(updated);
        // Last, so the inventory changes only after every other check has passed. Its 409 aborts the hotel change too.
        roomInventoryService.syncRoomTypes(hotel, updated, StayValidator.today(at));
        return updated;
    }

    private Hotel requireOwnedHotel(String hotelId, RequestContext context) {
        Hotel hotel = get(hotelId);
        if (!hotel.ownerId().equals(context.actorId())) {
            throw new NotHotelOwnerException(hotelId);
        }
        return hotel;
    }

    private RoomType requireRoomType(Hotel hotel, String roomTypeId) {
        return hotel.findRoomType(roomTypeId).orElseThrow(() -> new RoomTypeNotFoundException(hotel.id(), roomTypeId));
    }

    private void requireUniqueRoomTypeNames(Hotel hotel) {
        if (hotel.hasDuplicateRoomTypeNames()) {
            throw new DuplicateRoomTypeException();
        }
    }

    private static Hotel newHotel(CreateHotelCommand command) {
        Instant now = command.context().requestTime();
        List<RoomType> roomTypes = command.roomTypes().stream().map(HotelServiceImpl::newRoomType).toList();
        return new Hotel(newId(), command.context().actorId(), command.name(), command.city(), command.details(),
                now, now, roomTypes);
    }

    private static RoomType newRoomType(NewRoomType roomType) {
        return new RoomType(newId(), roomType.name(), roomType.description(), roomType.totalRooms(),
                roomType.pricePerNight());
    }

    private static String newId() {
        return UUID.randomUUID().toString();
    }
}
