package com.practice.stripe;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/** Real application beans; JSON goes through validation, controller, parser and matching indexes. */
@SpringBootTest
@AutoConfigureMockMvc
class FullStackApiTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;

    @Test void allStagesReturnOrderedAuditableResultsAndRetriesAreBatchLocal() throws Exception {
        var body = Map.of("payments", List.of("p1,1,INV-12, thanks", "p2,500,", "p3,500,", "p4,500,"),
                "invoices", List.of("INV-1,500,2026-11-10", "INV-12,700,2026-11-12", "INV-2,505,2026-11-01"),
                "tolerance", 5);
        JsonNode first = success(body);
        JsonNode results = first.get("results");
        assertThat(results).hasSize(4);
        assertThat(results.get(0).get("payment").get("id").asText()).isEqualTo("p1");
        assertThat(results.get(0).get("payment").get("memo").asText()).isEqualTo("INV-12, thanks");
        assertThat(results.get(0).get("invoice").get("id").asText()).isEqualTo("INV-12");
        assertThat(results.get(0).get("invoice").get("amount").asLong()).isEqualTo(700);
        assertThat(results.get(0).get("invoice").get("dueDate").asText()).isEqualTo("2026-11-12");
        assertThat(results.get(0).get("rule").asText()).isEqualTo("MEMO");
        assertThat(results.get(1).get("rule").asText()).isEqualTo("EXACT_AMOUNT");
        assertThat(results.get(1).get("invoice").get("id").asText()).isEqualTo("INV-1");
        assertThat(results.get(2).get("rule").asText()).isEqualTo("TOLERANCE");
        assertThat(results.get(2).get("invoice").get("id").asText()).isEqualTo("INV-2");
        assertThat(results.get(3).get("rule").asText()).isEqualTo("NONE");
        assertThat(results.get(3).get("invoice").isNull()).isTrue();
        assertThat(success(body)).isEqualTo(first);
    }

    @Test void stageSelectionAndDefaultZeroToleranceAreHonored() throws Exception {
        for (String stage : List.of("MEMO_ONLY", "EXACT_AMOUNT", "TOLERANCE")) {
            JsonNode results = success(Map.of("payments", List.of("p1,100,", "p2,100,"),
                    "invoices", List.of("INV-1,100,2026-11-01", "INV-2,101,2026-11-01"),
                    "stage", stage, "tolerance", 1)).get("results");
            assertThat(results.get(0).get("rule").asText()).isEqualTo(stage.equals("MEMO_ONLY") ? "NONE" : "EXACT_AMOUNT");
            assertThat(results.get(1).get("rule").asText()).isEqualTo(stage.equals("TOLERANCE") ? "TOLERANCE" : "NONE");
        }
        var defaults = success(Map.of("payments", List.of("p1,100,", "p2,100,"),
                "invoices", List.of("INV-1,100,2026-11-01", "INV-2,101,2026-11-01"))).get("results");
        assertThat(defaults.get(0).get("rule").asText()).isEqualTo("EXACT_AMOUNT");
        assertThat(defaults.get(1).get("rule").asText()).isEqualTo("NONE");
        assertThat(success(Map.of("payments", List.of(), "invoices", List.of())).get("results")).isEmpty();
    }

    @Test void badRowsReturnActionableErrorsAndNextBatchStillWorks() throws Exception {
        mvc.perform(post("/reconciliations").contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsBytes(
                        Map.of("payments", List.of("p,100,INV-1", "broken"), "invoices", List.of("INV-1,100,2026-11-01")))))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("payment row 2: expected <payment_id>,<amount_minor>,<memo>"));
        assertThat(success(Map.of("payments", List.of("p,100,INV-1"),
                "invoices", List.of("INV-1,100,2026-11-01"))).get("results").get(0).get("rule").asText()).isEqualTo("MEMO");
    }

    @Test void invalidJsonMissingListsEnumsAndToleranceReturn400() throws Exception {
        for (String body : List.of("{", "{}", "null", "{\"payments\":null,\"invoices\":[]}",
                "{\"payments\":[],\"invoices\":[],\"stage\":\"UNKNOWN\"}",
                "{\"payments\":[],\"invoices\":[],\"tolerance\":-1}",
                "{\"payments\":[],\"invoices\":[],\"tolerance\":1.5}",
                "{\"payments\":[],\"invoices\":[],\"tolerance\":9223372036854775808}",
                "{\"payments\":[null],\"invoices\":[]}",
                "{\"payments\":[],\"invoices\":[\"INV-1,100,2026-02-30\"]}")) {
            mvc.perform(post("/reconciliations").contentType(MediaType.APPLICATION_JSON).content(body))
                    .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error").isString());
        }
    }

    private JsonNode success(Object body) throws Exception {
        var response = mvc.perform(post("/reconciliations").contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsBytes(body)))
                .andExpect(status().isOk()).andReturn().getResponse();
        return mapper.readTree(response.getContentAsString());
    }
}
