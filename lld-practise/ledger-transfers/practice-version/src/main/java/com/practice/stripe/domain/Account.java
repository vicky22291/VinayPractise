package com.practice.stripe.domain;

import java.util.UUID;

public record Account(UUID id, String currency, long openingBalance, long balance) {
    public Account withBalance(long next) { return new Account(id, currency, openingBalance, next); }
}
