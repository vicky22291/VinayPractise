package com.practice.hotel.service;

import java.util.List;

import com.practice.hotel.domain.Hotel;

public interface HotelService {

    Hotel create(CreateHotelCommand command);

    Hotel get(String hotelId);

    List<HotelSearchResult> search(HotelSearchQuery query);

    Hotel update(UpdateHotelCommand command);
}
