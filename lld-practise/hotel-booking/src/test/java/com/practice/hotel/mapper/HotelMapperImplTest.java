package com.practice.hotel.mapper;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.practice.hotel.api.dto.CreateHotelRequest;
import com.practice.hotel.api.dto.RoomTypeChangeRequest;
import com.practice.hotel.api.dto.RoomTypeRequest;
import com.practice.hotel.api.dto.UpdateHotelRequest;
import com.practice.hotel.domain.HotelChanges;
import com.practice.hotel.domain.RoomTypeChanges;
import com.practice.hotel.service.CreateHotelCommand;
import com.practice.hotel.service.NewRoomType;
import com.practice.hotel.service.RequestContext;
import com.practice.hotel.service.UpdateHotelCommand;

class HotelMapperImplTest {

    private static final RequestContext CONTEXT =
            new RequestContext("admin-1", Instant.parse("2026-10-24T09:15:02.123Z"), "key-1", "hash-1");

    private final HotelMapper mapper = new HotelMapperImpl();

    @Test
    void toCommandTrimsTextAndDefaultsDetails() {
        CreateHotelRequest request = new CreateHotelRequest("  Taj ", " Mumbai  ", null, List.of(
                new RoomTypeRequest(" Sea View Deluxe ", "  King bed, balcony facing the sea ", 10, new BigDecimal("4500.00"))));

        assertThat(mapper.toCommand(request, CONTEXT)).isEqualTo(new CreateHotelCommand(CONTEXT, "Taj", "Mumbai", "", List.of(
                new NewRoomType("Sea View Deluxe", "King bed, balcony facing the sea", 10, new BigDecimal("4500.00")))));
    }

    @Test
    void toUpdateCommandSplitsRoomTypes() {
        UpdateHotelRequest request = new UpdateHotelRequest(null, " Pune  ", null, List.of(
                new RoomTypeChangeRequest("room-1", null, "  King bed, balcony ", 8, null),
                new RoomTypeChangeRequest(null, " Garden Twin ", " Two single beds, garden view  ", 6, new BigDecimal("3200.00"))));

        assertThat(mapper.toUpdateCommand("hotel-1", request, CONTEXT)).isEqualTo(new UpdateHotelCommand(CONTEXT, "hotel-1",
                new HotelChanges(null, "Pune", null),
                List.of(new RoomTypeChanges("room-1", null, "King bed, balcony", 8, null)),
                List.of(new NewRoomType("Garden Twin", "Two single beds, garden view", 6, new BigDecimal("3200.00")))));
    }
}
