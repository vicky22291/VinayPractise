package com.practice.hotel.mapper;

import java.util.List;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.HotelSearchResponse;
import com.practice.hotel.api.dto.UpdateHotelRequest;
import com.practice.hotel.domain.Hotel;
import com.practice.hotel.service.CreateHotelCommand;
import com.practice.hotel.service.HotelSearchResult;
import com.practice.hotel.service.RequestContext;
import com.practice.hotel.service.UpdateHotelCommand;

public interface HotelMapper {

    CreateHotelCommand toCommand(CreateHotelRequest request, RequestContext context);

    UpdateHotelCommand toUpdateCommand(String hotelId, UpdateHotelRequest request, RequestContext context);

    HotelResponse toResponse(Hotel hotel);

    HotelSearchResponse toSearchResponse(List<HotelSearchResult> results);
}
