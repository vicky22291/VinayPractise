package com.practice.stripe.repository;

import com.practice.stripe.domain.Account;
import com.practice.stripe.domain.Entry;
import com.practice.stripe.domain.Transfer;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import org.springframework.stereotype.Repository;

@Repository
public class LedgerRepository {
    public static final class State {
        public final Map<UUID, Account> accounts = new LinkedHashMap<>();
        public final Map<UUID, Transfer> transfers = new LinkedHashMap<>();
        public final List<Entry> entries = new ArrayList<>();
        public final IdempotencyStore idempotency = new IdempotencyStore();
        private State() {}
    }
    private final State state = new State();

    /** One lock covers validation, both balances, entries, reversal markers and retry results. */
    public synchronized <T> T transaction(Function<State, T> operation) { return operation.apply(state); }
}
