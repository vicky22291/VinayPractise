package com.example.qabank.support;

import com.example.qabank.service.IdGenerator;

import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;

/** Produces 00000000-0000-0000-0000-000000000001, ...0002, ... so test failures are readable. */
public final class SequentialIdGenerator implements IdGenerator {
    private final AtomicLong counter = new AtomicLong();

    @Override
    public UUID next() {
        return new UUID(0, counter.incrementAndGet());
    }
}
