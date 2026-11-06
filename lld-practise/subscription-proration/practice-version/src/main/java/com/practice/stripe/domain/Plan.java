package com.practice.stripe.domain;

import com.practice.stripe.exception.ApiException;
import java.math.BigInteger;

public record Plan(long price, long quantity) {
    public Plan {
        if (price < 0) throw ApiException.invalid("Plan price cannot be negative");
        Checks.positive(quantity, "quantity");
    }
    public BigInteger fullPeriodAmount() { return BigInteger.valueOf(price).multiply(BigInteger.valueOf(quantity)); }
}
