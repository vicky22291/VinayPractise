package com.practice.hotel.repository;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class RoomInventoryRepositoryImplTest {

    private static final LocalDate NOV_10 = LocalDate.parse("2026-11-10");
    private static final LocalDate NOV_11 = LocalDate.parse("2026-11-11");
    private static final LocalDate NOV_12 = LocalDate.parse("2026-11-12");
    private static final LocalDate NOV_13 = LocalDate.parse("2026-11-13");

    private final RoomInventoryRepository repository = new RoomInventoryRepositoryImpl();

    // room-1 has rows for Nov 10, 11 and 12, with 2 rooms each. Nov 13 has no row.
    @BeforeEach
    void addRoomType() {
        repository.addRoomType("hotel-1", "room-1", 2, NOV_10, NOV_13);
    }

    @Test
    void reserveIsAllOrNothing() {
        repository.reserve("room-1", List.of(NOV_11), 2);

        assertThat(repository.reserve("room-1", List.of(NOV_10, NOV_11), 1)).isFalse();
        assertThat(available(NOV_10)).isEqualTo(2);
    }

    @Test
    void reserveNeedsRowForEveryDate() {
        assertThat(repository.reserve("room-1", List.of(NOV_12, NOV_13), 1)).isFalse();
        assertThat(available(NOV_12)).isEqualTo(2);
    }

    // Nov 10 has 1 room left, Nov 11 has none and Nov 12 has 2. An empty expected value means the room type is left out.
    @ParameterizedTest
    @CsvSource({
            "2026-11-10, 2026-11-11, 1, 1",
            "2026-11-12, 2026-11-13, 2, 2",
            "2026-11-10, 2026-11-12, 1, ",
            "2026-11-12, 2026-11-14, 1, "
    })
    void findAvailableKeepsRoomTypesFreeOnEveryDate(LocalDate from, LocalDate to, int rooms, Integer expected) {
        repository.reserve("room-1", List.of(NOV_10, NOV_11), 1);
        repository.reserve("room-1", List.of(NOV_11), 1);

        assertThat(repository.findAvailable(List.of("room-1"), from.datesUntil(to).toList(), rooms).get("room-1"))
                .isEqualTo(expected);
    }

    @Test
    void changeTotalRoomsRejectsTotalBelowBooked() {
        repository.reserve("room-1", List.of(NOV_11), 2);

        assertThat(repository.changeTotalRooms(Map.of("room-1", 1), NOV_10)).isFalse();
        assertThat(available(NOV_10)).isEqualTo(2);
    }

    @Test
    void changeTotalRoomsKeepsBookingsAndEarlierDates() {
        repository.reserve("room-1", List.of(NOV_11), 1);

        assertThat(repository.changeTotalRooms(Map.of("room-1", 5), NOV_11)).isTrue();
        assertThat(List.of(available(NOV_10), available(NOV_11), available(NOV_12))).containsExactly(2, 4, 5);
    }

    @Test
    void parallelReservesNeverOverbook() throws Exception {
        int threads = 20;
        CyclicBarrier start = new CyclicBarrier(threads);
        Callable<Boolean> call = () -> {
            start.await();
            return repository.reserve("room-1", List.of(NOV_10, NOV_11), 1);
        };

        List<Boolean> results = new ArrayList<>();
        try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
            for (Future<Boolean> result : pool.invokeAll(Collections.nCopies(threads, call))) {
                results.add(result.get());
            }
        }

        assertThat(results).filteredOn(Boolean::booleanValue).hasSize(2);
        assertThat(available(NOV_10)).isZero();
    }

    // Rooms of room-1 available on the date, read as 0 when findAvailable leaves it out.
    private int available(LocalDate date) {
        return repository.findAvailable(List.of("room-1"), List.of(date), 1).getOrDefault("room-1", 0);
    }
}
