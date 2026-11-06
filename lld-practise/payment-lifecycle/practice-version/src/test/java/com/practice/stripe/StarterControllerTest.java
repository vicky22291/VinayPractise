package com.practice.stripe;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class StarterControllerTest {
    @Autowired MockMvc mvc;

    @Test
    void healthIsUp() throws Exception {
        mvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }

    @Test
    void echoUsesJsonAndGeneratedMapper() throws Exception {
        mvc.perform(post("/echo").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"message\":\"ready\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("ready"));
    }

    @Test
    void echoRejectsBlankMessages() throws Exception {
        mvc.perform(post("/echo").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"message\":\" \"}"))
                .andExpect(status().isBadRequest());
    }
}
