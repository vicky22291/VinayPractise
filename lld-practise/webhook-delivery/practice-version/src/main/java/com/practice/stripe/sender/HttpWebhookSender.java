package com.practice.stripe.sender;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.practice.stripe.domain.Delivery;
import java.io.IOException;
import java.net.http.*;
import java.time.Duration;
import org.springframework.stereotype.Component;

@Component
public class HttpWebhookSender implements WebhookSender {
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    private final ObjectMapper mapper;
    public HttpWebhookSender(ObjectMapper mapper) { this.mapper = mapper; }

    @Override
    public Delivery.Outcome send(Delivery delivery) {
        try {
            HttpRequest request = HttpRequest.newBuilder(delivery.destination())
                    .timeout(Duration.ofSeconds(10))
                    .header("Content-Type", "application/json")
                    .header("Webhook-Event-Id", delivery.event().id())
                    .header("Webhook-Delivery-Id", delivery.id().toString())
                    .POST(HttpRequest.BodyPublishers.ofString(mapper.writeValueAsString(delivery.event())))
                    .build();
            int status = client.send(request, HttpResponse.BodyHandlers.discarding()).statusCode();
            return status >= 200 && status < 300 ? Delivery.Outcome.SUCCEEDED : Delivery.Outcome.FAILED;
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            return Delivery.Outcome.UNKNOWN;
        } catch (IOException uncertain) {
            return Delivery.Outcome.UNKNOWN;
        }
    }
}
