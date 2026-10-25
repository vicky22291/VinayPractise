package com.practice.hotel.repository;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.stream.IntStream;

import org.junit.jupiter.api.Test;

import com.practice.hotel.domain.CityKey;
import com.practice.hotel.domain.Hotel;
import com.practice.hotel.domain.RoomType;

class HotelRepositoryImplTest {

    private static final Instant NOW = Instant.parse("2026-10-24T09:15:02.123Z");

    private final HotelRepository repository = new HotelRepositoryImpl();

    @Test
    void parallelUpdatesAreAllKept() throws Exception {
        int threads = 20;
        repository.save(new Hotel("hotel-1", "admin-1", "Taj", "Mumbai", "", NOW, NOW, List.of()));
        List<String> roomTypeIds = IntStream.range(0, threads).mapToObj(i -> "room-" + i).toList();
        CyclicBarrier start = new CyclicBarrier(threads);
        List<Callable<Optional<Hotel>>> calls = roomTypeIds.stream()
                .map(id -> (Callable<Optional<Hotel>>) () -> {
                    RoomType roomType = new RoomType(id, "Room " + id, "A room", 1, BigDecimal.TEN);
                    start.await();
                    return repository.update("hotel-1", hotel -> hotel.withRoomType(roomType, NOW));
                })
                .toList();

        try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
            for (Future<Optional<Hotel>> result : pool.invokeAll(calls)) {
                assertThat(result.get()).isPresent();
            }
        }

        assertThat(repository.findById("hotel-1").orElseThrow().roomTypes())
                .extracting(RoomType::id)
                .containsExactlyInAnyOrderElementsOf(roomTypeIds);
    }

    @Test
    void findByCityFiltersAndSorts() {
        // A case-sensitive sort would put "Taj" before "taj", and without the filter "Abode" would come first.
        repository.save(hotel("hotel-2", "Taj", "Mumbai"));
        repository.save(hotel("hotel-4", "Abode", "Pune"));
        repository.save(hotel("hotel-1", "taj", "MUMBAI"));
        repository.save(hotel("hotel-3", "Harbour Inn", "mumbai"));

        assertThat(repository.findByCity(CityKey.of("Mumbai")))
                .extracting(Hotel::id)
                .containsExactly("hotel-3", "hotel-1", "hotel-2");
    }

    private static Hotel hotel(String id, String name, String city) {
        return new Hotel(id, "admin-1", name, city, "", NOW, NOW, List.of());
    }
}
