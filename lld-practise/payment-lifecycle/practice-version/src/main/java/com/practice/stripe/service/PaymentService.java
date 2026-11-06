package com.practice.stripe.service;

import com.practice.stripe.domain.Capture;
import com.practice.stripe.domain.Checks;
import com.practice.stripe.domain.Payment;
import com.practice.stripe.exception.ApiException;
import com.practice.stripe.processor.CaptureProcessor;
import com.practice.stripe.repository.PaymentRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class PaymentService {
    private record Request(String operation, UUID target, Object payload) {}
    private record Create(long amount, String currency) {}
    private final PaymentRepository repository;
    private final CaptureProcessor processor;

    public PaymentService(PaymentRepository repository, CaptureProcessor processor) {
        this.repository = repository;
        this.processor = processor;
    }

    public Payment create(long amount, String currency, String key) {
        Checks.positive(amount, "amount");
        String normalized = Checks.currency(currency);
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request("create", null, new Create(amount, normalized)), Payment.class, () -> {
                    Payment payment = new Payment(UUID.randomUUID(), amount, normalized, Payment.Status.CREATED, 0, 0);
                    s.payments.put(payment.id(), payment);
                    return payment;
                }));
    }

    public Payment get(UUID id) { return repository.transaction(s -> require(s, id)); }

    public Payment authorize(UUID id, String key) { return transition(id, key, true); }
    public Payment cancel(UUID id, String key) { return transition(id, key, false); }

    private Payment transition(UUID id, String key, boolean authorize) {
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request(authorize ? "authorize" : "cancel", id, null), Payment.class, () -> {
                    Payment current = require(s, id);
                    Payment next = authorize ? current.authorize() : current.cancel();
                    s.payments.put(id, next);
                    return next;
                }));
    }

    /** A null amount captures all remaining unreserved authorization (the stage-one API). */
    public Capture capture(UUID id, Long amount, String key) {
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request("capture", id, amount), Capture.class, () -> {
                    Payment payment = require(s, id);
                    long wanted = amount == null ? payment.amount() - payment.capturedAmount() - payment.reservedAmount() : amount;
                    Payment reserved = payment.reserve(wanted);
                    Capture capture = new Capture(UUID.randomUUID(), id, wanted, payment.currency(), Capture.Status.UNKNOWN);
                    // Persist the operation ID and reservation before crossing the processor boundary.
                    s.payments.put(id, reserved);
                    s.captures.put(capture.id(), capture);
                    return resolve(s, capture);
                }));
    }

    public List<Capture> captures(UUID id) {
        return repository.transaction(s -> {
            require(s, id);
            return s.captures.values().stream().filter(c -> c.paymentId().equals(id)).toList();
        });
    }

    /** A fresh reconciliation key observes progress; replaying an old key returns its original snapshot. */
    public Capture reconcile(UUID paymentId, UUID captureId, String key) {
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request("reconcile", paymentId, captureId), Capture.class, () -> {
                    require(s, paymentId);
                    Capture capture = s.captures.get(captureId);
                    if (capture == null || !capture.paymentId().equals(paymentId))
                        throw ApiException.missing("Capture not found");
                    return capture.status() == Capture.Status.UNKNOWN ? resolve(s, capture) : capture;
                }));
    }

    private Capture resolve(PaymentRepository.State state, Capture capture) {
        CaptureProcessor.Outcome outcome;
        try {
            outcome = processor.capture(new CaptureProcessor.Command(capture.id(), capture.paymentId(), capture.amount(), capture.currency()));
        } catch (RuntimeException uncertain) {
            // A network exception cannot establish whether the processor charged the customer.
            outcome = CaptureProcessor.Outcome.UNKNOWN;
        }
        if (outcome == CaptureProcessor.Outcome.UNKNOWN) return capture;
        boolean succeeded = outcome == CaptureProcessor.Outcome.SUCCEEDED;
        Capture next = capture.withStatus(succeeded ? Capture.Status.SUCCEEDED : Capture.Status.DECLINED);
        state.payments.put(capture.paymentId(), require(state, capture.paymentId()).resolve(capture.amount(), succeeded));
        state.captures.put(capture.id(), next);
        return next;
    }

    private Payment require(PaymentRepository.State state, UUID id) {
        Payment payment = state.payments.get(id);
        if (payment == null) throw ApiException.missing("Payment not found");
        return payment;
    }
}
