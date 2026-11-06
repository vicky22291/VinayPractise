package com.practice.stripe.domain;

import java.net.URI;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public record Delivery(UUID id, Event event, UUID endpointId, URI destination, Status status,
                       int attempts, Instant nextAttemptAt, String workerId, UUID leaseToken,
                       Instant leaseUntil, List<Attempt> history) {
    public enum Status { PENDING, IN_FLIGHT, RETRY_SCHEDULED, DELIVERED, DEAD }
    public enum Outcome { SUCCEEDED, FAILED, UNKNOWN }
    public record Attempt(int number, UUID token, Instant startedAt, Instant finishedAt, Outcome outcome) {}
    public Delivery { history = List.copyOf(history); }

    public Delivery claim(String worker, Instant now, Instant until) {
        UUID token = UUID.randomUUID();
        var nextHistory = new ArrayList<>(history);
        nextHistory.add(new Attempt(attempts + 1, token, now, null, Outcome.UNKNOWN));
        return new Delivery(id, event, endpointId, destination, Status.IN_FLIGHT, attempts + 1,
                null, worker, token, until, nextHistory);
    }

    public Delivery finish(Outcome outcome, Instant now, Instant retryAt, int maxAttempts) {
        var nextHistory = new ArrayList<>(history);
        Attempt active = nextHistory.getLast();
        nextHistory.set(nextHistory.size() - 1, new Attempt(active.number(), active.token(), active.startedAt(), now, outcome));
        Status next = outcome == Outcome.SUCCEEDED ? Status.DELIVERED
                : attempts >= maxAttempts ? Status.DEAD : Status.RETRY_SCHEDULED;
        return new Delivery(id, event, endpointId, destination, next, attempts,
                next == Status.RETRY_SCHEDULED ? retryAt : null, null, null, null, nextHistory);
    }
}
