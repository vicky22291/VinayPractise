package com.practice.stripe.domain;

import java.time.Duration;

public record RetryPolicy(int maxAttempts, Duration initialBackoff, Duration maxBackoff, Duration leaseDuration) {
    public RetryPolicy {
        if (maxAttempts < 1 || maxAttempts > 30 || initialBackoff == null || maxBackoff == null || leaseDuration == null
                || initialBackoff.isNegative() || initialBackoff.isZero() || maxBackoff.compareTo(initialBackoff) < 0
                || leaseDuration.isNegative() || leaseDuration.isZero()) throw new IllegalArgumentException("Invalid retry policy");
    }
    public Duration delay(int attempts) {
        Duration delay = initialBackoff;
        for (int i = 1; i < attempts; i++) {
            // Cap before multiplying, avoiding overflow for a large configured duration.
            if (delay.compareTo(maxBackoff.dividedBy(2)) > 0) return maxBackoff;
            delay = delay.multipliedBy(2);
        }
        return delay.compareTo(maxBackoff) > 0 ? maxBackoff : delay;
    }
}
