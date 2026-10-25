package com.practice.hotel.api.dto;

import java.util.List;

// The list sits inside an object so pagination (e.g. nextCursor) can be added later without breaking clients.
public record HotelSearchResponse(List<HotelSummaryResponse> hotels) {
}
