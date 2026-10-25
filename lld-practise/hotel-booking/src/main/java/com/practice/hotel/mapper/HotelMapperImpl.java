package com.practice.hotel.mapper;

import java.util.List;

import org.springframework.stereotype.Component;

import com.practice.hotel.api.dto.AvailableRoomTypeResponse;
import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.HotelSearchResponse;
import com.practice.hotel.api.dto.HotelSummaryResponse;
import com.practice.hotel.api.dto.RoomTypeChangeRequest;
import com.practice.hotel.api.dto.RoomTypeRequest;
import com.practice.hotel.api.dto.RoomTypeResponse;
import com.practice.hotel.api.dto.UpdateHotelRequest;
import com.practice.hotel.domain.Hotel;
import com.practice.hotel.domain.HotelChanges;
import com.practice.hotel.domain.RoomType;
import com.practice.hotel.domain.RoomTypeChanges;
import com.practice.hotel.service.AvailableRoomType;
import com.practice.hotel.service.CreateHotelCommand;
import com.practice.hotel.service.HotelSearchResult;
import com.practice.hotel.service.NewRoomType;
import com.practice.hotel.service.RequestContext;
import com.practice.hotel.service.UpdateHotelCommand;

@Component
public class HotelMapperImpl implements HotelMapper {

    @Override
    public CreateHotelCommand toCommand(CreateHotelRequest request, RequestContext context) {
        return new CreateHotelCommand(
                context,
                request.name().trim(),
                request.city().trim(),
                request.details() == null ? "" : request.details().trim(),
                request.roomTypes().stream().map(HotelMapperImpl::toNewRoomType).toList());
    }

    // Entries with an id become RoomTypeChanges and the rest NewRoomType. A field that wasn't sent stays null.
    @Override
    public UpdateHotelCommand toUpdateCommand(String hotelId, UpdateHotelRequest request, RequestContext context) {
        List<RoomTypeChangeRequest> roomTypes = request.roomTypes() == null ? List.of() : request.roomTypes();
        return new UpdateHotelCommand(
                context,
                hotelId,
                new HotelChanges(trim(request.name()), trim(request.city()), trim(request.details())),
                roomTypes.stream().filter(roomType -> roomType.id() != null).map(HotelMapperImpl::toRoomTypeChanges).toList(),
                roomTypes.stream().filter(roomType -> roomType.id() == null).map(HotelMapperImpl::toNewRoomType).toList());
    }

    @Override
    public HotelResponse toResponse(Hotel hotel) {
        return new HotelResponse(
                hotel.id(),
                hotel.name(),
                hotel.city(),
                hotel.details(),
                hotel.createdAt(),
                hotel.updatedAt(),
                hotel.roomTypes().stream().map(HotelMapperImpl::toRoomTypeResponse).toList());
    }

    // Keeps the order of results. Each item is a summary: the full room types come from get. availableRoomTypes stays
    // null when the search has no dates.
    @Override
    public HotelSearchResponse toSearchResponse(List<HotelSearchResult> results) {
        return new HotelSearchResponse(results.stream().map(HotelMapperImpl::toSummaryResponse).toList());
    }

    private static HotelSummaryResponse toSummaryResponse(HotelSearchResult result) {
        Hotel hotel = result.hotel();
        List<AvailableRoomTypeResponse> availableRoomTypes = result.availableRoomTypes() == null
                ? null
                : result.availableRoomTypes().stream().map(HotelMapperImpl::toAvailableRoomTypeResponse).toList();
        return new HotelSummaryResponse(hotel.id(), hotel.name(), hotel.city(), hotel.details(), availableRoomTypes);
    }

    private static AvailableRoomTypeResponse toAvailableRoomTypeResponse(AvailableRoomType availableRoomType) {
        RoomType roomType = availableRoomType.roomType();
        return new AvailableRoomTypeResponse(roomType.id(), roomType.name(), roomType.pricePerNight(),
                availableRoomType.available());
    }

    private static NewRoomType toNewRoomType(RoomTypeRequest request) {
        return new NewRoomType(request.name().trim(), request.description().trim(), request.count(), request.pricePerNight());
    }

    // Only for entries without an id, which validation guarantees are complete.
    private static NewRoomType toNewRoomType(RoomTypeChangeRequest request) {
        return new NewRoomType(request.name().trim(), request.description().trim(), request.count(), request.pricePerNight());
    }

    private static RoomTypeChanges toRoomTypeChanges(RoomTypeChangeRequest request) {
        return new RoomTypeChanges(request.id(), trim(request.name()), trim(request.description()),
                request.count(), request.pricePerNight());
    }

    private static RoomTypeResponse toRoomTypeResponse(RoomType roomType) {
        return new RoomTypeResponse(roomType.id(), roomType.name(), roomType.description(),
                roomType.totalRooms(), roomType.pricePerNight());
    }

    private static String trim(String text) {
        return text == null ? null : text.trim();
    }
}
