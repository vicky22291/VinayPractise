package com.practice.stripe;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.*;

/** Full application wiring: all mutations and reads go through MockMvc, with no mocked beans. */
@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
class FullStackApiTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    private MockMvcTestClient api;
    @BeforeEach void client() { api = new MockMvcTestClient(mvc, mapper); }
    private String key() { return UUID.randomUUID().toString(); }

    private String create(long amount) {
        return api.expect("POST", "/payments", Map.of("amount", amount, "currency", "usd"), key(), 201).get("id").asText();
    }
    private String authorized(long amount) {
        String id = create(amount);
        api.expect("POST", "/payments/" + id + "/authorize", null, key(), 200);
        return id;
    }

    @Test void invalidTransitionsPreserveStoredPaymentAndRejectedKeyCanBeRetried() {
        String id = create(1000);
        String path = "/payments/" + id;
        JsonNode original = api.get(path);
        String captureKey = key();
        api.expect("POST", path + "/captures", Map.of("amount", 1000), captureKey, 409);
        assertThat(api.get(path)).isEqualTo(original);
        api.expect("POST", path + "/authorize", null, key(), 200);
        api.expect("POST", path + "/captures", Map.of("amount", 1000), captureKey, 201);
        JsonNode captured = api.get(path);
        assertThat(captured.get("capturedAmount").asLong()).isEqualTo(1000);
        api.expect("POST", path + "/cancel", null, key(), 409);
        api.expect("POST", path + "/authorize", null, key(), 409);
        assertThat(api.get(path)).isEqualTo(captured);
    }

    @Test void cancellationIsPersistedAndPreventsAuthorizationAndCapture() {
        for (boolean authorizeFirst : new boolean[]{false, true}) {
            String id = authorizeFirst ? authorized(1000) : create(1000);
            String path = "/payments/" + id;
            String cancelKey = key();
            JsonNode canceled = api.expect("POST", path + "/cancel", null, cancelKey, 200);
            assertThat(canceled.get("status").asText()).isEqualTo("CANCELED");
            assertThat(api.expect("POST", path + "/cancel", null, cancelKey, 200)).isEqualTo(canceled);
            api.expect("POST", path + "/authorize", null, key(), 409);
            api.expect("POST", path + "/captures", Map.of("amount", 1), key(), 409);
            assertThat(api.get(path)).isEqualTo(canceled);
            assertThat(api.get(path + "/captures")).isEmpty();
        }
    }

    @Test void partialCaptureFailureDoesNotAlterDataAndReplayKeepsOriginalSnapshot() {
        String id = authorized(1000);
        String path = "/payments/" + id;
        String captureKey = key();
        JsonNode first = api.expect("POST", path + "/captures", Map.of("amount", 400), captureKey, 201);
        JsonNode partial = api.get(path);
        assertThat(partial.get("status").asText()).isEqualTo("PARTIALLY_CAPTURED");
        api.expect("POST", path + "/captures", Map.of("amount", 601), key(), 409);
        api.expect("POST", path + "/captures", Map.of("amount", 401), captureKey, 409);
        api.expect("POST", path + "/cancel", null, captureKey, 409);
        assertThat(api.get(path)).isEqualTo(partial);
        assertThat(api.get(path + "/captures")).hasSize(1);
        api.expect("POST", path + "/captures", Map.of(), key(), 201);
        assertThat(api.expect("POST", path + "/captures", Map.of("amount", 400), captureKey, 201)).isEqualTo(first);
        assertThat(api.get(path).get("capturedAmount").asLong()).isEqualTo(1000);
        assertThat(api.get(path + "/captures")).hasSize(2);
    }

    @Test void concurrentHttpCapturesCannotExceedAuthorization() throws Exception {
        String id = authorized(1000);
        String path = "/payments/" + id;
        var statuses = Concurrently.run(10, i -> api.send("POST", path + "/captures", Map.of("amount", 200), key()).status());
        assertThat(statuses.stream().filter(s -> s == 201).count()).isEqualTo(5);
        assertThat(statuses.stream().filter(s -> s == 409).count()).isEqualTo(5);
        assertThat(api.get(path).get("capturedAmount").asLong()).isEqualTo(1000);
        assertThat(api.get(path).get("reservedAmount").asLong()).isZero();
        assertThat(api.get(path + "/captures")).hasSize(5);
    }

    @Test void concurrentSameKeyHttpRetriesStoreExactlyOneCapture() throws Exception {
        String id = authorized(1000);
        String path = "/payments/" + id;
        String captureKey = key();
        var replies = Concurrently.run(10, i -> api.expect("POST", path + "/captures", Map.of("amount", 200), captureKey, 201));
        assertThat(replies).allMatch(replies.getFirst()::equals);
        assertThat(api.get(path).get("capturedAmount").asLong()).isEqualTo(200);
        assertThat(api.get(path + "/captures")).hasSize(1);
    }
}
