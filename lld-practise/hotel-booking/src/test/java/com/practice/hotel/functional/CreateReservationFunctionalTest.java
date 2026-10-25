package com.practice.hotel.functional;

import static com.practice.hotel.functional.HotelApiClient.GUEST_ID;
import static com.practice.hotel.functional.HotelApiClient.newKey;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.startsWith;
import static org.junit.jupiter.api.Named.named;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import java.util.stream.Stream;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.CreateReservationRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.ReservationResponse;
import com.practice.hotel.api.dto.RoomTypeRequest;

// Today is 2026-10-24 (TestClockConfig.NOW).
@SpringBootTest
@AutoConfigureMockMvc
@Import(TestClockConfig.class)
class CreateReservationFunctionalTest {

    private static final LocalDate NOV_10 = LocalDate.parse("2026-11-10");
    private static final LocalDate NOV_11 = LocalDate.parse("2026-11-11");
    private static final LocalDate NOV_12 = LocalDate.parse("2026-11-12");
    private static final LocalDate NOV_13 = LocalDate.parse("2026-11-13");

    @Autowired
    MockMvc mvc;

    @Autowired
    ObjectMapper objectMapper;

    HotelApiClient client;

    @BeforeEach
    void setUp() {
        client = new HotelApiClient(mvc, objectMapper);
    }

    @Test
    void createsReservation() throws Exception {
        HotelResponse hotel = createHotel("Reservation Test City", 10);
        String roomTypeId = hotel.roomTypes().get(0).id();

        MvcResult result = client.reserve(GUEST_ID, newKey(), hotel.id(),
                        new CreateReservationRequest(roomTypeId, NOV_10, NOV_13, 2))
                .andExpect(status().isCreated())
                .andReturn();
        ReservationResponse reservation = client.read(result, ReservationResponse.class);

        assertThat(reservation).usingRecursiveComparison().ignoringFields("id").isEqualTo(new ReservationResponse(
                null, hotel.id(), roomTypeId, GUEST_ID, NOV_10, NOV_13, 2, new BigDecimal("4500.00"),
                new BigDecimal("27000.00"), TestClockConfig.NOW));
        assertThat(UUID.fromString(reservation.id())).hasToString(reservation.id());
    }

    // checkOut 365 days after today: rows reach the last night a valid stay can include.
    @Test
    void reservesLastBookableNight() throws Exception {
        HotelResponse hotel = createHotel("Last Bookable Night Test City", 1);

        client.reserve(GUEST_ID, newKey(), hotel.id(), new CreateReservationRequest(
                        hotel.roomTypes().get(0).id(), LocalDate.parse("2027-10-23"), LocalDate.parse("2027-10-24"), 1))
                .andExpect(status().isCreated());
    }

    // The service never runs, so the hotel and room type ids don't need to exist.
    static Stream<Arguments> invalidBodies() {
        String roomTypeId = UUID.randomUUID().toString();
        return Stream.of(
                Arguments.of(named("missing roomTypeId", new CreateReservationRequest(null, NOV_10, NOV_13, 1)), "roomTypeId"),
                Arguments.of(named("missing checkIn", new CreateReservationRequest(roomTypeId, null, NOV_13, 1)), "checkIn"),
                Arguments.of(named("missing checkOut", new CreateReservationRequest(roomTypeId, NOV_10, null, 1)), "checkOut"),
                Arguments.of(named("rooms 0", new CreateReservationRequest(roomTypeId, NOV_10, NOV_13, 0)), "rooms"),
                // Valid JSON that no request record can hold, so the body is written as text.
                Arguments.of(named("checkIn \"10-11-2026\"", """
                        {"roomTypeId": "%s", "checkIn": "10-11-2026", "checkOut": "2026-11-13", "rooms": 1}
                        """.formatted(roomTypeId)), "checkIn"));
    }

    @ParameterizedTest
    @MethodSource("invalidBodies")
    void rejectsInvalidBody(Object body, String field) throws Exception {
        client.reserve(GUEST_ID, newKey(), UUID.randomUUID().toString(), body)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value(startsWith(field + " ")));
    }

    @Test
    void rejectsMissingGuestId() throws Exception {
        client.reserve(null, newKey(), UUID.randomUUID().toString(),
                        new CreateReservationRequest(UUID.randomUUID().toString(), NOV_10, NOV_13, 1))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("UNAUTHORIZED"));
    }

    @Test
    void rejectsUnknownHotel() throws Exception {
        client.reserve(GUEST_ID, newKey(), UUID.randomUUID().toString(),
                        new CreateReservationRequest(UUID.randomUUID().toString(), NOV_10, NOV_13, 1))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("HOTEL_NOT_FOUND"));
    }

    @Test
    void rejectsRoomTypeOfAnotherHotel() throws Exception {
        HotelResponse hotel = createHotel("Other Room Type Test City", 10);
        HotelResponse other = createHotel("Other Room Type Test City", 10);

        client.reserve(GUEST_ID, newKey(), hotel.id(),
                        new CreateReservationRequest(other.roomTypes().get(0).id(), NOV_10, NOV_13, 1))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("ROOM_TYPE_NOT_FOUND"));
    }

    @Test
    void rejectsInvalidStay() throws Exception {
        HotelResponse hotel = createHotel("Invalid Stay Test City", 10);

        client.reserve(GUEST_ID, newKey(), hotel.id(),
                        new CreateReservationRequest(hotel.roomTypes().get(0).id(), NOV_10, NOV_10, 1))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_STAY"));
    }

    @Test
    void rejectsWhenRoomsRunOut() throws Exception {
        HotelResponse hotel = createHotel("Rooms Run Out Test City", 2);
        String roomTypeId = hotel.roomTypes().get(0).id();
        reserve(newKey(), hotel.id(), new CreateReservationRequest(roomTypeId, NOV_10, NOV_12, 2));

        client.reserve(GUEST_ID, newKey(), hotel.id(), new CreateReservationRequest(roomTypeId, NOV_11, NOV_13, 1))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("ROOMS_NOT_AVAILABLE"));
    }

    @Test
    void replaysSameKey() throws Exception {
        HotelResponse hotel = createHotel("Replay Reservation Test City", 2);
        CreateReservationRequest oneRoom = new CreateReservationRequest(hotel.roomTypes().get(0).id(), NOV_10, NOV_13, 1);
        String key = newKey();

        ReservationResponse first = reserve(key, hotel.id(), oneRoom);
        ReservationResponse second = reserve(key, hotel.id(), oneRoom);
        // The replay reserved nothing, so the second room is still free.
        reserve(newKey(), hotel.id(), oneRoom);

        assertThat(second.id()).isEqualTo(first.id());
    }

    private HotelResponse createHotel(String city, int rooms) throws Exception {
        return client.createHotel(newKey(), new CreateHotelRequest("Taj", city, null, List.of(
                new RoomTypeRequest("Sea View Deluxe", "King bed, balcony facing the sea", rooms, new BigDecimal("4500.00")))));
    }

    private ReservationResponse reserve(String key, String hotelId, CreateReservationRequest request) throws Exception {
        MvcResult result = client.reserve(GUEST_ID, key, hotelId, request).andExpect(status().isCreated()).andReturn();
        return client.read(result, ReservationResponse.class);
    }
}
