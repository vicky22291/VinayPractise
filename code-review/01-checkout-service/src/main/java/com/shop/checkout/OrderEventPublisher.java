package com.shop.checkout;

/** Thin wrapper over the Kafka producer. publish() is asynchronous and returns at once. */
public interface OrderEventPublisher {
    void publish(String topic, String key, String payload);
}
