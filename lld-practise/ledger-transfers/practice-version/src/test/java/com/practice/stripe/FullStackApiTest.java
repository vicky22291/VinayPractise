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

    private String account(String currency, long balance) {
        return api.expect("POST", "/accounts", Map.of("currency", currency, "openingBalance", balance), key(), 201).get("id").asText();
    }
    private Map<String, Object> move(String from, String to, long amount) {
        return Map.of("sourceId", from, "destinationId", to, "amount", amount);
    }
    private void balance(String id, long expected) {
        assertThat(api.get("/accounts/" + id).get("balance").asLong()).isEqualTo(expected);
        JsonNode audit = api.get("/accounts/" + id + "/audit");
        assertThat(audit.get("consistent").asBoolean()).isTrue();
        assertThat(audit.get("rebuiltBalance").asLong()).isEqualTo(expected);
    }
    private List<JsonNode> entries(String transferId) {
        List<JsonNode> entries = new ArrayList<>();
        api.get("/entries").forEach(e -> { if (e.get("transferId").asText().equals(transferId)) entries.add(e); });
        return entries;
    }

    @Test void transferAndReversalPersistBalancedImmutableEntriesAndReplayOriginalResults() {
        String source = account("USD", 1000), destination = account("usd", 0);
        String transferKey = key();
        var request = move(source, destination, 400);
        JsonNode transfer = api.expect("POST", "/transfers", request, transferKey, 201);
        String id = transfer.get("id").asText();
        balance(source, 600); balance(destination, 400);
        var originalEntries = entries(id);
        assertThat(originalEntries).hasSize(2);
        assertThat(originalEntries.stream().mapToLong(e -> e.get("amount").asLong()).sum()).isZero();
        String reverseKey = key();
        JsonNode reversal = api.expect("POST", "/transfers/" + id + "/reversals", null, reverseKey, 201);
        String reversalId = reversal.get("id").asText();
        assertThat(reversal.get("reversalOf").asText()).isEqualTo(id);
        assertThat(api.get("/transfers/" + id).get("reversedBy").asText()).isEqualTo(reversalId);
        assertThat(entries(id)).isEqualTo(originalEntries);
        assertThat(entries(reversalId)).hasSize(2);
        assertThat(entries(reversalId).stream().mapToLong(e -> e.get("amount").asLong()).sum()).isZero();
        assertThat(api.expect("POST", "/transfers", request, transferKey, 201)).isEqualTo(transfer);
        assertThat(api.expect("POST", "/transfers/" + id + "/reversals", null, reverseKey, 201)).isEqualTo(reversal);
        api.expect("POST", "/transfers/" + id + "/reversals", null, key(), 409);
        api.expect("POST", "/transfers/" + reversalId + "/reversals", null, key(), 409);
        balance(source, 1000); balance(destination, 0);
    }

    @Test void rejectedTransfersIncludingOverflowChangeNoBalancesOrHistory() {
        String source = account("USD", 1000), destination = account("USD", 0);
        String eur = account("EUR", 0), full = account("USD", Long.MAX_VALUE);
        JsonNode before = api.get("/entries");
        api.expect("POST", "/transfers", move(source, destination, 1001), key(), 409);
        api.expect("POST", "/transfers", move(source, eur, 1), key(), 400);
        api.expect("POST", "/transfers", move(source, source, 1), key(), 400);
        api.expect("POST", "/transfers", move(source, full, 1), key(), 400);
        api.expect("POST", "/transfers", move(source, key(), 1), key(), 404);
        balance(source, 1000); balance(destination, 0); balance(eur, 0); balance(full, Long.MAX_VALUE);
        assertThat(api.get("/entries")).isEqualTo(before);
    }

    @Test void unfundedReversalCanRetryItsRejectedKeyAfterFundsReturn() {
        String source = account("USD", 1000), destination = account("USD", 0);
        String id = api.expect("POST", "/transfers", move(source, destination, 400), key(), 201).get("id").asText();
        api.expect("POST", "/transfers", move(destination, source, 400), key(), 201);
        String reversalKey = key();
        JsonNode history = api.get("/entries");
        api.expect("POST", "/transfers/" + id + "/reversals", null, reversalKey, 409);
        assertThat(api.get("/transfers/" + id).get("reversedBy").isNull()).isTrue();
        assertThat(api.get("/entries")).isEqualTo(history);
        balance(source, 1000); balance(destination, 0);
        api.expect("POST", "/transfers", move(source, destination, 400), key(), 201);
        api.expect("POST", "/transfers/" + id + "/reversals", null, reversalKey, 201);
        balance(source, 1000); balance(destination, 0);
    }

    @Test void concurrentHttpTransfersPreserveFundsAndAudit() throws Exception {
        String source = account("USD", 1000), destination = account("USD", 0);
        var statuses = Concurrently.run(20, i -> api.send("POST", "/transfers", move(source, destination, 100), key()).status());
        assertThat(statuses.stream().filter(s -> s == 201).count()).isEqualTo(10);
        assertThat(statuses.stream().filter(s -> s == 409).count()).isEqualTo(10);
        balance(source, 0); balance(destination, 1000);
    }

    @Test void competingHttpReversalsAppendOnlyOneCorrection() throws Exception {
        String source = account("USD", 1000), destination = account("USD", 0);
        String id = api.expect("POST", "/transfers", move(source, destination, 400), key(), 201).get("id").asText();
        var statuses = Concurrently.run(10, i -> api.send("POST", "/transfers/" + id + "/reversals", null, key()).status());
        assertThat(statuses.stream().filter(s -> s == 201).count()).isEqualTo(1);
        assertThat(statuses.stream().filter(s -> s == 409).count()).isEqualTo(9);
        balance(source, 1000); balance(destination, 0);
        assertThat(entries(api.get("/transfers/" + id).get("reversedBy").asText())).hasSize(2);
    }

    @Test void sameKeyHttpTransfersExecuteOnceAndConflictingPayloadIsRejected() throws Exception {
        String source = account("USD", 1000), destination = account("USD", 0), requestKey = key();
        var replies = Concurrently.run(10, i -> api.expect("POST", "/transfers", move(source, destination, 400), requestKey, 201));
        assertThat(replies).allMatch(replies.getFirst()::equals);
        api.expect("POST", "/transfers", move(source, destination, 401), requestKey, 409);
        balance(source, 600); balance(destination, 400);
        assertThat(entries(replies.getFirst().get("id").asText())).hasSize(2);
    }
}
