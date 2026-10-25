package com.practice.hotel.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Named.named;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.MethodSource;

class HotelTest {

    private static final Instant NOW = Instant.parse("2026-10-24T09:15:02.123Z");
    private static final Instant LATER = NOW.plusSeconds(60);
    private static final RoomType DELUXE = roomType("room-1", "Deluxe");
    private static final RoomType SUITE = roomType("room-2", "Suite");
    private static final Hotel TAJ = new Hotel("hotel-1", "admin-1", "Taj", "Mumbai", "Sea-facing", NOW, NOW,
            List.of(DELUXE, SUITE));

    @ParameterizedTest
    @CsvSource({
            "Deluxe, Suite, false",
            "Deluxe, deluxe, true",
            "Deluxe, ' Deluxe ', true"
    })
    void detectsDuplicateRoomTypeNames(String first, String second, boolean duplicate) {
        Hotel hotel = new Hotel("hotel-1", "admin-1", "Taj", "Mumbai", "", NOW, NOW,
                List.of(roomType("room-1", first), roomType("room-2", second)));

        assertThat(hotel.hasDuplicateRoomTypeNames()).isEqualTo(duplicate);
    }

    static Stream<Arguments> singleHotelChanges() {
        return Stream.of(
                Arguments.of(named("name", new HotelChanges("Taj Palace", null, null)),
                        new Hotel("hotel-1", "admin-1", "Taj Palace", "Mumbai", "Sea-facing", NOW, LATER, TAJ.roomTypes())),
                Arguments.of(named("city", new HotelChanges(null, "Pune", null)),
                        new Hotel("hotel-1", "admin-1", "Taj", "Pune", "Sea-facing", NOW, LATER, TAJ.roomTypes())),
                Arguments.of(named("details", new HotelChanges(null, null, "")),
                        new Hotel("hotel-1", "admin-1", "Taj", "Mumbai", "", NOW, LATER, TAJ.roomTypes())));
    }

    @ParameterizedTest
    @MethodSource("singleHotelChanges")
    void withChangesKeepsNullFields(HotelChanges changes, Hotel expected) {
        assertThat(TAJ.withChanges(changes, LATER)).isEqualTo(expected);
    }

    static Stream<Arguments> roomTypesToSet() {
        RoomType deluxeKing = roomType("room-1", "Deluxe King");
        RoomType gardenTwin = roomType("room-3", "Garden Twin");
        return Stream.of(
                Arguments.of(named("existing id", deluxeKing), List.of(deluxeKing, SUITE)),
                Arguments.of(named("new id", gardenTwin), List.of(DELUXE, SUITE, gardenTwin)));
    }

    @ParameterizedTest
    @MethodSource("roomTypesToSet")
    void withRoomTypeReplacesOrAppends(RoomType roomType, List<RoomType> expected) {
        assertThat(TAJ.withRoomType(roomType, LATER)).isEqualTo(
                new Hotel("hotel-1", "admin-1", "Taj", "Mumbai", "Sea-facing", NOW, LATER, expected));
    }

    // An empty expected name means no room type has that id.
    @ParameterizedTest
    @CsvSource({
            "room-2, Suite",
            "room-9, "
    })
    void findsRoomTypeById(String id, String expectedName) {
        assertThat(TAJ.findRoomType(id).map(RoomType::name)).isEqualTo(Optional.ofNullable(expectedName));
    }

    private static RoomType roomType(String id, String name) {
        return new RoomType(id, name, "A room", 1, BigDecimal.TEN);
    }
}
