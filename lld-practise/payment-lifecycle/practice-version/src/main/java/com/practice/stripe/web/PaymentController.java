package com.practice.stripe.web;

import com.practice.stripe.domain.Capture;
import com.practice.stripe.domain.Payment;
import com.practice.stripe.service.PaymentService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/payments")
public class PaymentController {
    public record CreateRequest(@Positive long amount, @NotBlank String currency) {}
    public record CaptureRequest(@Positive Long amount) {}
    private final PaymentService service;
    public PaymentController(PaymentService service) { this.service = service; }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Payment create(@Valid @RequestBody CreateRequest request, @RequestHeader("Idempotency-Key") String key) {
        return service.create(request.amount(), request.currency(), key);
    }
    @GetMapping("/{id}")
    public Payment get(@PathVariable UUID id) { return service.get(id); }
    @PostMapping("/{id}/authorize")
    public Payment authorize(@PathVariable UUID id, @RequestHeader("Idempotency-Key") String key) { return service.authorize(id, key); }
    @PostMapping("/{id}/cancel")
    public Payment cancel(@PathVariable UUID id, @RequestHeader("Idempotency-Key") String key) { return service.cancel(id, key); }
    @PostMapping("/{id}/captures")
    @ResponseStatus(HttpStatus.CREATED)
    public Capture capture(@PathVariable UUID id, @Valid @RequestBody CaptureRequest request,
                           @RequestHeader("Idempotency-Key") String key) { return service.capture(id, request.amount(), key); }
    @GetMapping("/{id}/captures")
    public List<Capture> captures(@PathVariable UUID id) { return service.captures(id); }
    @PostMapping("/{id}/captures/{captureId}/reconcile")
    public Capture reconcile(@PathVariable UUID id, @PathVariable UUID captureId, @RequestHeader("Idempotency-Key") String key) {
        return service.reconcile(id, captureId, key);
    }
}
