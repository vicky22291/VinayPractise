package com.shop.checkout;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Calls the card processor. The processor's POST /charges accepts an Idempotency-Key header. */
@Component
public class PaymentClient {

    private static final Logger log = LoggerFactory.getLogger(PaymentClient.class);

    private final HttpClient http = HttpClient.newHttpClient();
    private final String baseUrl;

    public PaymentClient(@Value("${payments.base-url}") String baseUrl) {
        this.baseUrl = baseUrl;
    }

    public String charge(Long customerId, String cardNumber, String cvv, double amount)
            throws PaymentDeclinedException {
        String body = "{\"customer\":" + customerId + ",\"card\":\"" + cardNumber
                + "\",\"cvv\":\"" + cvv + "\",\"amount\":" + amount + "}";

        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                HttpRequest request = HttpRequest.newBuilder(URI.create(baseUrl + "/charges"))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body))
                        .build();
                HttpResponse<String> resp = http.send(request, HttpResponse.BodyHandlers.ofString());

                if (resp.statusCode() == 200) {
                    return parseChargeId(resp.body());
                }
                if (resp.statusCode() == 402) {
                    throw new PaymentDeclinedException(resp.body());
                }
                log.warn("charge failed, attempt {}, status {}, request {}", attempt, resp.statusCode(), body);
            } catch (IOException e) {
                log.warn("charge error, retrying", e);
            } catch (InterruptedException e) {
                // ignore, we retry anyway
            }
            try {
                Thread.sleep(1000);
            } catch (InterruptedException ignored) {
            }
        }
        throw new IllegalStateException("payment failed after 3 attempts");
    }

    private String parseChargeId(String json) {
        int start = json.indexOf("\"id\":\"") + 6;
        return json.substring(start, json.indexOf('"', start));
    }

    public static class PaymentDeclinedException extends Exception {
        public PaymentDeclinedException(String reason) {
            super(reason);
        }
    }
}
