package com.practice.stripe.repository;

import com.practice.stripe.domain.Capture;
import com.practice.stripe.domain.Payment;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import org.springframework.stereotype.Repository;

@Repository
public class PaymentRepository {
    public static final class State {
        public final Map<UUID, Payment> payments = new LinkedHashMap<>();
        public final Map<UUID, Capture> captures = new LinkedHashMap<>();
        public final IdempotencyStore idempotency = new IdempotencyStore();
        private State() {}
    }
    private final State state = new State();

    /** All reads and writes use this lock; callers must not retain State outside the callback. */
    public synchronized <T> T transaction(Function<State, T> operation) { return operation.apply(state); }
}
