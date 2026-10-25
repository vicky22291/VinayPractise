package com.practice.hotel.service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.stereotype.Service;

import com.practice.hotel.domain.Hotel;
import com.practice.hotel.domain.RoomType;
import com.practice.hotel.error.RoomCountBelowReservedException;
import com.practice.hotel.repository.RoomInventoryRepository;

@Service
public class RoomInventoryServiceImpl implements RoomInventoryService {

    private final RoomInventoryRepository roomInventoryRepository;

    public RoomInventoryServiceImpl(RoomInventoryRepository roomInventoryRepository) {
        this.roomInventoryRepository = roomInventoryRepository;
    }

    @Override
    public void addRoomTypes(String hotelId, List<RoomType> roomTypes, LocalDate today) {
        for (RoomType roomType : roomTypes) {
            roomInventoryRepository.addRoomType(hotelId, roomType.id(), roomType.totalRooms(), today,
                    today.plusDays(StayValidator.MAX_DAYS_AHEAD));
        }
    }

    @Override
    public void syncRoomTypes(Hotel before, Hotel after, LocalDate today) {
        Map<String, Integer> changedTotals = new HashMap<>();
        List<RoomType> added = new ArrayList<>();
        for (RoomType roomType : after.roomTypes()) {
            Optional<RoomType> old = before.findRoomType(roomType.id());
            if (old.isEmpty()) {
                added.add(roomType);
            } else if (old.get().totalRooms() != roomType.totalRooms()) {
                changedTotals.put(roomType.id(), roomType.totalRooms());
            }
        }
        if (!roomInventoryRepository.changeTotalRooms(changedTotals, today)) {
            throw new RoomCountBelowReservedException();
        }
        addRoomTypes(after.id(), added, today);
    }
}
