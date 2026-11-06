package com.practice.stripe;

import com.practice.stripe.domain.*;
import com.practice.stripe.repository.DeliveryRepository;
import com.practice.stripe.service.*;
import java.net.URI;
import java.time.*;
import java.util.Set;

public class Practice {
    public static void main(String[] args) {
        var clock = new DemoClock();
        var policy = new RetryPolicy(3, Duration.ofSeconds(1), Duration.ofMinutes(1), Duration.ofSeconds(30));
        var service = new DeliveryService(new DeliveryRepository(), clock, policy);
        service.register(URI.create("https://example.com/webhooks"), Set.of("payment.captured"), "endpoint");
        System.out.println("Stage 1: " + service.publish(new Event("evt-1", "payment.captured", "demo"), "event"));
        var worker = new DeliveryWorker(service, delivery -> Delivery.Outcome.UNKNOWN);
        System.out.println("Stage 2: " + worker.runOnce("worker-1"));
        clock.advance(Duration.ofSeconds(1));
        System.out.println("Worker crashes after claiming: " + service.claimNext("worker-crashed"));
        clock.advance(Duration.ofSeconds(32));
        System.out.println("Stage 3: " + new DeliveryWorker(service, delivery -> Delivery.Outcome.SUCCEEDED).runOnce("recovery-worker"));
    }
    private static class DemoClock extends Clock {
        private Instant now = Instant.parse("2026-01-01T00:00:00Z");
        void advance(Duration duration) { now = now.plus(duration); }
        public Instant instant() { return now; }
        public ZoneId getZone() { return ZoneOffset.UTC; }
        public Clock withZone(ZoneId zone) { return Clock.fixed(now, zone); }
    }
}
