package com.practice.stripe.service;

import com.practice.stripe.domain.*;
import com.practice.stripe.exception.ApiException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;

/** Pure calculator: exact integer fractions until one HALF_UP rounding of the invoice adjustment. */
@Service
public class ProrationCalculator {
    private static final BigInteger BILLION = BigInteger.valueOf(1_000_000_000);
    private static final BigInteger BASIS_POINTS = BigInteger.valueOf(10_000);

    public Proration single(String currency, long oldPrice, long newPrice, Instant start, Instant end, Instant at) {
        return calculate(currency, start, end, new Plan(oldPrice, 1), List.of(new PlanChange(at, new Plan(newPrice, 1))), 0);
    }

    public Proration calculate(String currency, Instant start, Instant end, Plan initial,
                               List<PlanChange> changes, int discountBasisPoints) {
        String normalized = Checks.currency(currency);
        if (start == null || end == null || !start.isBefore(end)) throw ApiException.invalid("Period must have positive duration");
        if (initial == null || changes == null) throw ApiException.invalid("Initial plan and changes are required");
        if (discountBasisPoints < 0 || discountBasisPoints > 10_000)
            throw ApiException.invalid("discountBasisPoints must be between 0 and 10000");
        List<PlanChange> ordered = new ArrayList<>(changes);
        // Require the caller's chronology rather than silently reordering simultaneous product changes.
        Instant previous = null;
        for (PlanChange change : ordered) {
            if (change == null || change.at() == null || change.plan() == null) throw ApiException.invalid("Each change needs a time and plan");
            if (change.at().isBefore(start) || !change.at().isBefore(end)) throw ApiException.invalid("Change must be in [start, end)");
            if (previous != null && !previous.isBefore(change.at())) throw ApiException.invalid("Changes must be strictly increasing");
            previous = change.at();
        }
        BigInteger denominator = nanos(start, end).multiply(BASIS_POINTS);
        BigInteger discountFactor = BigInteger.valueOf(10_000 - discountBasisPoints);
        List<Proration.Segment> segments = new ArrayList<>();
        Plan plan = initial;
        Instant cursor = start;
        for (PlanChange change : ordered) {
            append(segments, cursor, change.at(), plan, initial, discountFactor);
            cursor = change.at();
            plan = change.plan();
        }
        append(segments, cursor, end, plan, initial, discountFactor);
        BigInteger numerator = segments.stream().map(Proration.Segment::numerator).reduce(BigInteger.ZERO, BigInteger::add);
        long rounded = new BigDecimal(numerator).divide(new BigDecimal(denominator), 0, RoundingMode.HALF_UP).longValueExact();
        return new Proration(normalized, rounded, numerator, denominator, segments);
    }

    private void append(List<Proration.Segment> segments, Instant start, Instant end, Plan plan, Plan initial, BigInteger discountFactor) {
        if (start.equals(end)) return;
        BigInteger delta = plan.fullPeriodAmount().subtract(initial.fullPeriodAmount());
        BigInteger numerator = delta.multiply(nanos(start, end)).multiply(discountFactor);
        segments.add(new Proration.Segment(start, end, plan, numerator));
    }

    private BigInteger nanos(Instant start, Instant end) {
        Duration duration = Duration.between(start, end);
        return BigInteger.valueOf(duration.getSeconds()).multiply(BILLION).add(BigInteger.valueOf(duration.getNano()));
    }
}
