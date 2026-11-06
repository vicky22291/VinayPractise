package com.practice.stripe;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ExerciseApiTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;

    private String key() { return UUID.randomUUID().toString(); }
    private String postJson(String path, String body, String key) throws Exception {
        return mvc.perform(post(path).contentType(MediaType.APPLICATION_JSON).header("Idempotency-Key", key).content(body))
                .andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
    }

    @Test void routeClaimCompleteAndRejectStaleTokenThroughHttp() throws Exception {
        String type = "payment." + key();
        postJson("/endpoints", "{\"destination\":\"https://example.com/hook\",\"eventTypes\":[\"" + type + "\"]}", key());
        String publishKey = key();
        String event = "{\"id\":\"" + key() + "\",\"type\":\"" + type + "\",\"payload\":\"demo\"}";
        String batch = postJson("/events", event, publishKey);
        assertThat(postJson("/events", event, publishKey)).isEqualTo(batch);
        String claim = mvc.perform(post("/deliveries/claim").contentType(MediaType.APPLICATION_JSON).content("{\"workerId\":\"worker\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("IN_FLIGHT"))
                .andReturn().getResponse().getContentAsString();
        String id = mapper.readTree(claim).get("id").asText();
        String token = mapper.readTree(claim).get("leaseToken").asText();
        String completion = "{\"leaseToken\":\"" + token + "\",\"outcome\":\"SUCCEEDED\"}";
        mvc.perform(post("/deliveries/" + id + "/attempts").contentType(MediaType.APPLICATION_JSON).content(completion))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("DELIVERED"));
        mvc.perform(post("/deliveries/" + id + "/attempts").contentType(MediaType.APPLICATION_JSON).content(completion))
                .andExpect(status().isConflict());
        mvc.perform(post("/deliveries/claim").contentType(MediaType.APPLICATION_JSON).content("{\"workerId\":\"worker\"}"))
                .andExpect(status().isNoContent());
    }
    @Test void invalidEndpointsAndMissingDeliveriesReturn400And404() throws Exception {
        mvc.perform(post("/endpoints").contentType(MediaType.APPLICATION_JSON).header("Idempotency-Key", key())
                .content("{\"destination\":\"file:///tmp/hook\",\"eventTypes\":[\"event\"]}")).andExpect(status().isBadRequest());
        mvc.perform(post("/events").contentType(MediaType.APPLICATION_JSON).header("Idempotency-Key", key())
                .content("{\"id\":\"\",\"type\":\"event\"}")).andExpect(status().isBadRequest());
        mvc.perform(get("/deliveries/" + UUID.randomUUID())).andExpect(status().isNotFound());
    }
}
