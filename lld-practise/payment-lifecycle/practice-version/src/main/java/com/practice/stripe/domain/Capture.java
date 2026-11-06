package com.practice.stripe.domain;

import java.util.UUID;

public record Capture(UUID id, UUID paymentId, long amount, String currency, Status status) {
    public enum Status { UNKNOWN, SUCCEEDED, DECLINED }
    public Capture withStatus(Status next) { return new Capture(id, paymentId, amount, currency, next); }
}
