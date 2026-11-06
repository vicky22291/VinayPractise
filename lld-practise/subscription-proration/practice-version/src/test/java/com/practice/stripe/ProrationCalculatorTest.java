package com.practice.stripe;

import com.practice.stripe.domain.*;
import com.practice.stripe.exception.ApiException;
import com.practice.stripe.service.ProrationCalculator;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class ProrationCalculatorTest {
    private final ProrationCalculator calculator = new ProrationCalculator();
    private final Instant start = Instant.parse("2026-01-01T00:00:00Z");
    private final Instant end = start.plusSeconds(30 * 86400);
    private final Instant middle = start.plusSeconds(15 * 86400);

    @Test void halfwayUpgradeAndDowngrade() {
        assertThat(calculator.single("usd", 2000, 3000, start, end, middle).adjustment()).isEqualTo(500);
        assertThat(calculator.single("USD", 3000, 2000, start, end, middle).adjustment()).isEqualTo(-500);
    }

    @Test void halfUnitsRoundAwayFromZero() {
        assertThat(calculator.single("USD", 0, 1, start, end, middle).adjustment()).isEqualTo(1);
        assertThat(calculator.single("USD", 1, 0, start, end, middle).adjustment()).isEqualTo(-1);
    }

    @Test void startIsInclusiveAndEndIsExclusive() {
        assertThat(calculator.single("USD", 2000, 3000, start, end, start).adjustment()).isEqualTo(1000);
        assertThatThrownBy(() -> calculator.single("USD", 2000, 3000, start, end, end)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> calculator.single("USD", 2000, 3000, start, end, start.minusNanos(1))).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> calculator.single("USD", 2000, 3000, start, start, start)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> calculator.single("USD", 2000, 3000, end, start, start)).isInstanceOf(ApiException.class);
    }

    @Test void quantitiesAndAdjacentChangesCoverTheWholePeriodOnce() {
        var changes = List.of(new PlanChange(start.plusSeconds(10 * 86400), new Plan(3000, 2)),
                new PlanChange(start.plusSeconds(20 * 86400), new Plan(1000, 1)));
        Proration result = calculator.calculate("USD", start, end, new Plan(2000, 1), changes, 0);
        assertThat(result.adjustment()).isEqualTo(1000); // (4000 * 10 - 1000 * 10) / 30
        assertThat(result.segments()).hasSize(3);
        assertThat(result.segments().getFirst().start()).isEqualTo(start);
        assertThat(result.segments().getLast().end()).isEqualTo(end);
        assertThat(result.segments().get(0).end()).isEqualTo(result.segments().get(1).start());
        assertThat(result.segments().get(1).end()).isEqualTo(result.segments().get(2).start());
    }

    @Test void roundsOnlyAfterSummingIntervals() {
        var changes = List.of(new PlanChange(start, new Plan(1, 1)),
                new PlanChange(start.plusSeconds(1), new Plan(1, 1)),
                new PlanChange(start.plusSeconds(2), new Plan(1, 1)));
        Proration result = calculator.calculate("USD", start, start.plusSeconds(3), new Plan(0, 1), changes, 0);
        assertThat(result.adjustment()).isEqualTo(1); // three thirds; rounding each line would lose this cent
        assertThat(result.exactNumerator()).isEqualTo(result.exactDenominator());
    }

    @Test void discountExtensionPreservesCreditsAndBaseBehavior() {
        var changes = List.of(new PlanChange(middle, new Plan(3000, 1)));
        assertThat(calculator.calculate("USD", start, end, new Plan(2000, 1), changes, 1000).adjustment()).isEqualTo(450);
        assertThat(calculator.calculate("USD", start, end, new Plan(2000, 1), changes, 10000).adjustment()).isZero();
        assertThat(calculator.calculate("USD", start, end, new Plan(3000, 1), List.of(new PlanChange(middle, new Plan(2000, 1))), 1000).adjustment()).isEqualTo(-450);
    }

    @Test void handlesSubsecondsLeapDayAndLargeIntermediateAmountsExactly() {
        assertThat(calculator.single("USD", 0, 1, start, start.plusSeconds(1), start.plusNanos(500_000_000)).adjustment()).isEqualTo(1);
        Instant leapStart = Instant.parse("2024-02-28T00:00:00Z");
        assertThat(calculator.single("USD", 200, 400, leapStart, leapStart.plusSeconds(2 * 86400), leapStart.plusSeconds(86400)).adjustment()).isEqualTo(100);
        var huge = new Plan(Long.MAX_VALUE, Long.MAX_VALUE);
        assertThat(calculator.calculate("USD", start, end, huge, List.of(new PlanChange(middle, huge)), 0).adjustment()).isZero();
        assertThatThrownBy(() -> calculator.calculate("USD", start, end, new Plan(0, 1), List.of(new PlanChange(start, huge)), 0)).isInstanceOf(ArithmeticException.class);
    }

    @Test void rejectsInvalidPlansChronologyAndDiscounts() {
        assertThatThrownBy(() -> new Plan(-1, 1)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> new Plan(100, 0)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> calculator.calculate("USD", start, end, new Plan(100, 1), List.of(
                new PlanChange(middle, new Plan(200, 1)), new PlanChange(middle, new Plan(300, 1))), 0)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> calculator.calculate("USD", start, end, new Plan(100, 1), List.of(
                new PlanChange(middle, new Plan(200, 1)), new PlanChange(start, new Plan(300, 1))), 0)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> calculator.calculate("USD", start, end, new Plan(100, 1), List.of(), -1)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> calculator.calculate("USD", start, end, new Plan(100, 1), List.of(), 10001)).isInstanceOf(ApiException.class);
        assertThat(calculator.calculate("USD", start, end, new Plan(100, 1), List.of(), 0).adjustment()).isZero();
    }
}
