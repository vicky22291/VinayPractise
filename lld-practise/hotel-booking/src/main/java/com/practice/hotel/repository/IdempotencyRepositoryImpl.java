package com.practice.hotel.repository;

import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Repository;

import com.practice.hotel.domain.IdempotencyKey;
import com.practice.hotel.domain.IdempotencyRecord;
import com.practice.hotel.domain.IdempotencyStatus;

@Repository
public class IdempotencyRepositoryImpl implements IdempotencyRepository {

    private final ConcurrentHashMap<IdempotencyKey, IdempotencyRecord> records = new ConcurrentHashMap<>();

    @Override
    public Optional<IdempotencyRecord> claim(IdempotencyRecord record) {
        return Optional.ofNullable(records.putIfAbsent(record.key(), record));
    }

    @Override
    public void complete(IdempotencyKey key, String resourceId) {
        records.computeIfPresent(key, (k, record) -> new IdempotencyRecord(
                k, record.requestHash(), IdempotencyStatus.COMPLETED, resourceId, record.createdAt()));
    }

    @Override
    public void release(IdempotencyKey key) {
        records.remove(key);
    }
}
