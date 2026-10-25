package com.practice.hotel.functional;

import static com.practice.hotel.functional.HotelApiClient.ADMIN_ID;
import static com.practice.hotel.functional.HotelApiClient.GUEST_ID;
import static com.practice.hotel.functional.HotelApiClient.newKey;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Named.named;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
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

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.CreateReservationRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.RoomTypeChangeRequest;
import com.practice.hotel.api.dto.RoomTypeRequest;
import com.practice.hotel.api.dto.RoomTypeResponse;
import com.practice.hotel.api.dto.UpdateHotelRequest;

@SpringBootTest
@AutoConfigureMockMvc
@Import(TestClockConfig.class)
class UpdateHotelFunctionalTest {

    private static final RoomTypeRequest SEA_VIEW =
            new RoomTypeRequest("Sea View Deluxe", "King bed, balcony facing the sea", 10, new BigDecimal("4500.00"));
    private static final RoomTypeRequest FAMILY_SUITE =
            new RoomTypeRequest("Family Suite", "Two bedrooms, sleeps 4", 2, new BigDecimal("12000.00"));
    private static final RoomTypeChangeRequest GARDEN_TWIN =
            new RoomTypeChangeRequest(null, "Garden Twin", "Two single beds, garden view", 6, new BigDecimal("3200.00"));

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
    void updatesHotelFields() throws Exception {
        HotelResponse created = createTaj("Update Fields Test City");

        HotelResponse updated = updateHotel(newKey(), created.id(), new UpdateHotelRequest("Taj Palace", null, "", null));

        assertThat(updated).isEqualTo(new HotelResponse(created.id(), "Taj Palace", created.city(), "",
                created.createdAt(), TestClockConfig.NOW, created.roomTypes()));
    }

    @Test
    void addsAndChangesRoomTypes() throws Exception {
        HotelResponse created = createTaj("Update Room Types Test City");
        RoomTypeResponse seaView = created.roomTypes().get(0);
        RoomTypeResponse familySuite = created.roomTypes().get(1);

        HotelResponse updated = updateHotel(newKey(), created.id(), roomTypes(
                new RoomTypeChangeRequest(seaView.id(), null, null, 8, new BigDecimal("3500.00")), GARDEN_TWIN));

        assertThat(updated.roomTypes()).hasSize(3);
        assertThat(updated.roomTypes().subList(0, 2)).containsExactly(
                new RoomTypeResponse(seaView.id(), seaView.name(), seaView.description(), 8, new BigDecimal("3500.00")),
                familySuite);
        RoomTypeResponse gardenTwin = updated.roomTypes().get(2);
        assertThat(gardenTwin).usingRecursiveComparison().ignoringFields("id").isEqualTo(new RoomTypeResponse(
                null, GARDEN_TWIN.name(), GARDEN_TWIN.description(), 6, new BigDecimal("3200.00")));
        assertThat(UUID.fromString(gardenTwin.id())).hasToString(gardenTwin.id());
        assertThat(updated.roomTypes()).extracting(RoomTypeResponse::id).doesNotHaveDuplicates();
    }

    @Test
    void rejectsNonOwner() throws Exception {
        HotelResponse hotel = createTaj("Non Owner Test City");

        client.update("admin-2", newKey(), hotel.id(), new UpdateHotelRequest("Taj Palace", null, null, null))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value("NOT_HOTEL_OWNER"));
    }

    @Test
    void rejectsUnknownHotel() throws Exception {
        client.update(ADMIN_ID, newKey(), UUID.randomUUID().toString(), new UpdateHotelRequest("Taj Palace", null, null, null))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("HOTEL_NOT_FOUND"));
    }

    @Test
    void rejectsUnknownRoomType() throws Exception {
        HotelResponse hotel = createTaj("Unknown Room Type Test City");

        client.update(ADMIN_ID, newKey(), hotel.id(),
                        roomTypes(new RoomTypeChangeRequest(UUID.randomUUID().toString(), null, null, 1, null)))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("ROOM_TYPE_NOT_FOUND"));
    }

    static Stream<Arguments> invalidBodies() {
        return Stream.of(
                Arguments.of(named("empty body", "{}")),
                Arguments.of(named("empty roomTypes", "{\"roomTypes\": []}")),
                Arguments.of(named("room type change with only an id",
                        roomTypes(new RoomTypeChangeRequest(UUID.randomUUID().toString(), null, null, null, null)))),
                Arguments.of(named("blank name", new UpdateHotelRequest(" ", null, null, null))),
                Arguments.of(named("new room type without pricePerNight",
                        roomTypes(new RoomTypeChangeRequest(null, "Garden Twin", "Two single beds", 6, null)))),
                Arguments.of(named("count -1",
                        roomTypes(new RoomTypeChangeRequest(null, "Garden Twin", "Two single beds", -1, BigDecimal.TEN)))),
                Arguments.of(named("pricePerNight 0",
                        roomTypes(new RoomTypeChangeRequest(null, "Garden Twin", "Two single beds", 6, BigDecimal.ZERO)))));
    }

    @ParameterizedTest
    @MethodSource("invalidBodies")
    void rejectsInvalidBody(Object body) throws Exception {
        HotelResponse hotel = createTaj("Invalid Update Test City");

        client.update(ADMIN_ID, newKey(), hotel.id(), body)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"));
    }

    static Stream<Arguments> duplicateNameChanges() {
        return Stream.of(
                change("add a name that exists in another case", hotel -> roomTypes(
                        new RoomTypeChangeRequest(null, "sea view deluxe", "Same name, other case", 1, BigDecimal.TEN))),
                change("rename to an existing name", hotel -> roomTypes(
                        new RoomTypeChangeRequest(hotel.roomTypes().get(1).id(), "Sea View Deluxe", null, null, null))));
    }

    @ParameterizedTest
    @MethodSource("duplicateNameChanges")
    void rejectsDuplicateRoomTypeName(Function<HotelResponse, UpdateHotelRequest> change) throws Exception {
        HotelResponse hotel = createTaj("Duplicate Update Test City");

        client.update(ADMIN_ID, newKey(), hotel.id(), change.apply(hotel))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("DUPLICATE_ROOM_TYPE"));
    }

    @Test
    void replaysSameKey() throws Exception {
        HotelResponse hotel = createTaj("Replay Update Test City");
        String key = newKey();

        HotelResponse first = updateHotel(key, hotel.id(), roomTypes(GARDEN_TWIN));
        HotelResponse second = updateHotel(key, hotel.id(), roomTypes(GARDEN_TWIN));

        assertThat(second).isEqualTo(first);
        assertThat(second.roomTypes()).hasSize(hotel.roomTypes().size() + 1);
    }

    @Test
    void rejectsSameKeyForAnotherHotel() throws Exception {
        HotelResponse first = createTaj("Key Reuse Update Test City");
        HotelResponse other = createTaj("Key Reuse Update Test City");
        String key = newKey();
        UpdateHotelRequest request = new UpdateHotelRequest("Taj Palace", null, null, null);
        updateHotel(key, first.id(), request);

        client.update(ADMIN_ID, key, other.id(), request)
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.code").value("IDEMPOTENCY_KEY_REUSED"));
    }

    @Test
    void rejectsCountBelowReserved() throws Exception {
        HotelResponse hotel = client.createHotel(newKey(), new CreateHotelRequest("Taj", "Count Below Reserved Test City", null,
                List.of(new RoomTypeRequest("Sea View Deluxe", "King bed, balcony facing the sea", 3, BigDecimal.TEN))));
        String roomTypeId = hotel.roomTypes().get(0).id();
        client.reserve(GUEST_ID, newKey(), hotel.id(), new CreateReservationRequest(
                        roomTypeId, LocalDate.parse("2026-11-10"), LocalDate.parse("2026-11-12"), 2))
                .andExpect(status().isCreated());

        client.update(ADMIN_ID, newKey(), hotel.id(), roomTypes(new RoomTypeChangeRequest(roomTypeId, null, null, 1, null)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("ROOM_COUNT_BELOW_RESERVED"));
        HotelResponse updated =
                updateHotel(newKey(), hotel.id(), roomTypes(new RoomTypeChangeRequest(roomTypeId, null, null, 2, null)));
        assertThat(updated.roomTypes().get(0).count()).isEqualTo(2);
        // The inventory took the new total too, so the 2 booked rooms leave none free.
        client.reserve(GUEST_ID, newKey(), hotel.id(), new CreateReservationRequest(
                        roomTypeId, LocalDate.parse("2026-11-10"), LocalDate.parse("2026-11-11"), 1))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("ROOMS_NOT_AVAILABLE"));
    }

    @Test
    void addedRoomTypeCanBeBooked() throws Exception {
        HotelResponse hotel = createTaj("Added Room Type Test City");
        HotelResponse updated = updateHotel(newKey(), hotel.id(), roomTypes(GARDEN_TWIN));
        String roomTypeId = updated.roomTypes().get(2).id();

        client.reserve(GUEST_ID, newKey(), hotel.id(), new CreateReservationRequest(
                        roomTypeId, LocalDate.parse("2026-11-10"), LocalDate.parse("2026-11-11"), 1))
                .andExpect(status().isCreated());
    }

    private HotelResponse createTaj(String city) throws Exception {
        return client.createHotel(newKey(), new CreateHotelRequest("Taj", city, "Sea-facing heritage hotel with a pool",
                List.of(SEA_VIEW, FAMILY_SUITE)));
    }

    private HotelResponse updateHotel(String key, String hotelId, UpdateHotelRequest request) throws Exception {
        MvcResult result = client.update(ADMIN_ID, key, hotelId, request).andExpect(status().isOk()).andReturn();
        return client.read(result, HotelResponse.class);
    }

    private static UpdateHotelRequest roomTypes(RoomTypeChangeRequest... roomTypes) {
        return new UpdateHotelRequest(null, null, null, List.of(roomTypes));
    }

    private static Arguments change(String name, Function<HotelResponse, UpdateHotelRequest> change) {
        return Arguments.of(named(name, change));
    }
}
