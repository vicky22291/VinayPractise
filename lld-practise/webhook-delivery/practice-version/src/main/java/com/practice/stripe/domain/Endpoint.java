package com.practice.stripe.domain;

import java.net.URI;
import java.util.Set;
import java.util.UUID;

public record Endpoint(UUID id, URI destination, Set<String> eventTypes) {
    public Endpoint { eventTypes = Set.copyOf(eventTypes); }
}
