package com.practice.hotel.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Named.named;

import java.math.BigDecimal;
import java.util.stream.Stream;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

class RoomTypeTest {

    private static final BigDecimal PRICE = new BigDecimal("4500.00");
    private static final RoomType DELUXE = new RoomType("room-1", "Deluxe", "King bed", 10, PRICE);

    static Stream<Arguments> singleRoomTypeChanges() {
        return Stream.of(
                Arguments.of(named("name", new RoomTypeChanges("room-1", "Deluxe King", null, null, null)),
                        new RoomType("room-1", "Deluxe King", "King bed", 10, PRICE)),
                Arguments.of(named("description", new RoomTypeChanges("room-1", null, "King bed, balcony", null, null)),
                        new RoomType("room-1", "Deluxe", "King bed, balcony", 10, PRICE)),
                Arguments.of(named("totalRooms", new RoomTypeChanges("room-1", null, null, 0, null)),
                        new RoomType("room-1", "Deluxe", "King bed", 0, PRICE)),
                Arguments.of(named("pricePerNight", new RoomTypeChanges("room-1", null, null, null, new BigDecimal("3500.00"))),
                        new RoomType("room-1", "Deluxe", "King bed", 10, new BigDecimal("3500.00"))));
    }

    @ParameterizedTest
    @MethodSource("singleRoomTypeChanges")
    void withChangesKeepsNullFields(RoomTypeChanges changes, RoomType expected) {
        assertThat(DELUXE.withChanges(changes)).isEqualTo(expected);
    }
}
