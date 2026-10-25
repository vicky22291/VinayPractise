package com.practice.hotel.domain;

public record IdempotencyKey(OperationType operation, String key) {
}
