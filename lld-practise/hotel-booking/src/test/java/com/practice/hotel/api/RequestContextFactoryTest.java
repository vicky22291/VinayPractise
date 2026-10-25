package com.practice.hotel.api;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Named.named;

import java.math.BigDecimal;
import java.util.List;
import java.util.stream.Stream;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.RoomTypeRequest;

class RequestContextFactoryTest {

    private static final String ADMIN_ID = "admin-1";
    private static final String PATH = "/api/v1/hotels";

    private final RequestContextFactory factory = new RequestContextFactory(new ObjectMapper());

    static Stream<Arguments> changedInputs() {
        return Stream.of(
                Arguments.of(named("change actorId", "admin-2"), PATH, body("Taj")),
                Arguments.of(ADMIN_ID, named("change path", "/api/v1/hotels/hotel-1"), body("Taj")),
                Arguments.of(ADMIN_ID, PATH, named("change body", body("Taj Palace"))));
    }

    @ParameterizedTest
    @MethodSource("changedInputs")
    void hashChangesWithEachInput(String actorId, String path, Object body) {
        String hash = factory.hash(ADMIN_ID, PATH, body("Taj"));

        assertThat(factory.hash(ADMIN_ID, PATH, body("Taj"))).isEqualTo(hash);
        assertThat(factory.hash(actorId, path, body)).isNotEqualTo(hash);
    }

    private static CreateHotelRequest body(String name) {
        return new CreateHotelRequest(name, "Mumbai", null,
                List.of(new RoomTypeRequest("Deluxe", "King bed", 10, new BigDecimal("4500.00"))));
    }
}
