package com.practice.stripe.domain;

/** An unmatched payment has a null invoice and the NONE rule. */
public record MatchResult(Payment payment, Invoice invoice, MatchRule rule) {
    public String description() {
        String prefix = "payment " + payment.id() + " (amount " + payment.amount() + ")";
        return invoice == null ? prefix + " has no matching invoice"
                : prefix + " pays invoice " + invoice.id() + " due " + invoice.dueDate();
    }
}
