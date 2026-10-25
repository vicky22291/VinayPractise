package com.practice.qabank.repository;

import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Supplier;

import org.springframework.stereotype.Repository;

import com.practice.qabank.domain.IdempotencyKey;
import com.practice.qabank.domain.IdempotentResult;

// One store for every write. The key holds the operation, and each operation always stores one type.
@Repository
public class IdempotencyRepositoryImpl implements IdempotencyRepository {

    // Entries are never removed: keys live as long as the app, one per successful write.
    private final ConcurrentHashMap<IdempotencyKey, Object> store = new ConcurrentHashMap<>();

    @Override
    public <T> IdempotentResult<T> getOrCreate(IdempotencyKey key, Class<T> type, Supplier<T> create) {
        // computeIfAbsent makes check-and-create one atomic step per key: a concurrent retry blocks until the first
        // call's create finishes and then gets its value, so two retries can never both run it. If create throws, no
        // entry is recorded and the client can retry with the same key.
        // The flag is local to this call, so only the call whose supplier ran sees replayed false. Comparing instances
        // wouldn't work for updates, whose no-op returns the unchanged stored instance.
        AtomicBoolean created = new AtomicBoolean();
        Object stored = store.computeIfAbsent(key, k -> {
            created.set(true);
            return Objects.requireNonNull(create.get(), "create returned null");
        });
        // A mismatch fails loudly here instead of handing back a silently wrong type.
        return new IdempotentResult<>(type.cast(stored), !created.get());
    }
}
