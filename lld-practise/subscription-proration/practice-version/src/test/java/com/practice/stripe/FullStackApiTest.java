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

    private Map<String, Object> plan(long price, long quantity) { return Map.of("price", price, "quantity", quantity); }
    private Map<String, Object> change(String at, long price, long quantity) { return Map.of("at", at, "plan", plan(price, quantity)); }
    private Map<String, Object> request(long oldPrice, List<?> changes, int discount) {
        return Map.of("currency", "usd", "start", "2026-01-01T00:00:00Z", "end", "2026-01-31T00:00:00Z",
                "initial", plan(oldPrice, 1), "changes", changes, "discountBasisPoints", discount);
    }
    private JsonNode calculate(Map<String, Object> request) { return api.expect("POST", "/prorations", request, null, 200); }

    @Test void stageOneCalculatesUpgradeDowngradeAndSignedHalfRounding() {
        String middle = "2026-01-16T00:00:00Z";
        assertThat(calculate(request(2000, List.of(change(middle, 3000, 1)), 0)).get("adjustment").asLong()).isEqualTo(500);
        assertThat(calculate(request(3000, List.of(change(middle, 2000, 1)), 0)).get("adjustment").asLong()).isEqualTo(-500);
        assertThat(calculate(request(0, List.of(change(middle, 1, 1)), 0)).get("adjustment").asLong()).isEqualTo(1);
        assertThat(calculate(request(1, List.of(change(middle, 0, 1)), 0)).get("adjustment").asLong()).isEqualTo(-1);
    }

    @Test void stageTwoQuantitiesAndStageThreeDiscountRetainAnExactIntervalBreakdown() {
        var changes = List.of(change("2026-01-11T00:00:00Z", 3000, 2), change("2026-01-21T00:00:00Z", 1000, 1));
        JsonNode undiscounted = calculate(request(2000, changes, 0));
        JsonNode discounted = calculate(request(2000, changes, 1000));
        assertThat(undiscounted.get("adjustment").asLong()).isEqualTo(1000);
        assertThat(discounted.get("adjustment").asLong()).isEqualTo(900);
        JsonNode segments = discounted.get("segments");
        assertThat(segments).hasSize(3);
        assertThat(segments.get(0).get("end")).isEqualTo(segments.get(1).get("start"));
        assertThat(segments.get(1).get("end")).isEqualTo(segments.get(2).get("start"));
        java.math.BigInteger sum = java.math.BigInteger.ZERO;
        for (JsonNode segment : segments) sum = sum.add(segment.get("numerator").bigIntegerValue());
        assertThat(sum).isEqualTo(discounted.get("exactNumerator").bigIntegerValue());
        assertThat(calculate(request(2000, changes, 10000)).get("adjustment").asLong()).isZero();
    }

    @Test void repeatedRequestsRemainPureAndInvalidChronologyDoesNotAffectLaterResults() {
        var valid = request(2000, List.of(change("2026-01-16T00:00:00Z", 3000, 1)), 0);
        JsonNode original = calculate(valid);
        api.expect("POST", "/prorations", request(2000, List.of(change("2026-01-21T00:00:00Z", 3000, 1),
                change("2026-01-11T00:00:00Z", 1000, 1)), 0), null, 400);
        api.expect("POST", "/prorations", request(2000, List.of(change("2026-01-31T00:00:00Z", 3000, 1)), 0), null, 400);
        api.expect("POST", "/prorations", request(2000, List.of(change("2026-01-16T00:00:00Z", 3000, 1)), -1), null, 400);
        assertThat(calculate(valid)).isEqualTo(original);
    }

    @Test void exactFractionsAreSummedBeforeTheHttpResultIsRounded() {
        var request = new HashMap<String, Object>();
        request.put("currency", "USD"); request.put("start", "2026-01-01T00:00:00Z"); request.put("end", "2026-01-01T00:00:03Z");
        request.put("initial", plan(0, 1));
        request.put("changes", List.of(change("2026-01-01T00:00:00Z", 1, 1), change("2026-01-01T00:00:01Z", 1, 1), change("2026-01-01T00:00:02Z", 1, 1)));
        JsonNode result = calculate(request);
        assertThat(result.get("adjustment").asLong()).isEqualTo(1);
        assertThat(result.get("exactNumerator").bigIntegerValue()).isEqualTo(result.get("exactDenominator").bigIntegerValue());
    }
}
