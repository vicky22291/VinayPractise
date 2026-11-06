package com.practice.stripe.domain;

import com.practice.stripe.exception.ApiException;
import java.util.UUID;

/** Immutable snapshots: pending captures reserve authorization until their outcome is known. */
public record Payment(UUID id, long amount, String currency, Status status,
                      long capturedAmount, long reservedAmount) {
    public enum Status { CREATED, AUTHORIZED, PARTIALLY_CAPTURED, CAPTURED, CANCELED }

    public Payment authorize() {
        if (status != Status.CREATED) throw ApiException.conflict("Only a created payment can be authorized");
        return new Payment(id, amount, currency, Status.AUTHORIZED, 0, 0);
    }

    public Payment cancel() {
        if (capturedAmount != 0 || reservedAmount != 0 || status == Status.CANCELED)
            throw ApiException.conflict("Cannot cancel a captured, pending, or canceled payment");
        return new Payment(id, amount, currency, Status.CANCELED, 0, 0);
    }

    public Payment reserve(long captureAmount) {
        Checks.positive(captureAmount, "capture amount");
        if (status != Status.AUTHORIZED && status != Status.PARTIALLY_CAPTURED)
            throw ApiException.conflict("Capture requires an authorized payment");
        if (captureAmount > amount - capturedAmount - reservedAmount)
            throw ApiException.conflict("Capture exceeds remaining authorization");
        return new Payment(id, amount, currency, status, capturedAmount, reservedAmount + captureAmount);
    }

    public Payment resolve(long captureAmount, boolean accepted) {
        long captured = capturedAmount + (accepted ? captureAmount : 0);
        Status next = captured == amount ? Status.CAPTURED
                : captured > 0 ? Status.PARTIALLY_CAPTURED : Status.AUTHORIZED;
        return new Payment(id, amount, currency, next, captured, reservedAmount - captureAmount);
    }
}
