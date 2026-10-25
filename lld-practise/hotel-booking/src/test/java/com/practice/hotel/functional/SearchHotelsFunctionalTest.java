package com.practice.hotel.functional;

import static com.practice.hotel.functional.HotelApiClient.GUEST_ID;
import static com.practice.hotel.functional.HotelApiClient.newKey;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Named.named;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.function.Function;
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

import com.practice.hotel.api.dto.AvailableRoomTypeResponse;
import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.CreateReservationRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.HotelSearchResponse;
import com.practice.hotel.api.dto.HotelSummaryResponse;
import com.practice.hotel.api.dto.RoomTypeRequest;
import com.practice.hotel.api.dto.RoomTypeResponse;

@SpringBootTest
@AutoConfigureMockMvc
@Import(TestClockConfig.class)
class SearchHotelsFunctionalTest {

    private static final RoomTypeRequest SEA_VIEW =
            new RoomTypeRequest("Sea View Deluxe", "King bed, balcony facing the sea", 10, new BigDecimal("4500.00"));
    private static final RoomTypeRequest DELUXE = new RoomTypeRequest("Deluxe", "King bed", 2, new BigDecimal("4500.00"));
    private static final RoomTypeRequest SUITE = new RoomTypeRequest("Suite", "Two bedrooms", 1, new BigDecimal("12000.00"));
    private static final RoomTypeRequest SINGLE = new RoomTypeRequest("Single", "One single bed", 1, new BigDecimal("2000.00"));

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
    void findsHotelsInCity() throws Exception {
        String city = uniqueCity("Search Test City");
        HotelResponse taj = createHotel("Taj", city, "Sea-facing heritage hotel with a pool");
        HotelResponse harbourInn = createHotel("Harbour Inn", city, null);
        createHotel("Taj", uniqueCity("Other Search Test City"), null);

        MvcResult result = client.search("  " + city.toUpperCase(Locale.ROOT) + " ")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.hotels[*].roomTypes").doesNotExist())
                .andExpect(jsonPath("$.hotels[*].availableRoomTypes").doesNotExist())
                .andReturn();

        assertThat(client.read(result, HotelSearchResponse.class).hotels())
                .containsExactlyInAnyOrder(summary(taj), summary(harbourInn));
    }

    @Test
    void returnsEmptyListForUnknownCity() throws Exception {
        MvcResult result = client.search(uniqueCity("Unknown Search Test City"))
                .andExpect(status().isOk())
                .andReturn();

        assertThat(client.read(result, HotelSearchResponse.class)).isEqualTo(new HotelSearchResponse(List.of()));
    }

    static Stream<Arguments> missingOrBlankCities() {
        return Stream.of(
                Arguments.of(named("no city", null)),
                Arguments.of(named("city=", "")),
                Arguments.of(named("city=%20%20", "  ")));
    }

    @ParameterizedTest
    @MethodSource("missingOrBlankCities")
    void rejectsMissingOrBlankCity(String city) throws Exception {
        client.search(city)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"));
    }

    static Stream<Arguments> roomsToFit() {
        return Stream.of(
                fit(1, "only A, with only Deluxe", hotelA -> {
                    RoomTypeResponse deluxe = hotelA.roomTypes().get(0);
                    return List.of(summary(hotelA, List.of(
                            new AvailableRoomTypeResponse(deluxe.id(), deluxe.name(), deluxe.pricePerNight(), 1))));
                }),
                fit(2, "no hotel", hotelA -> List.of()));
    }

    @ParameterizedTest
    @MethodSource("roomsToFit")
    void listsRoomTypesThatFit(int rooms, Function<HotelResponse, List<HotelSummaryResponse>> expected) throws Exception {
        String city = uniqueCity("Availability Test City");
        HotelResponse hotelA = client.createHotel(newKey(),
                new CreateHotelRequest("Hotel A", city, null, List.of(DELUXE, SUITE)));
        HotelResponse hotelB = client.createHotel(newKey(),
                new CreateHotelRequest("Hotel B", city, null, List.of(SINGLE)));
        // The Deluxe and Single bookings cover one night each, so the worst night decides.
        reserve(hotelA.id(), hotelA.roomTypes().get(1).id(), "2026-11-10", "2026-11-13");
        reserve(hotelA.id(), hotelA.roomTypes().get(0).id(), "2026-11-12", "2026-11-13");
        reserve(hotelB.id(), hotelB.roomTypes().get(0).id(), "2026-11-11", "2026-11-12");

        MvcResult result = client.search(city, "2026-11-10", "2026-11-13", String.valueOf(rooms))
                .andExpect(status().isOk())
                .andReturn();

        assertThat(client.read(result, HotelSearchResponse.class).hotels()).isEqualTo(expected.apply(hotelA));
    }

    static Stream<Arguments> invalidAvailabilityQueries() {
        return Stream.of(
                Arguments.of(named("only checkIn", "2026-11-10"), null, null, "INVALID_STAY"),
                Arguments.of(named("checkIn=2026-13-01", "2026-13-01"), "2026-11-13", null, "VALIDATION_FAILED"),
                Arguments.of("2026-11-10", "2026-11-13", named("rooms=0", "0"), "VALIDATION_FAILED"));
    }

    @ParameterizedTest
    @MethodSource("invalidAvailabilityQueries")
    void rejectsInvalidAvailabilityQuery(String checkIn, String checkOut, String rooms, String code) throws Exception {
        client.search("Invalid Availability Test City", checkIn, checkOut, rooms)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(code));
    }

    private HotelResponse createHotel(String name, String city, String details) throws Exception {
        return client.createHotel(newKey(), new CreateHotelRequest(name, city, details, List.of(SEA_VIEW)));
    }

    // Books 1 room through the reservation API, so search reads the inventory that real bookings fill.
    private void reserve(String hotelId, String roomTypeId, String checkIn, String checkOut) throws Exception {
        client.reserve(GUEST_ID, newKey(), hotelId,
                        new CreateReservationRequest(roomTypeId, LocalDate.parse(checkIn), LocalDate.parse(checkOut), 1))
                .andExpect(status().isCreated());
    }

    // The shared context keeps every hotel the other functional tests create, so each test gets its own city.
    private static String uniqueCity(String prefix) {
        return prefix + " " + UUID.randomUUID();
    }

    private static HotelSummaryResponse summary(HotelResponse hotel) {
        return summary(hotel, null);
    }

    private static HotelSummaryResponse summary(HotelResponse hotel, List<AvailableRoomTypeResponse> availableRoomTypes) {
        return new HotelSummaryResponse(hotel.id(), hotel.name(), hotel.city(), hotel.details(), availableRoomTypes);
    }

    private static Arguments fit(int rooms, String name, Function<HotelResponse, List<HotelSummaryResponse>> expected) {
        return Arguments.of(rooms, named(name, expected));
    }
}
