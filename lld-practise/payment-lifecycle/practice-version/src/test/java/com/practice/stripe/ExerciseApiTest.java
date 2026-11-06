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

    @Test void createAuthorizePartialCaptureReplayAndCancelConflict() throws Exception {
        String createKey = key();
        String body = "{\"amount\":1000,\"currency\":\"usd\"}";
        String created = postJson("/payments", body, createKey);
        String id = mapper.readTree(created).get("id").asText();
        assertThat(postJson("/payments", body, createKey)).isEqualTo(created);
        mvc.perform(post("/payments/" + id + "/authorize").header("Idempotency-Key", key()))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("AUTHORIZED"));
        String captureKey = key();
        String capture = postJson("/payments/" + id + "/captures", "{\"amount\":400}", captureKey);
        assertThat(postJson("/payments/" + id + "/captures", "{\"amount\":400}", captureKey)).isEqualTo(capture);
        mvc.perform(post("/payments/" + id + "/captures").contentType(MediaType.APPLICATION_JSON)
                        .header("Idempotency-Key", captureKey).content("{\"amount\":401}"))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error").exists());
        mvc.perform(post("/payments/" + id + "/cancel").header("Idempotency-Key", key())).andExpect(status().isConflict());
        postJson("/payments/" + id + "/captures", "{}", key());
        mvc.perform(get("/payments/" + id)).andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CAPTURED")).andExpect(jsonPath("$.capturedAmount").value(1000));
        mvc.perform(get("/payments/" + id + "/captures")).andExpect(jsonPath("$.length()").value(2));
    }
    @Test void invalidMissingAndMalformedRequestsHaveUsefulHttpCodes() throws Exception {
        mvc.perform(post("/payments").contentType(MediaType.APPLICATION_JSON).header("Idempotency-Key", key())
                .content("{\"amount\":0,\"currency\":\"USD\"}")).andExpect(status().isBadRequest());
        mvc.perform(post("/payments").contentType(MediaType.APPLICATION_JSON).content("{\"amount\":1,\"currency\":\"USD\"}"))
                .andExpect(status().isBadRequest());
        mvc.perform(get("/payments/" + UUID.randomUUID())).andExpect(status().isNotFound());
        mvc.perform(get("/payments/not-a-uuid")).andExpect(status().isBadRequest());
    }
}
