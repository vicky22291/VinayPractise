package com.practice.stripe;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.practice.stripe.processor.SimulatedProcessor;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = "processor.timeout-after-accept=true")
@AutoConfigureMockMvc
class UncertainCaptureApiTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired SimulatedProcessor processor;

    @Test void unknownCaptureCanBeReconciledThroughTheApi() throws Exception {
        String prefix = UUID.randomUUID().toString();
        int chargesBefore = processor.chargeCount();
        String created = mvc.perform(post("/payments").header("Idempotency-Key", prefix + "-create")
                        .contentType(MediaType.APPLICATION_JSON).content("{\"amount\":100,\"currency\":\"USD\"}"))
                .andExpect(status().isCreated()).andReturn().getResponse().getContentAsString();
        String id = mapper.readTree(created).get("id").asText();
        mvc.perform(post("/payments/" + id + "/authorize").header("Idempotency-Key", prefix + "-auth")).andExpect(status().isOk());
        String pending = mvc.perform(post("/payments/" + id + "/captures").header("Idempotency-Key", prefix + "-capture")
                        .contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.status").value("UNKNOWN"))
                .andReturn().getResponse().getContentAsString();
        String capture = mapper.readTree(pending).get("id").asText();
        mvc.perform(get("/payments/" + id)).andExpect(jsonPath("$.reservedAmount").value(100));
        mvc.perform(post("/payments/" + id + "/captures").header("Idempotency-Key", prefix + "-competing")
                        .contentType(MediaType.APPLICATION_JSON).content("{\"amount\":1}"))
                .andExpect(status().isConflict());
        mvc.perform(post("/payments/" + id + "/cancel").header("Idempotency-Key", prefix + "-cancel"))
                .andExpect(status().isConflict());
        mvc.perform(post("/payments/" + id + "/captures/" + capture + "/reconcile")
                        .header("Idempotency-Key", prefix + "-reconcile"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("SUCCEEDED"));
        mvc.perform(get("/payments/" + id)).andExpect(jsonPath("$.status").value("CAPTURED"))
                .andExpect(jsonPath("$.reservedAmount").value(0)).andExpect(jsonPath("$.capturedAmount").value(100));
        String replay = mvc.perform(post("/payments/" + id + "/captures").header("Idempotency-Key", prefix + "-capture")
                        .contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.status").value("UNKNOWN"))
                .andReturn().getResponse().getContentAsString();
        assertThat(replay).isEqualTo(pending);
        mvc.perform(post("/payments/" + id + "/captures/" + capture + "/reconcile")
                        .header("Idempotency-Key", prefix + "-observe"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("SUCCEEDED"));
        mvc.perform(get("/payments/" + id + "/captures")).andExpect(jsonPath("$.length()").value(1))
                .andExpect(jsonPath("$[0].status").value("SUCCEEDED"));
        assertThat(processor.chargeCount() - chargesBefore).isEqualTo(1);
    }
}
