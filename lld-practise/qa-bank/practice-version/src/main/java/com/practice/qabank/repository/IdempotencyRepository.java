package com.practice.qabank.repository;

import java.util.function.Supplier;

import com.practice.qabank.domain.IdempotencyKey;
import com.practice.qabank.domain.IdempotentResult;

public interface IdempotencyRepository {

    /**
     * Returns the value stored under {@code key} with {@code replayed} true, or runs {@code create}, stores its result
     * under the key and returns it with {@code replayed} false. Concurrent calls with the same key run {@code create}
     * at most once. If {@code create} throws, nothing is stored.
     *
     * @throws ClassCastException if the value stored under {@code key} isn't a {@code type}
     */
    <T> IdempotentResult<T> getOrCreate(IdempotencyKey key, Class<T> type, Supplier<T> create);
}
