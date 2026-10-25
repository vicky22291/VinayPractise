package com.practice.hotel.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Named.named;

import java.time.Instant;
import java.time.LocalDate;
import java.util.stream.Stream;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.hotel.domain.Stay;
import com.practice.hotel.error.InvalidStayException;

class StayValidatorTest {

    private static final Instant NOW = Instant.parse("2026-10-24T09:15:02.123Z");
    private static final LocalDate TODAY = LocalDate.parse("2026-10-24");

    static Stream<Arguments> validStays() {
        return Stream.of(
                Arguments.of(named("today to tomorrow", TODAY), TODAY.plusDays(1)),
                Arguments.of(named("30 nights", TODAY), TODAY.plusDays(30)),
                Arguments.of(named("checkOut 365 days ahead", TODAY.plusDays(364)), TODAY.plusDays(365)));
    }

    @ParameterizedTest
    @MethodSource("validStays")
    void acceptsStay(LocalDate checkIn, LocalDate checkOut) {
        assertThat(StayValidator.requireValidStay(checkIn, checkOut, NOW)).isEqualTo(new Stay(checkIn, checkOut));
    }

    static Stream<Arguments> invalidStays() {
        return Stream.of(
                Arguments.of(named("only checkIn", TODAY), null),
                Arguments.of(named("only checkOut", null), TODAY.plusDays(1)),
                Arguments.of(named("checkOut equal to checkIn", TODAY), TODAY),
                Arguments.of(named("checkOut before checkIn", TODAY.plusDays(1)), TODAY),
                Arguments.of(named("31 nights", TODAY), TODAY.plusDays(31)),
                Arguments.of(named("checkIn yesterday", TODAY.minusDays(1)), TODAY.plusDays(1)),
                Arguments.of(named("checkOut 366 days ahead", TODAY.plusDays(365)), TODAY.plusDays(366)));
    }

    @ParameterizedTest
    @MethodSource("invalidStays")
    void rejectsStay(LocalDate checkIn, LocalDate checkOut) {
        assertThatThrownBy(() -> StayValidator.requireValidStay(checkIn, checkOut, NOW))
                .isInstanceOf(InvalidStayException.class);
    }
}
