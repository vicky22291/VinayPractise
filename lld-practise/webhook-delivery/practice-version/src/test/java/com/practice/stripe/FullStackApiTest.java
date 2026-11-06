package com.practice.stripe;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.*;

/** Real Spring beans throughout, including the HTTP sender; only the customer receiver is a local server. */
@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
class FullStackApiTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    private MockMvcTestClient api;
    private HttpServer receiver;
    private ExecutorService receiverThreads;
    private final List<Received> received = new CopyOnWriteArrayList<>();
    private record Received(JsonNode event, String eventId, String deliveryId, String contentType) {}
    private record Published(String eventId, String deliveryId, JsonNode original, Map<String, Object> request) {}

    @BeforeEach void client() { api = new MockMvcTestClient(mvc, mapper); }
    @AfterEach void stopReceiver() {
        if (receiver != null) receiver.stop(0);
        if (receiverThreads != null) receiverThreads.shutdownNow();
    }
    private String key() { return UUID.randomUUID().toString(); }

    private String startReceiver(String mode) throws Exception {
        receiver = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        receiverThreads = Executors.newCachedThreadPool();
        receiver.setExecutor(receiverThreads);
        receiver.createContext("/hook", exchange -> {
            try (exchange) {
                received.add(new Received(mapper.readTree(exchange.getRequestBody()),
                        exchange.getRequestHeaders().getFirst("Webhook-Event-Id"),
                        exchange.getRequestHeaders().getFirst("Webhook-Delivery-Id"),
                        exchange.getRequestHeaders().getFirst("Content-Type")));
                int attempt = received.size();
                if (mode.equals("timeout") && attempt == 1) {
                    try { Thread.sleep(10_500); }
                    catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); return; }
                }
                int code = mode.equals("flaky") && attempt == 1 ? 503 : 204;
                exchange.sendResponseHeaders(code, -1);
            } catch (java.io.IOException disconnected) {
                // A timed-out sender may disconnect after the receiver has accepted the event.
            }
        });
        receiver.start();
        return "http://127.0.0.1:" + receiver.getAddress().getPort() + "/hook";
    }

    private Published publish(String destination) {
        String type = "payment." + key(), eventId = key();
        api.expect("POST", "/endpoints", Map.of("destination", destination, "eventTypes", List.of(type)), key(), 201);
        var request = Map.<String, Object>of("id", eventId, "type", type, "payload", "actual-data");
        JsonNode batch = api.expect("POST", "/events", request, key(), 201);
        assertThat(batch.get("deliveries")).hasSize(1);
        JsonNode delivery = batch.get("deliveries").get(0);
        return new Published(eventId, delivery.get("id").asText(), delivery, request);
    }
    private JsonNode claim(int expected) { return api.expect("POST", "/deliveries/claim", Map.of("workerId", key()), null, expected); }
    private JsonNode complete(String id, String token, String outcome, int expected) {
        return api.expect("POST", "/deliveries/" + id + "/attempts", Map.of("leaseToken", token, "outcome", outcome), null, expected);
    }
    private JsonNode send() { return api.expect("POST", "/workers/run-once", Map.of("workerId", key()), null, 200); }
    private JsonNode stored(Published published) { return api.get("/deliveries/" + published.deliveryId()); }
    private void waitUntil(Instant target) throws InterruptedException {
        long remaining = Duration.between(Instant.now(), target).toMillis();
        if (remaining >= 0) Thread.sleep(remaining + 50);
    }
    private void waitForRetry(JsonNode delivery) throws InterruptedException { waitUntil(Instant.parse(delivery.get("nextAttemptAt").asText())); }

    @Test void matchingEndpointReceivesActualHttpJsonAndPersistedAttempt() throws Exception {
        Published published = publish(startReceiver("success"));
        JsonNode done = send();
        assertThat(done.get("status").asText()).isEqualTo("DELIVERED");
        assertThat(stored(published)).isEqualTo(done);
        assertThat(done.get("attempts").asInt()).isEqualTo(1);
        assertThat(done.get("history").get(0).get("outcome").asText()).isEqualTo("SUCCEEDED");
        assertThat(received).hasSize(1);
        assertThat(received.getFirst().event()).isEqualTo(mapper.valueToTree(published.request()));
        assertThat(received.getFirst().eventId()).isEqualTo(published.eventId());
        assertThat(received.getFirst().deliveryId()).isEqualTo(published.deliveryId());
        assertThat(received.getFirst().contentType()).isEqualTo("application/json");
        claim(204);
    }

    @Test void actual503ResponseSchedulesRetryAndSecondHttpAttemptUsesSameIdentity() throws Exception {
        Published published = publish(startReceiver("flaky"));
        JsonNode retry = send();
        assertThat(retry.get("status").asText()).isEqualTo("RETRY_SCHEDULED");
        assertThat(retry.get("history").get(0).get("outcome").asText()).isEqualTo("FAILED");
        claim(204);
        waitForRetry(retry);
        JsonNode done = send();
        assertThat(done.get("status").asText()).isEqualTo("DELIVERED");
        assertThat(stored(published).get("history")).hasSize(2);
        assertThat(received).hasSize(2);
        assertThat(received.get(0)).isEqualTo(received.get(1));
    }

    @Test void realSenderTimeoutIsUnknownAndRetryPreservesAcceptedEventIdentity() throws Exception {
        Published published = publish(startReceiver("timeout"));
        JsonNode retry = send(); // real HttpClient timeout after the receiver reads the event
        assertThat(retry.get("status").asText()).isEqualTo("RETRY_SCHEDULED");
        assertThat(retry.get("history").get(0).get("outcome").asText()).isEqualTo("UNKNOWN");
        assertThat(received).hasSize(1);
        waitForRetry(retry);
        JsonNode done = send();
        assertThat(done.get("status").asText()).isEqualTo("DELIVERED");
        assertThat(stored(published).get("attempts").asInt()).isEqualTo(2);
        assertThat(received).hasSize(2);
        assertThat(received.get(0)).isEqualTo(received.get(1));
    }

    @Test void boundedRetryPolicyAndUnknownHistoryArePersistedThroughRequestFlow() throws Exception {
        Published published = publish("http://127.0.0.1:1/unused");
        for (int attempt = 1; attempt <= 3; attempt++) {
            JsonNode claimed = claim(200);
            JsonNode result = complete(published.deliveryId(), claimed.get("leaseToken").asText(), attempt == 1 ? "UNKNOWN" : "FAILED", 200);
            assertThat(stored(published)).isEqualTo(result);
            assertThat(result.get("attempts").asInt()).isEqualTo(attempt);
            if (attempt < 3) {
                assertThat(result.get("status").asText()).isEqualTo("RETRY_SCHEDULED");
                claim(204);
                waitForRetry(result);
            } else assertThat(result.get("status").asText()).isEqualTo("DEAD");
        }
        assertThat(stored(published).get("history")).hasSize(3);
        claim(204);
    }

    @Test void workerCrashExpiresActualLeaseAndOldTokenCannotOverwriteRecovery() throws Exception {
        Published published = publish("http://127.0.0.1:1/unused");
        JsonNode crashed = claim(200);
        String staleToken = crashed.get("leaseToken").asText();
        claim(204);
        waitUntil(Instant.parse(crashed.get("leaseUntil").asText()).plusMillis(1100));
        JsonNode recovered = claim(200);
        assertThat(recovered.get("id").asText()).isEqualTo(published.deliveryId());
        assertThat(recovered.get("attempts").asInt()).isEqualTo(2);
        assertThat(recovered.get("leaseToken").asText()).isNotEqualTo(staleToken);
        assertThat(recovered.get("history").get(0).get("outcome").asText()).isEqualTo("UNKNOWN");
        complete(published.deliveryId(), staleToken, "SUCCEEDED", 409);
        assertThat(stored(published)).isEqualTo(recovered);
        JsonNode done = complete(published.deliveryId(), recovered.get("leaseToken").asText(), "SUCCEEDED", 200);
        assertThat(done.get("status").asText()).isEqualTo("DELIVERED");
        complete(published.deliveryId(), recovered.get("leaseToken").asText(), "FAILED", 409);
        assertThat(stored(published)).isEqualTo(done);
    }

    @Test void concurrentMockMvcWorkersClaimOnceWithoutMockingQueueOrService() throws Exception {
        Published published = publish("http://127.0.0.1:1/unused");
        var responses = Concurrently.run(10, i -> api.send("POST", "/deliveries/claim", Map.of("workerId", key()), null));
        assertThat(responses.stream().filter(r -> r.status() == 200).count()).isEqualTo(1);
        assertThat(responses.stream().filter(r -> r.status() == 204).count()).isEqualTo(9);
        JsonNode claimed = responses.stream().filter(r -> r.status() == 200).findFirst().orElseThrow().body();
        assertThat(stored(published).get("attempts").asInt()).isEqualTo(1);
        complete(published.deliveryId(), claimed.get("leaseToken").asText(), "SUCCEEDED", 200);
    }

    @Test void republishingEventChecksPayloadAndDoesNotDuplicateStoredFanout() {
        Published published = publish("http://127.0.0.1:1/unused");
        JsonNode replay = api.expect("POST", "/events", published.request(), key(), 201);
        assertThat(replay.get("deliveries")).hasSize(1);
        assertThat(replay.get("deliveries").get(0)).isEqualTo(published.original());
        var changed = new HashMap<>(published.request());
        changed.put("payload", "different");
        api.expect("POST", "/events", changed, key(), 409);
        assertThat(stored(published)).isEqualTo(published.original());
        JsonNode claimed = claim(200);
        complete(published.deliveryId(), claimed.get("leaseToken").asText(), "SUCCEEDED", 200);
        claim(204);
    }
}
