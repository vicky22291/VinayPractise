package com.practice.hotel.functional;

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
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.HotelResponse;
import com.practice.hotel.api.dto.RoomTypeRequest;

@SpringBootTest
@AutoConfigureMockMvc
@Import(TestClockConfig.class)
class GetHotelFunctionalTest {

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
    void returnsHotel() throws Exception {
        HotelResponse created = client.createHotel(newKey(), new CreateHotelRequest("Taj", "Get Test City",
                "Sea-facing heritage hotel with a pool",
                List.of(new RoomTypeRequest("Sea View Deluxe", "King bed, balcony facing the sea", 10,
                        new BigDecimal("4500.00")))));

        MvcResult result = client.get(created.id())
                .andExpect(status().isOk())
                .andReturn();

        assertThat(client.read(result, HotelResponse.class)).isEqualTo(created);
    }

    static Stream<Arguments> unknownIds() {
        return Stream.of(
                Arguments.of(named("unknown UUID", UUID.randomUUID().toString())),
                Arguments.of(named("id that isn't a UUID", "not-a-uuid")));
    }

    @ParameterizedTest
    @MethodSource("unknownIds")
    void returnsNotFound(String hotelId) throws Exception {
        client.get(hotelId)
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("HOTEL_NOT_FOUND"));
    }
}
