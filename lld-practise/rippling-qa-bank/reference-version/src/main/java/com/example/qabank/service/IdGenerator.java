package com.example.qabank.service;

import java.util.UUID;

/** Seam for deterministic ids in tests. */
@FunctionalInterface
public interface IdGenerator {
    UUID next();
}
