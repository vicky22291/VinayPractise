package com.practice.hotel.api;

import java.net.URI;
import java.time.Instant;
import java.time.LocalDate;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.format.annotation.DateTimeFormat.ISO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.HotelSearchResponse;
import com.practice.hotel.api.dto.UpdateHotelRequest;
import com.practice.hotel.domain.Hotel;
import com.practice.hotel.mapper.HotelMapper;
import com.practice.hotel.service.HotelSearchQuery;
import com.practice.hotel.service.HotelService;
import com.practice.hotel.service.RequestContext;

@RestController
@RequestMapping("/api/v1/hotels")
public class HotelController {

    private final HotelService hotelService;
    private final HotelMapper hotelMapper;
    private final RequestContextFactory requestContextFactory;

    public HotelController(HotelService hotelService, HotelMapper hotelMapper,
            RequestContextFactory requestContextFactory) {
        this.hotelService = hotelService;
        this.hotelMapper = hotelMapper;
        this.requestContextFactory = requestContextFactory;
    }

    @PostMapping
    public ResponseEntity<HotelResponse> create(
            @RequestAttribute(RequestTimeFilter.REQUEST_TIME_ATTRIBUTE) Instant requestTime,
            @RequestHeader("X-Admin-Id") String adminId,
            @RequestHeader("Idempotency-Key") String idempotencyKey,
            @Valid @RequestBody CreateHotelRequest request,
            HttpServletRequest httpRequest) {
        String path = httpRequest.getRequestURI();
        RequestContext context = requestContextFactory.create(adminId, requestTime, idempotencyKey, path, request);
        Hotel hotel = hotelService.create(hotelMapper.toCommand(request, context));
        return ResponseEntity.created(URI.create(path + "/" + hotel.id())).body(hotelMapper.toResponse(hotel));
    }

    @GetMapping("/{hotelId}")
    public HotelResponse get(@PathVariable String hotelId) {
        return hotelMapper.toResponse(hotelService.get(hotelId));
    }

    // required = false lets a missing city reach @NotBlank, so missing and blank both fail Spring's built-in method
    // validation with HandlerMethodValidationException. @Validated on the class would switch to a different exception.
    // ISO.DATE keeps date parsing free of locale defaults, and an empty value such as checkIn= counts as not sent.
    @GetMapping
    public HotelSearchResponse search(
            @RequestAttribute(RequestTimeFilter.REQUEST_TIME_ATTRIBUTE) Instant requestTime,
            @RequestParam(required = false) @NotBlank String city,
            @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE) LocalDate checkIn,
            @RequestParam(required = false) @DateTimeFormat(iso = ISO.DATE) LocalDate checkOut,
            @RequestParam(defaultValue = "1") @Positive int rooms) {
        HotelSearchQuery query = new HotelSearchQuery(city, checkIn, checkOut, rooms, requestTime);
        return hotelMapper.toSearchResponse(hotelService.search(query));
    }

    @PatchMapping("/{hotelId}")
    public HotelResponse update(
            @RequestAttribute(RequestTimeFilter.REQUEST_TIME_ATTRIBUTE) Instant requestTime,
            @RequestHeader("X-Admin-Id") String adminId,
            @RequestHeader("Idempotency-Key") String idempotencyKey,
            @PathVariable String hotelId,
            @Valid @RequestBody UpdateHotelRequest request,
            HttpServletRequest httpRequest) {
        RequestContext context = requestContextFactory.create(
                adminId, requestTime, idempotencyKey, httpRequest.getRequestURI(), request);
        return hotelMapper.toResponse(hotelService.update(hotelMapper.toUpdateCommand(hotelId, request, context)));
    }
}
