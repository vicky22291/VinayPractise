package com.example.qabank.domain;

import java.time.Instant;
import java.util.UUID;

public record Question(UUID id, UUID authorId, String title, String body, Instant createdAt) {
}
