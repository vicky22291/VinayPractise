package com.practice.hotel.repository;

import java.util.Optional;

import com.practice.hotel.domain.IdempotencyKey;
import com.practice.hotel.domain.IdempotencyRecord;

public interface IdempotencyRepository {

    // Stores the record and returns empty if its key is free; otherwise returns the stored record unchanged.
    Optional<IdempotencyRecord> claim(IdempotencyRecord record);

    void complete(IdempotencyKey key, String resourceId);

    void release(IdempotencyKey key);
}
