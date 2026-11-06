package com.practice.stripe.service;

import com.practice.stripe.domain.*;
import com.practice.stripe.exception.ApiException;
import com.practice.stripe.repository.DeliveryRepository;
import java.net.URI;
import java.time.Clock;
import java.time.Instant;
import java.util.*;
import org.springframework.stereotype.Service;

@Service
public class DeliveryService {
    private record Request(String operation, Object payload) {}
    private record Registration(URI destination, Set<String> eventTypes) {}
    public record Batch(List<Delivery> deliveries) {
        public Batch { deliveries = List.copyOf(deliveries); }
    }
    private final DeliveryRepository repository;
    private final Clock clock;
    private final RetryPolicy policy;
    public DeliveryService(DeliveryRepository repository, Clock clock, RetryPolicy policy) {
        this.repository = repository;
        this.clock = clock;
        this.policy = policy;
    }

    public Endpoint register(URI destination, Set<String> eventTypes, String key) {
        if (destination == null || destination.getHost() == null
                || !("http".equalsIgnoreCase(destination.getScheme()) || "https".equalsIgnoreCase(destination.getScheme())))
            throw ApiException.invalid("Destination must be an absolute HTTP(S) URL");
        if (eventTypes == null || eventTypes.isEmpty()) throw ApiException.invalid("At least one event type is required");
        eventTypes.forEach(type -> Checks.text(type, "event type"));
        Set<String> types = Set.copyOf(eventTypes);
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request("register", new Registration(destination, types)), Endpoint.class, () -> {
                    Endpoint endpoint = new Endpoint(UUID.randomUUID(), destination, types);
                    s.endpoints.put(endpoint.id(), endpoint);
                    return endpoint;
                }));
    }

    public Batch publish(Event event, String key) {
        if (event == null) throw ApiException.invalid("Event is required");
        Checks.text(event.id(), "event id");
        Checks.text(event.type(), "event type");
        return repository.transaction(s -> s.idempotency.execute(key, new Request("publish", event), Batch.class, () -> {
            Event existing = s.events.get(event.id());
            if (existing != null) {
                if (!existing.equals(event)) throw ApiException.conflict("Event ID already has a different payload");
                return new Batch(s.deliveries.values().stream().filter(d -> d.event().id().equals(event.id())).toList());
            }
            Instant now = clock.instant();
            List<Delivery> created = new ArrayList<>();
            for (Endpoint endpoint : s.endpoints.values()) {
                if (endpoint.eventTypes().contains(event.type())) {
                    created.add(new Delivery(UUID.randomUUID(), event, endpoint.id(), endpoint.destination(),
                            Delivery.Status.PENDING, 0, now, null, null, null, List.of()));
                }
            }
            s.events.put(event.id(), event);
            created.forEach(d -> s.deliveries.put(d.id(), d));
            return new Batch(created);
        }));
    }

    public Delivery get(UUID id) { return repository.transaction(s -> require(s, id)); }
    public List<Delivery> list() { return repository.transaction(s -> List.copyOf(s.deliveries.values())); }

    public Optional<Delivery> claimNext(String workerId) {
        Checks.text(workerId, "workerId");
        return repository.transaction(s -> {
            Instant now = clock.instant();
            // An expired claim is an UNKNOWN attempt, not evidence of a failed receiver-side effect.
            for (Delivery delivery : List.copyOf(s.deliveries.values())) {
                if (delivery.status() == Delivery.Status.IN_FLIGHT && !now.isBefore(delivery.leaseUntil())) {
                    Delivery recovered = delivery.finish(Delivery.Outcome.UNKNOWN, delivery.leaseUntil(),
                            delivery.leaseUntil().plus(policy.delay(delivery.attempts())), policy.maxAttempts());
                    s.deliveries.put(delivery.id(), recovered);
                }
            }
            for (Delivery delivery : s.deliveries.values()) {
                if ((delivery.status() == Delivery.Status.PENDING || delivery.status() == Delivery.Status.RETRY_SCHEDULED)
                        && !now.isBefore(delivery.nextAttemptAt())) {
                    Delivery claimed = delivery.claim(workerId, now, now.plus(policy.leaseDuration()));
                    s.deliveries.put(claimed.id(), claimed);
                    return Optional.of(claimed);
                }
            }
            return Optional.empty();
        });
    }

    public Delivery complete(UUID id, UUID leaseToken, Delivery.Outcome outcome) {
        if (leaseToken == null || outcome == null) throw ApiException.invalid("leaseToken and outcome are required");
        return repository.transaction(s -> {
            Delivery current = require(s, id);
            Instant now = clock.instant();
            if (current.status() != Delivery.Status.IN_FLIGHT || !leaseToken.equals(current.leaseToken())
                    || !now.isBefore(current.leaseUntil())) throw ApiException.conflict("Stale, expired, or completed claim");
            Delivery next = current.finish(outcome, now, now.plus(policy.delay(current.attempts())), policy.maxAttempts());
            s.deliveries.put(id, next);
            return next;
        });
    }

    private Delivery require(DeliveryRepository.State state, UUID id) {
        Delivery delivery = state.deliveries.get(id);
        if (delivery == null) throw ApiException.missing("Delivery not found");
        return delivery;
    }
}
