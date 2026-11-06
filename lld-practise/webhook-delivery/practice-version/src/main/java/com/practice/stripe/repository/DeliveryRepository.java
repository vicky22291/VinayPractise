package com.practice.stripe.repository;

import com.practice.stripe.domain.*;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import org.springframework.stereotype.Repository;

@Repository
public class DeliveryRepository {
    public static final class State {
        public final Map<UUID, Endpoint> endpoints = new LinkedHashMap<>();
        public final Map<String, Event> events = new LinkedHashMap<>();
        public final Map<UUID, Delivery> deliveries = new LinkedHashMap<>();
        public final IdempotencyStore idempotency = new IdempotencyStore();
        private State() {}
    }
    private final State state = new State();
    public synchronized <T> T transaction(Function<State, T> operation) { return operation.apply(state); }
}
