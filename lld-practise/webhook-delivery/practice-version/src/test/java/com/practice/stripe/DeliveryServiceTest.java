package com.practice.stripe;

import com.practice.stripe.domain.*;
import com.practice.stripe.exception.ApiException;
import com.practice.stripe.repository.DeliveryRepository;
import com.practice.stripe.service.*;
import java.net.URI;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class DeliveryServiceTest {
    private final MutableClock clock = new MutableClock();
    private final RetryPolicy policy = new RetryPolicy(3, Duration.ofSeconds(1), Duration.ofSeconds(2), Duration.ofSeconds(30));
    private final DeliveryService service = new DeliveryService(new DeliveryRepository(), clock, policy);
    private final Event event = new Event("evt-1", "payment.captured", "payload");

    private Delivery pending() {
        service.register(URI.create("https://example.com/hook"), Set.of(event.type()), "endpoint");
        return service.publish(event, "publish").deliveries().getFirst();
    }

    @Test void routingIsDeduplicatedByEventAndEndpointAndPayloadIsChecked() {
        Delivery pending = pending();
        service.register(URI.create("https://example.com/other"), Set.of("other.type"), "other");
        assertThat(service.publish(event, "publish").deliveries()).containsExactly(pending);
        assertThat(service.publish(event, "new-publish-key").deliveries()).containsExactly(pending);
        assertThat(service.list()).hasSize(1);
        assertThatThrownBy(() -> service.publish(new Event(event.id(), event.type(), "changed"), "new-key")).hasMessageContaining("different payload");
        assertThatThrownBy(() -> service.publish(new Event("evt-2", event.type(), "payload"), "publish")).hasMessageContaining("different request");
        assertThat(service.publish(new Event("unmatched", "unknown", ""), "unmatched").deliveries()).isEmpty();
    }

    @Test void successIsTerminalAndAttemptHistoryIsImmutable() {
        Delivery pending = pending();
        Delivery claimed = service.claimNext("worker").orElseThrow();
        Delivery done = service.complete(claimed.id(), claimed.leaseToken(), Delivery.Outcome.SUCCEEDED);
        assertThat(done.status()).isEqualTo(Delivery.Status.DELIVERED);
        assertThat(done.history().getFirst().outcome()).isEqualTo(Delivery.Outcome.SUCCEEDED);
        assertThat(done.history().getFirst().finishedAt()).isEqualTo(clock.instant());
        assertThat(service.claimNext("another")).isEmpty();
        assertThatThrownBy(() -> service.complete(claimed.id(), claimed.leaseToken(), Delivery.Outcome.SUCCEEDED)).isInstanceOf(ApiException.class);
        assertThat(pending.history()).isEmpty();
        assertThatThrownBy(() -> done.history().clear()).isInstanceOf(UnsupportedOperationException.class);
    }

    @Test void failureAndTimeoutUseExponentialBackoffAndBoundedAttempts() {
        pending();
        Delivery first = service.claimNext("worker").orElseThrow();
        Delivery retry = service.complete(first.id(), first.leaseToken(), Delivery.Outcome.UNKNOWN);
        assertThat(retry.nextAttemptAt()).isEqualTo(clock.instant().plusSeconds(1));
        assertThat(retry.history().getFirst().outcome()).isEqualTo(Delivery.Outcome.UNKNOWN);
        assertThat(service.claimNext("early")).isEmpty();
        clock.advance(Duration.ofSeconds(1));
        Delivery second = service.claimNext("worker").orElseThrow();
        retry = service.complete(second.id(), second.leaseToken(), Delivery.Outcome.FAILED);
        assertThat(retry.nextAttemptAt()).isEqualTo(clock.instant().plusSeconds(2));
        clock.advance(Duration.ofSeconds(2));
        Delivery third = service.claimNext("worker").orElseThrow();
        Delivery dead = service.complete(third.id(), third.leaseToken(), Delivery.Outcome.FAILED);
        assertThat(dead.status()).isEqualTo(Delivery.Status.DEAD);
        assertThat(dead.attempts()).isEqualTo(3);
        clock.advance(Duration.ofDays(1));
        assertThat(service.claimNext("worker")).isEmpty();
        assertThat(policy.delay(10)).isEqualTo(Duration.ofSeconds(2));
    }

    @Test void expiredLeaseBecomesUnknownAndStaleWorkerCannotCompleteNewClaim() {
        pending();
        Delivery crashed = service.claimNext("crashed").orElseThrow();
        clock.advance(Duration.ofSeconds(30));
        assertThatThrownBy(() -> service.complete(crashed.id(), crashed.leaseToken(), Delivery.Outcome.SUCCEEDED)).hasMessageContaining("expired");
        assertThat(service.claimNext("recovering")).isEmpty(); // recovered, but backoff is not yet due
        assertThat(service.get(crashed.id()).history().getFirst().outcome()).isEqualTo(Delivery.Outcome.UNKNOWN);
        clock.advance(Duration.ofSeconds(1));
        Delivery recovered = service.claimNext("recovering").orElseThrow();
        assertThat(recovered.id()).isEqualTo(crashed.id());
        assertThat(recovered.event().id()).isEqualTo(event.id());
        assertThat(recovered.leaseToken()).isNotEqualTo(crashed.leaseToken());
        assertThatThrownBy(() -> service.complete(crashed.id(), crashed.leaseToken(), Delivery.Outcome.SUCCEEDED)).hasMessageContaining("Stale");
        assertThat(service.complete(recovered.id(), recovered.leaseToken(), Delivery.Outcome.SUCCEEDED).status()).isEqualTo(Delivery.Status.DELIVERED);
    }

    @Test void repeatedlyCrashedWorkersEventuallyExhaustAttempts() {
        pending();
        for (int i = 0; i < 3; i++) {
            assertThat(service.claimNext("worker")).isPresent();
            clock.advance(Duration.ofSeconds(32));
        }
        assertThat(service.claimNext("recovery")).isEmpty();
        assertThat(service.list().getFirst().status()).isEqualTo(Delivery.Status.DEAD);
        assertThat(service.list().getFirst().history()).allMatch(a -> a.outcome() == Delivery.Outcome.UNKNOWN);
    }

    @Test void racingWorkersClaimEachDeliveryOnlyOnce() throws Exception {
        pending();
        var claims = Concurrently.run(10, i -> service.claimNext("worker-" + i));
        assertThat(claims.stream().filter(Optional::isPresent).count()).isEqualTo(1);
        assertThat(service.list().getFirst().attempts()).isEqualTo(1);
    }

    @Test void slowEndpointDoesNotHoldQueueLockOrBlockOtherEndpoints() throws Exception {
        pending();
        service.register(URI.create("https://example.org/hook"), Set.of(event.type()), "endpoint-2");
        service.publish(new Event("evt-2", event.type(), "payload"), "event-2");
        var sending = new CountDownLatch(1);
        var release = new CountDownLatch(1);
        var worker = new DeliveryWorker(service, delivery -> {
            sending.countDown();
            try { if (!release.await(5, TimeUnit.SECONDS)) throw new AssertionError("Timed out"); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new AssertionError(e); }
            return Delivery.Outcome.SUCCEEDED;
        });
        try (var executor = Executors.newFixedThreadPool(2)) {
            Future<?> first = executor.submit(() -> worker.runOnce("slow"));
            try {
                assertThat(sending.await(5, TimeUnit.SECONDS)).isTrue();
                assertThat(executor.submit(() -> service.claimNext("other")).get(2, TimeUnit.SECONDS)).isPresent();
            } finally { release.countDown(); }
            first.get(5, TimeUnit.SECONDS);
        }
    }

    @Test void workerUsesStableDeliveryIdentityAndTreatsTransportExceptionAsUnknown() {
        Delivery delivery = pending();
        var observed = new AtomicReference<UUID>();
        var worker = new DeliveryWorker(service, claim -> { observed.set(claim.id()); throw new IllegalStateException("timeout"); });
        assertThat(worker.runOnce("worker").orElseThrow().status()).isEqualTo(Delivery.Status.RETRY_SCHEDULED);
        assertThat(observed.get()).isEqualTo(delivery.id());
    }

    @Test void registrationAndCompletionValidateInput() {
        assertThatThrownBy(() -> service.register(URI.create("file:///tmp/test"), Set.of("event"), "x")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.register(URI.create("https://example.com"), Set.of(), "x")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.complete(UUID.randomUUID(), null, Delivery.Outcome.SUCCEEDED)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.get(UUID.randomUUID())).isInstanceOf(ApiException.class);
    }

    private static class MutableClock extends Clock {
        private Instant now = Instant.parse("2026-01-01T00:00:00Z");
        void advance(Duration duration) { now = now.plus(duration); }
        public Instant instant() { return now; }
        public ZoneId getZone() { return ZoneOffset.UTC; }
        public Clock withZone(ZoneId zone) { return Clock.fixed(now, zone); }
    }
}
