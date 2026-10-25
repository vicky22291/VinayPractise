package com.practice.hotel.functional;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.io.IOException;
import java.util.UUID;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.HotelResponse;

// Builds the hotel API requests for functional tests. A null header or query parameter is left out; a String body is
// sent as is.
public class HotelApiClient {

    public static final String ADMIN_ID = "admin-1";
    public static final String GUEST_ID = "guest-1";

    private static final String HOTELS = "/api/v1/hotels";

    private final MockMvc mvc;
    private final ObjectMapper objectMapper;

    public HotelApiClient(MockMvc mvc, ObjectMapper objectMapper) {
        this.mvc = mvc;
        this.objectMapper = objectMapper;
    }

    public static String newKey() {
        return UUID.randomUUID().toString();
    }

    public ResultActions create(String adminId, String idempotencyKey, Object body) throws Exception {
        return mvc.perform(withWriteHeaders(post(HOTELS), "X-Admin-Id", adminId, idempotencyKey)
                .contentType(MediaType.APPLICATION_JSON)
                .content(json(body)));
    }

    public HotelResponse createHotel(String idempotencyKey, CreateHotelRequest request) throws Exception {
        MvcResult result = create(ADMIN_ID, idempotencyKey, request).andExpect(status().isCreated()).andReturn();
        return read(result, HotelResponse.class);
    }

    public ResultActions get(String hotelId) throws Exception {
        return mvc.perform(MockMvcRequestBuilders.get(HOTELS + "/{hotelId}", hotelId));
    }

    public ResultActions search(String city) throws Exception {
        return search(city, null, null, null);
    }

    // Each value goes into the query string encoded, so a city of "  " is sent as city=%20%20.
    public ResultActions search(String city, String checkIn, String checkOut, String rooms) throws Exception {
        MockHttpServletRequestBuilder request = MockMvcRequestBuilders.get(HOTELS);
        addQueryParam(request, "city", city);
        addQueryParam(request, "checkIn", checkIn);
        addQueryParam(request, "checkOut", checkOut);
        addQueryParam(request, "rooms", rooms);
        return mvc.perform(request);
    }

    public ResultActions update(String adminId, String idempotencyKey, String hotelId, Object body) throws Exception {
        return mvc.perform(withWriteHeaders(patch(HOTELS + "/{hotelId}", hotelId), "X-Admin-Id", adminId, idempotencyKey)
                .contentType(MediaType.APPLICATION_JSON)
                .content(json(body)));
    }

    public ResultActions reserve(String guestId, String idempotencyKey, String hotelId, Object body) throws Exception {
        MockHttpServletRequestBuilder request = post(HOTELS + "/{hotelId}/reservations", hotelId);
        return mvc.perform(withWriteHeaders(request, "X-Guest-Id", guestId, idempotencyKey)
                .contentType(MediaType.APPLICATION_JSON)
                .content(json(body)));
    }

    public <T> T read(MvcResult result, Class<T> type) throws IOException {
        return objectMapper.readValue(result.getResponse().getContentAsByteArray(), type);
    }

    // actorHeader is X-Admin-Id for hotel writes and X-Guest-Id for reservations.
    private static MockHttpServletRequestBuilder withWriteHeaders(
            MockHttpServletRequestBuilder request, String actorHeader, String actorId, String idempotencyKey) {
        if (actorId != null) {
            request.header(actorHeader, actorId);
        }
        if (idempotencyKey != null) {
            request.header("Idempotency-Key", idempotencyKey);
        }
        return request;
    }

    private String json(Object body) throws JsonProcessingException {
        return body instanceof String raw ? raw : objectMapper.writeValueAsString(body);
    }

    private static void addQueryParam(MockHttpServletRequestBuilder request, String name, String value) {
        if (value != null) {
            request.queryParam(name, value);
        }
    }
}
