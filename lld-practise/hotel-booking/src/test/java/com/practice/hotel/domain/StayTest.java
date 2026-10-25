package com.practice.hotel.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Named.named;

import java.time.LocalDate;
import java.util.List;
import java.util.stream.Stream;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

class StayTest {

    private static final LocalDate NOV_10 = LocalDate.parse("2026-11-10");
    private static final LocalDate NOV_11 = LocalDate.parse("2026-11-11");
    private static final LocalDate NOV_12 = LocalDate.parse("2026-11-12");
    private static final LocalDate NOV_13 = LocalDate.parse("2026-11-13");

    static Stream<Arguments> stays() {
        return Stream.of(
                Arguments.of(named("1 night", new Stay(NOV_10, NOV_11)), List.of(NOV_10)),
                Arguments.of(named("3 nights", new Stay(NOV_10, NOV_13)), List.of(NOV_10, NOV_11, NOV_12)));
    }

    @ParameterizedTest
    @MethodSource("stays")
    void nightsRunUpToCheckOut(Stay stay, List<LocalDate> nights) {
        assertThat(stay.nights()).isEqualTo(nights);
        assertThat(stay.nightCount()).isEqualTo(nights.size());
    }
}
