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

    private final String body = """
            {"currency":"USD","start":"2026-01-01T00:00:00Z","end":"2026-01-31T00:00:00Z",
             "initial":{"price":2000,"quantity":1},
             "changes":[{"at":"2026-01-16T00:00:00Z","plan":{"price":3000,"quantity":1}}],
             "discountBasisPoints":1000}
            """;
    @Test void calculatesDiscountedAdjustmentThroughHttp() throws Exception {
        mvc.perform(post("/prorations").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isOk()).andExpect(jsonPath("$.adjustment").value(450))
                .andExpect(jsonPath("$.segments.length()").value(2));
    }
    @Test void invalidQuantityBoundaryAndDiscountReturn400() throws Exception {
        for (String invalid : new String[]{body.replace("\"quantity\":1", "\"quantity\":0"),
                body.replace("2026-01-16", "2026-01-31"), body.replace("1000}", "10001}"), "{}"}) {
            mvc.perform(post("/prorations").contentType(MediaType.APPLICATION_JSON).content(invalid))
                    .andExpect(status().isBadRequest());
        }
    }
}
