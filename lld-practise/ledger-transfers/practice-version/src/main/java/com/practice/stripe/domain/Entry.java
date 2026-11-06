package com.practice.stripe.domain;

import java.util.UUID;

/** Signed balance delta: debit is negative, credit is positive. Original entries are never edited. */
public record Entry(UUID id, UUID transferId, UUID accountId, long amount, String currency) {}
