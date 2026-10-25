package com.practice.hotel.functional;

import static com.practice.hotel.functional.HotelApiClient.ADMIN_ID;
import static com.practice.hotel.functional.HotelApiClient.newKey;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.entry;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.ResultActions;

import com.practice.hotel.api.dto.AvailableRoomTypeResponse;
import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.CreateReservationRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.HotelSearchResponse;
import com.practice.hotel.api.dto.HotelSummaryResponse;
import com.practice.hotel.api.dto.ReservationResponse;
import com.practice.hotel.api.dto.RoomTypeChangeRequest;
import com.practice.hotel.api.dto.RoomTypeRequest;
import com.practice.hotel.api.dto.RoomTypeResponse;
import com.practice.hotel.api.dto.UpdateHotelRequest;

// Flows across the APIs, as an owner and guests use them. Today is 2026-10-24 (TestClockConfig.NOW).
@SpringBootTest
@AutoConfigureMockMvc
@Import(TestClockConfig.class)
class UserStoriesFunctionalTest {

    private static final LocalDate NOV_10 = LocalDate.parse("2026-11-10");
    private static final LocalDate NOV_11 = LocalDate.parse("2026-11-11");
    private static final LocalDate NOV_12 = LocalDate.parse("2026-11-12");
    private static final LocalDate NOV_13 = LocalDate.parse("2026-11-13");
    private static final LocalDate NOV_14 = LocalDate.parse("2026-11-14");

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
    void guestsBookUntilSoldOut() throws Exception {
        String city = uniqueCity();
        HotelResponse hotel = createHotel(city, deluxe(2));
        String deluxeId = roomTypeId(hotel, "Deluxe");

        assertThat(availability(city, NOV_10, NOV_12)).containsExactly(entry("Deluxe", 2));
        book("guest-1", hotel, deluxeId, NOV_10, NOV_12).andExpect(status().isCreated());
        assertThat(availability(city, NOV_10, NOV_12)).containsExactly(entry("Deluxe", 1));
        book("guest-2", hotel, deluxeId, NOV_10, NOV_12).andExpect(status().isCreated());
        assertThat(availability(city, NOV_10, NOV_12)).isEmpty();
        book("guest-3", hotel, deluxeId, NOV_10, NOV_12)
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("ROOMS_NOT_AVAILABLE"));

        assertThat(searchWithoutDates(city)).extracting(HotelSummaryResponse::id).containsExactly(hotel.id());
        assertThat(get(hotel).roomTypes()).extracting(RoomTypeResponse::count).containsExactly(2);
    }

    @Test
    void backToBackStaysShareCheckoutDate() throws Exception {
        String city = uniqueCity();
        HotelResponse hotel = createHotel(city, deluxe(1));
        String deluxeId = roomTypeId(hotel, "Deluxe");
        book("guest-1", hotel, deluxeId, NOV_10, NOV_12).andExpect(status().isCreated());

        assertThat(availability(city, NOV_11, NOV_13)).isEmpty();
        assertThat(availability(city, NOV_12, NOV_14)).containsExactly(entry("Deluxe", 1));
        book("guest-2", hotel, deluxeId, NOV_12, NOV_14).andExpect(status().isCreated());
        book("guest-3", hotel, deluxeId, NOV_11, NOV_12).andExpect(status().isConflict());
    }

    @Test
    void ownerAddsRoomsToSoldOutRoomType() throws Exception {
        String city = uniqueCity();
        HotelResponse hotel = createHotel(city, deluxe(1));
        String deluxeId = roomTypeId(hotel, "Deluxe");
        book("guest-1", hotel, deluxeId, NOV_10, NOV_12).andExpect(status().isCreated());

        update(hotel, changeCount(deluxeId, 2)).andExpect(status().isOk());
        assertThat(availability(city, NOV_10, NOV_12)).containsExactly(entry("Deluxe", 1));
        book("guest-2", hotel, deluxeId, NOV_10, NOV_12).andExpect(status().isCreated());

        update(hotel, changeCount(deluxeId, 1))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("ROOM_COUNT_BELOW_RESERVED"));
        assertThat(get(hotel).roomTypes()).extracting(RoomTypeResponse::count).containsExactly(2);
        assertThat(availability(city, NOV_10, NOV_12)).isEmpty();
    }

    @Test
    void ownerAddsRoomTypeToSoldOutHotel() throws Exception {
        String city = uniqueCity();
        HotelResponse hotel = createHotel(city, deluxe(1));
        book("guest-1", hotel, roomTypeId(hotel, "Deluxe"), NOV_10, NOV_12).andExpect(status().isCreated());

        RoomTypeChangeRequest suite = new RoomTypeChangeRequest(null, "Suite", "Two bedrooms", 1, new BigDecimal("9000.00"));
        HotelResponse updated = read(update(hotel, new UpdateHotelRequest(null, null, null, List.of(suite)))
                .andExpect(status().isOk()), HotelResponse.class);
        assertThat(availability(city, NOV_10, NOV_12)).containsExactly(entry("Suite", 1));

        ReservationResponse reservation = read(book("guest-2", hotel, roomTypeId(updated, "Suite"), NOV_10, NOV_12)
                .andExpect(status().isCreated()), ReservationResponse.class);
        assertThat(reservation.pricePerNight()).isEqualTo(new BigDecimal("9000.00"));
        assertThat(availability(city, NOV_10, NOV_12)).isEmpty();
    }

    @Test
    void searchAndBookingFollowHotelEdits() throws Exception {
        String oldCity = uniqueCity();
        String newCity = uniqueCity();
        HotelResponse hotel = createHotel(oldCity, deluxe(2));
        String deluxeId = roomTypeId(hotel, "Deluxe");
        ReservationResponse first = read(book("guest-1", hotel, deluxeId, NOV_10, NOV_12)
                .andExpect(status().isCreated()), ReservationResponse.class);

        RoomTypeChangeRequest newPrice = new RoomTypeChangeRequest(deluxeId, null, null, null, new BigDecimal("5000.00"));
        update(hotel, new UpdateHotelRequest(null, newCity, null, List.of(newPrice))).andExpect(status().isOk());
        assertThat(searchWithoutDates(oldCity)).isEmpty();
        assertThat(availability(newCity, NOV_10, NOV_12)).containsExactly(entry("Deluxe", 1));

        ReservationResponse second = read(book("guest-2", hotel, deluxeId, NOV_10, NOV_12)
                .andExpect(status().isCreated()), ReservationResponse.class);
        assertThat(first.pricePerNight()).isEqualTo(new BigDecimal("4500.00"));
        assertThat(second.pricePerNight()).isEqualTo(new BigDecimal("5000.00"));
        assertThat(second.totalPrice()).isEqualTo(new BigDecimal("10000.00"));
    }

    private HotelResponse createHotel(String city, RoomTypeRequest roomType) throws Exception {
        return client.createHotel(newKey(), new CreateHotelRequest("Harbour Inn", city, null, List.of(roomType)));
    }

    private HotelResponse get(HotelResponse hotel) throws Exception {
        return read(client.get(hotel.id()).andExpect(status().isOk()), HotelResponse.class);
    }

    private ResultActions update(HotelResponse hotel, UpdateHotelRequest request) throws Exception {
        return client.update(ADMIN_ID, newKey(), hotel.id(), request);
    }

    // Always 1 room.
    private ResultActions book(String guestId, HotelResponse hotel, String roomTypeId, LocalDate checkIn,
            LocalDate checkOut) throws Exception {
        return client.reserve(guestId, newKey(), hotel.id(),
                new CreateReservationRequest(roomTypeId, checkIn, checkOut, 1));
    }

    private List<HotelSummaryResponse> searchWithoutDates(String city) throws Exception {
        return read(client.search(city).andExpect(status().isOk()), HotelSearchResponse.class).hotels();
    }

    // Room type name to rooms available for the stay, over every hotel the search lists. Empty when none are listed.
    private Map<String, Integer> availability(String city, LocalDate checkIn, LocalDate checkOut) throws Exception {
        MvcResult result = client.search(city, checkIn.toString(), checkOut.toString(), null)
                .andExpect(status().isOk())
                .andReturn();
        Map<String, Integer> available = new LinkedHashMap<>();
        for (HotelSummaryResponse hotel : client.read(result, HotelSearchResponse.class).hotels()) {
            for (AvailableRoomTypeResponse roomType : hotel.availableRoomTypes()) {
                available.put(roomType.name(), roomType.available());
            }
        }
        return available;
    }

    private <T> T read(ResultActions actions, Class<T> type) throws Exception {
        return client.read(actions.andReturn(), type);
    }

    private static RoomTypeRequest deluxe(int count) {
        return new RoomTypeRequest("Deluxe", "King bed", count, new BigDecimal("4500.00"));
    }

    private static UpdateHotelRequest changeCount(String roomTypeId, int count) {
        return new UpdateHotelRequest(null, null, null, List.of(new RoomTypeChangeRequest(roomTypeId, null, null, count, null)));
    }

    private static String roomTypeId(HotelResponse hotel, String name) {
        return hotel.roomTypes().stream().filter(roomType -> roomType.name().equals(name)).findFirst().orElseThrow().id();
    }

    // The shared context keeps every hotel the other functional tests create, so each story gets its own city.
    private static String uniqueCity() {
        return "Story City " + UUID.randomUUID();
    }
}
