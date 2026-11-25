package com.shop.checkout;

import java.time.LocalDate;

import org.springframework.stereotype.Component;

/** Counters for the ops dashboard. */
@Component
public class OrderStats {

    private volatile long placed;
    private static long placedToday;
    private static LocalDate today = LocalDate.now();

    public void increment() {
        placed++;
        rollIfNewDay();
        placedToday++;
    }

    private static synchronized void rollIfNewDay() {
        if (!LocalDate.now().equals(today)) {
            today = LocalDate.now();
            placedToday = 0;
        }
    }

    public synchronized long placedToday() {
        return placedToday;
    }

    public long placed() {
        return placed;
    }
}
