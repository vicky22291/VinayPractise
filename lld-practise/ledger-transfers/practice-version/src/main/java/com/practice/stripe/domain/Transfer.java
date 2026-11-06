package com.practice.stripe.domain;

import java.util.UUID;

public record Transfer(UUID id, UUID sourceId, UUID destinationId, long amount, String currency,
                       UUID reversalOf, UUID reversedBy) {
    public Transfer reversedBy(UUID reversalId) {
        return new Transfer(id, sourceId, destinationId, amount, currency, reversalOf, reversalId);
    }
}
