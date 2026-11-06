package com.practice.stripe.web;

import com.practice.stripe.domain.*;
import com.practice.stripe.service.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.net.URI;
import java.util.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
public class DeliveryController {
    public record EndpointRequest(@NotNull URI destination, @NotEmpty Set<@NotBlank String> eventTypes) {}
    public record EventRequest(@NotBlank String id, @NotBlank String type, String payload) {}
    public record WorkerRequest(@NotBlank String workerId) {}
    public record CompletionRequest(@NotNull UUID leaseToken, @NotNull Delivery.Outcome outcome) {}
    private final DeliveryService service;
    private final DeliveryWorker worker;
    public DeliveryController(DeliveryService service, DeliveryWorker worker) { this.service = service; this.worker = worker; }

    @PostMapping("/endpoints")
    @ResponseStatus(HttpStatus.CREATED)
    public Endpoint register(@Valid @RequestBody EndpointRequest request, @RequestHeader("Idempotency-Key") String key) {
        return service.register(request.destination(), request.eventTypes(), key);
    }
    @PostMapping("/events")
    @ResponseStatus(HttpStatus.CREATED)
    public DeliveryService.Batch publish(@Valid @RequestBody EventRequest request, @RequestHeader("Idempotency-Key") String key) {
        return service.publish(new Event(request.id(), request.type(), request.payload()), key);
    }
    @GetMapping("/deliveries")
    public List<Delivery> list() { return service.list(); }
    @GetMapping("/deliveries/{id}")
    public Delivery get(@PathVariable UUID id) { return service.get(id); }
    @PostMapping("/deliveries/claim")
    public ResponseEntity<Delivery> claim(@Valid @RequestBody WorkerRequest request) {
        return service.claimNext(request.workerId()).map(ResponseEntity::ok).orElseGet(() -> ResponseEntity.noContent().build());
    }
    @PostMapping("/deliveries/{id}/attempts")
    public Delivery complete(@PathVariable UUID id, @Valid @RequestBody CompletionRequest request) {
        return service.complete(id, request.leaseToken(), request.outcome());
    }
    @PostMapping("/workers/run-once")
    public ResponseEntity<Delivery> runOnce(@Valid @RequestBody WorkerRequest request) {
        return worker.runOnce(request.workerId()).map(ResponseEntity::ok).orElseGet(() -> ResponseEntity.noContent().build());
    }
}
