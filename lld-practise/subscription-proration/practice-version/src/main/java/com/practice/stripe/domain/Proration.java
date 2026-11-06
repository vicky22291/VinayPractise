package com.practice.stripe.domain;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;

public record Proration(String currency, long adjustment, BigInteger exactNumerator,
                        BigInteger exactDenominator, List<Segment> segments) {
    public Proration { segments = List.copyOf(segments); }
    /** Each segment contributes numerator / the result's exactDenominator, before the single final rounding. */
    public record Segment(Instant start, Instant end, Plan plan, BigInteger numerator) {}
}
