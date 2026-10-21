package com.example.qabank;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.UUID;

import static org.hamcrest.Matchers.startsWith;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class QuestionApiTest {
    private static final String VALID_BODY = """
            {"title": "How do I reverse a list in Java?", "body": "I tried a loop but it is slow."}""";

    @Autowired
    MockMvc mvc;

    @Test
    void createReturns201WithLocationAndAppearsInList() throws Exception {
        String author = UUID.randomUUID().toString();
        mvc.perform(post("/api/v1/questions").header("X-User-Id", author)
                        .contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", startsWith("/api/v1/questions/")))
                .andExpect(jsonPath("$.upvotes").value(0));

        mvc.perform(get("/api/v1/questions?limit=5"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items[0].authorId").value(author));
    }

    @Test
    void invalidTitleReturns400() throws Exception {
        mvc.perform(post("/api/v1/questions").header("X-User-Id", UUID.randomUUID())
                        .contentType(MediaType.APPLICATION_JSON).content("{\"title\": \"short\", \"body\": \"x\"}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void upvoteRules() throws Exception {
        String author = UUID.randomUUID().toString();
        String location = mvc.perform(post("/api/v1/questions").header("X-User-Id", author)
                        .contentType(MediaType.APPLICATION_JSON).content(VALID_BODY))
                .andReturn().getResponse().getHeader("Location");
        String voter = UUID.randomUUID().toString();

        mvc.perform(post(location + "/upvotes").header("X-User-Id", voter))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.upvotes").value(1));
        mvc.perform(post(location + "/upvotes").header("X-User-Id", voter)).andExpect(status().isConflict());
        mvc.perform(post(location + "/upvotes").header("X-User-Id", author)).andExpect(status().isForbidden());
        mvc.perform(post("/api/v1/questions/" + UUID.randomUUID() + "/upvotes").header("X-User-Id", voter))
                .andExpect(status().isNotFound());
        mvc.perform(post(location + "/upvotes")).andExpect(status().isUnauthorized());
    }
}
