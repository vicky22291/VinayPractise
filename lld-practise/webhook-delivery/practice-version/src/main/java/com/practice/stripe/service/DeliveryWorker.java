package com.practice.stripe.service;

import com.practice.stripe.domain.Delivery;
import com.practice.stripe.sender.WebhookSender;
import java.util.Optional;
import org.springframework.stereotype.Service;

@Service
public class DeliveryWorker {
    private final DeliveryService service;
    private final WebhookSender sender;
    public DeliveryWorker(DeliveryService service, WebhookSender sender) { this.service = service; this.sender = sender; }

    /** Network I/O happens outside the repository lock, so one slow customer cannot hold the queue lock. */
    public Optional<Delivery> runOnce(String workerId) {
        return service.claimNext(workerId).map(claim -> {
            Delivery.Outcome outcome;
            try { outcome = sender.send(claim); }
            catch (RuntimeException uncertain) { outcome = Delivery.Outcome.UNKNOWN; }
            return service.complete(claim.id(), claim.leaseToken(), outcome);
        });
    }
}
