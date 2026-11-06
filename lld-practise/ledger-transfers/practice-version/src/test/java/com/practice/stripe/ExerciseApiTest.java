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

    @Test void transferRetryReverseAndAuditThroughHttp() throws Exception {
        String source = mapper.readTree(postJson("/accounts", "{\"currency\":\"USD\",\"openingBalance\":1000}", key())).get("id").asText();
        String destination = mapper.readTree(postJson("/accounts", "{\"currency\":\"USD\",\"openingBalance\":0}", key())).get("id").asText();
        String body = "{\"sourceId\":\"" + source + "\",\"destinationId\":\"" + destination + "\",\"amount\":400}";
        String transferKey = key();
        String transfer = postJson("/transfers", body, transferKey);
        assertThat(postJson("/transfers", body, transferKey)).isEqualTo(transfer);
        String id = mapper.readTree(transfer).get("id").asText();
        postJson("/transfers/" + id + "/reversals", "", key());
        mvc.perform(post("/transfers/" + id + "/reversals").header("Idempotency-Key", key())).andExpect(status().isConflict());
        mvc.perform(get("/accounts/" + source)).andExpect(jsonPath("$.balance").value(1000));
        mvc.perform(get("/accounts/" + destination + "/audit")).andExpect(jsonPath("$.consistent").value(true));
        mvc.perform(get("/entries")).andExpect(jsonPath("$.length()").value(4));
    }
    @Test void invalidAndMissingResourcesReturn400And404() throws Exception {
        mvc.perform(post("/accounts").contentType(MediaType.APPLICATION_JSON).header("Idempotency-Key", key())
                .content("{\"currency\":\"USD\",\"openingBalance\":-1}")).andExpect(status().isBadRequest());
        mvc.perform(post("/transfers").contentType(MediaType.APPLICATION_JSON).header("Idempotency-Key", key())
                .content("{\"amount\":1}")).andExpect(status().isBadRequest());
        mvc.perform(get("/accounts/" + UUID.randomUUID())).andExpect(status().isNotFound());
        mvc.perform(get("/transfers/" + UUID.randomUUID())).andExpect(status().isNotFound());
    }
}
