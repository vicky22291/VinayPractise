package com.practice.stripe;

import com.practice.stripe.domain.Plan;
import com.practice.stripe.domain.PlanChange;
import com.practice.stripe.service.ProrationCalculator;
import java.time.Instant;
import java.util.List;

public class Practice {
    public static void main(String[] args) {
        var calculator = new ProrationCalculator();
        var start = Instant.parse("2026-01-01T00:00:00Z");
        var end = Instant.parse("2026-01-31T00:00:00Z");
        var middle = Instant.parse("2026-01-16T00:00:00Z");
        System.out.println("Stage 1 (+500): " + calculator.single("USD", 2000, 3000, start, end, middle));
        var changes = List.of(new PlanChange(middle, new Plan(3000, 2)),
                new PlanChange(Instant.parse("2026-01-26T00:00:00Z"), new Plan(1000, 1)));
        System.out.println("Stage 2: " + calculator.calculate("USD", start, end, new Plan(2000, 1), changes, 0));
        System.out.println("Stage 3, 10% discount: " + calculator.calculate("USD", start, end, new Plan(2000, 1), changes, 1000));
    }
}
