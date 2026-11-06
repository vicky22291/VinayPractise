package com.practice.stripe.sender;

import com.practice.stripe.domain.Delivery;

@FunctionalInterface
public interface WebhookSender {
    Delivery.Outcome send(Delivery delivery);
}
