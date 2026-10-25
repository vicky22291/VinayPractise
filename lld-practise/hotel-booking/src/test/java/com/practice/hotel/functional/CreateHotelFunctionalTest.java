package com.practice.hotel.functional;

import static com.practice.hotel.functional.HotelApiClient.ADMIN_ID;
import static com.practice.hotel.functional.HotelApiClient.newKey;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Named.named;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;
import java.util.stream.Stream;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.HttpHeaders;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.RoomTypeRequest;
import com.practice.hotel.api.dto.RoomTypeResponse;

@SpringBootTest
@AutoConfigureMockMvc
@Import(TestClockConfig.class)
class CreateHotelFunctionalTest {

    private static final String DETAILS = "Sea-facing heritage hotel with a pool";
    private static final RoomTypeRequest SEA_VIEW =
            new RoomTypeRequest("Sea View Deluxe", "King bed, balcony facing the sea", 10, new BigDecimal("4500.00"));
    private static final RoomTypeRequest FAMILY_SUITE =
            new RoomTypeRequest("Family Suite", "Two bedrooms, sleeps 4", 2, new BigDecimal("12000.00"));

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
    void createsHotel() throws Exception {
        MvcResult result = client.create(ADMIN_ID, newKey(), taj("Create Test City"))
                .andExpect(status().isCreated())
                .andReturn();
        HotelResponse hotel = client.read(result, HotelResponse.class);

        assertThat(result.getResponse().getHeader(HttpHeaders.LOCATION)).isEqualTo("/api/v1/hotels/" + hotel.id());
        assertThat(hotel).usingRecursiveComparison().ignoringFields("id", "roomTypes.id").isEqualTo(new HotelResponse(
                null, "Taj", "Create Test City", DETAILS, TestClockConfig.NOW, TestClockConfig.NOW, List.of(
                        new RoomTypeResponse(null, SEA_VIEW.name(), SEA_VIEW.description(), 10, new BigDecimal("4500.00")),
                        new RoomTypeResponse(null, FAMILY_SUITE.name(), FAMILY_SUITE.description(), 2, new BigDecimal("12000.00")))));
        assertThat(Stream.concat(Stream.of(hotel.id()), hotel.roomTypes().stream().map(RoomTypeResponse::id)))
                .doesNotHaveDuplicates()
                .allSatisfy(id -> assertThat(UUID.fromString(id)).hasToString(id));
    }

    static Stream<Arguments> invalidBodies() {
        String city = "Invalid Body Test City";
        return Stream.of(
                Arguments.of(named("blank name", new CreateHotelRequest(" ", city, null, List.of(SEA_VIEW))), "VALIDATION_FAILED"),
                Arguments.of(named("blank city", new CreateHotelRequest("Taj", " ", null, List.of(SEA_VIEW))), "VALIDATION_FAILED"),
                Arguments.of(named("empty roomTypes", new CreateHotelRequest("Taj", city, null, List.of())), "VALIDATION_FAILED"),
                Arguments.of(named("blank room type name", withRoomType(city, new RoomTypeRequest(" ", "King bed", 10, BigDecimal.TEN))),
                        "VALIDATION_FAILED"),
                Arguments.of(named("blank description", withRoomType(city, new RoomTypeRequest("Deluxe", " ", 10, BigDecimal.TEN))),
                        "VALIDATION_FAILED"),
                Arguments.of(named("count -1", withRoomType(city, new RoomTypeRequest("Deluxe", "King bed", -1, BigDecimal.TEN))),
                        "VALIDATION_FAILED"),
                Arguments.of(named("pricePerNight 0", withRoomType(city, new RoomTypeRequest("Deluxe", "King bed", 10, BigDecimal.ZERO))),
                        "VALIDATION_FAILED"),
                Arguments.of(named("body that isn't JSON", "{\"name\": \"Taj\","), "MALFORMED_REQUEST"));
    }

    @ParameterizedTest
    @MethodSource("invalidBodies")
    void rejectsInvalidBody(Object body, String code) throws Exception {
        client.create(ADMIN_ID, newKey(), body)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value(code));
    }

    // Valid JSON that no request record can hold, so the body is written as text.
    @ParameterizedTest
    @ValueSource(strings = {"2.9", "\"ten\""})
    void rejectsValueOfWrongType(String count) throws Exception {
        String body = """
                {"name": "Taj", "city": "Wrong Type Test City", "roomTypes": [
                  {"name": "Deluxe", "description": "King bed", "count": %s, "pricePerNight": 10}]}
                """.formatted(count);

        client.create(ADMIN_ID, newKey(), body)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value("roomTypes[0].count has an invalid value"));
    }

    static Stream<Arguments> badHeaders() {
        return Stream.of(
                Arguments.of(named("missing X-Admin-Id", null), newKey(), 401, "UNAUTHORIZED"),
                Arguments.of(named("blank X-Admin-Id", " "), newKey(), 401, "UNAUTHORIZED"),
                Arguments.of(ADMIN_ID, named("missing Idempotency-Key", null), 400, "IDEMPOTENCY_KEY_INVALID"),
                Arguments.of(ADMIN_ID, named("blank Idempotency-Key", " "), 400, "IDEMPOTENCY_KEY_INVALID"),
                Arguments.of(ADMIN_ID, named("256-character Idempotency-Key", (newKey() + "x".repeat(256)).substring(0, 256)),
                        400, "IDEMPOTENCY_KEY_INVALID"));
    }

    @ParameterizedTest
    @MethodSource("badHeaders")
    void rejectsBadHeaders(String adminId, String idempotencyKey, int status, String code) throws Exception {
        client.create(adminId, idempotencyKey, taj("Bad Headers Test City"))
                .andExpect(status().is(status))
                .andExpect(jsonPath("$.code").value(code));
    }

    @Test
    void rejectsDuplicateRoomTypeNames() throws Exception {
        CreateHotelRequest request = new CreateHotelRequest("Taj", "Duplicate Test City", null,
                List.of(SEA_VIEW, new RoomTypeRequest("sea view deluxe", "Same name, other case", 1, BigDecimal.TEN)));

        client.create(ADMIN_ID, newKey(), request)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("DUPLICATE_ROOM_TYPE"));
    }

    @Test
    void replaysSameKey() throws Exception {
        String key = newKey();
        CreateHotelRequest request = taj("Replay Test City");

        HotelResponse first = client.createHotel(key, request);
        HotelResponse second = client.createHotel(key, request);

        assertThat(second.id()).isEqualTo(first.id());
    }

    @Test
    void rejectsReusedKey() throws Exception {
        String key = newKey();
        client.createHotel(key, taj("Reused Key Test City"));

        client.create(ADMIN_ID, key, taj("Other Reused Key Test City"))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.code").value("IDEMPOTENCY_KEY_REUSED"));
    }

    private static CreateHotelRequest taj(String city) {
        return new CreateHotelRequest("Taj", city, DETAILS, List.of(SEA_VIEW, FAMILY_SUITE));
    }

    private static CreateHotelRequest withRoomType(String city, RoomTypeRequest roomType) {
        return new CreateHotelRequest("Taj", city, null, List.of(roomType));
    }
}
