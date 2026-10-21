package com.example.qabank.web;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicLong;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.matchesPattern;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD) // fresh in-memory store per test
class QuestionApiTest {
    private static final String BASE = "/api/v1/questions";
    private static final String USER_HEADER = "X-User-Id";
    private static final UUID AUTHOR = UUID.fromString("aaaaaaaa-0000-0000-0000-000000000001");
    private static final UUID VOTER = UUID.fromString("bbbbbbbb-0000-0000-0000-000000000002");

    @Autowired
    MockMvc mvc;
    @Autowired
    ObjectMapper json;

    /** Strictly increasing timestamps make ordering assertions exact. */
    @TestConfiguration
    static class TickingClockConfig {
        @Bean
        @Primary
        Clock tickingClock() {
            AtomicLong millis = new AtomicLong(Instant.parse("2026-01-01T00:00:00Z").toEpochMilli());
            return new Clock() {
                @Override public Instant instant() { return Instant.ofEpochMilli(millis.incrementAndGet()); }
                @Override public ZoneId getZone() { return ZoneOffset.UTC; }
                @Override public Clock withZone(ZoneId zone) { return this; }
            };
        }
    }

    @Test
    void createReturns201WithLocationAndBody() throws Exception {
        createQuestion(AUTHOR, "How do I reverse a list in Java?")
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", matchesPattern("http://localhost/api/v1/questions/[0-9a-f-]{36}")))
                .andExpect(jsonPath("$.id").isNotEmpty())
                .andExpect(jsonPath("$.authorId").value(AUTHOR.toString()))
                .andExpect(jsonPath("$.upvotes").value(0));
    }

    @Test
    void locationHeaderResolvesWith200() throws Exception {
        String location = createQuestion(AUTHOR, "How do I reverse a list in Java?")
                .andReturn().getResponse().getHeader("Location");

        mvc.perform(get(location))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("How do I reverse a list in Java?"))
                .andExpect(jsonPath("$.body").exists());
    }

    @Test
    void listReturns200NewestFirstWithoutBodies() throws Exception {
        String older = createAndGetId("Older question title here");
        String newer = createAndGetId("Newer question title here");

        mvc.perform(get(BASE))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items.length()").value(2))
                .andExpect(jsonPath("$.items[0].id").value(newer))
                .andExpect(jsonPath("$.items[1].id").value(older))
                .andExpect(jsonPath("$.items[0].body").doesNotExist())
                .andExpect(jsonPath("$.nextCursor").doesNotExist());
    }

    @Test
    void invalidBodyReturns400ProblemDetailWithFieldErrors() throws Exception {
        mvc.perform(post(BASE).header(USER_HEADER, AUTHOR).contentType(MediaType.APPLICATION_JSON)
                        .content("{\"title\": \"too short\", \"body\": \"   \"}"))
                .andExpect(status().isBadRequest())
                .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
                .andExpect(jsonPath("$.status").value(400))
                .andExpect(jsonPath("$.errors.title").exists())
                .andExpect(jsonPath("$.errors.body").exists());
    }

    @Test
    void malformedJsonReturns400() throws Exception {
        mvc.perform(post(BASE).header(USER_HEADER, AUTHOR).contentType(MediaType.APPLICATION_JSON).content("{\"title\":"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void badPagingParametersReturn400() throws Exception {
        mvc.perform(get(BASE).param("limit", "101")).andExpect(status().isBadRequest());
        mvc.perform(get(BASE).param("limit", "0")).andExpect(status().isBadRequest());
        mvc.perform(get(BASE).param("limit", "abc")).andExpect(status().isBadRequest());
        mvc.perform(get(BASE).param("cursor", "garbage!!")).andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Invalid cursor"));
    }

    @Test
    void malformedQuestionIdReturns400() throws Exception {
        mvc.perform(get(BASE + "/not-a-uuid")).andExpect(status().isBadRequest());
    }

    @Test
    void missingOrInvalidUserReturns401() throws Exception {
        mvc.perform(post(BASE).contentType(MediaType.APPLICATION_JSON).content(validBody("A valid title for this")))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.detail", containsString("X-User-Id")));
        mvc.perform(post(BASE).header(USER_HEADER, "alice").contentType(MediaType.APPLICATION_JSON)
                        .content(validBody("A valid title for this")))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void unknownQuestionReturns404() throws Exception {
        UUID unknown = UUID.randomUUID();
        mvc.perform(get(BASE + "/" + unknown)).andExpect(status().isNotFound())
                .andExpect(jsonPath("$.title").value("Question not found"));
        mvc.perform(post(BASE + "/" + unknown + "/upvotes").header(USER_HEADER, VOTER))
                .andExpect(status().isNotFound());
    }

    @Test
    void firstUpvoteReturns201AndDuplicateReturns409() throws Exception {
        String id = createAndGetId("A question worth voting on");

        upvote(id, VOTER).andExpect(status().isCreated())
                .andExpect(jsonPath("$.questionId").value(id))
                .andExpect(jsonPath("$.upvotes").value(1));
        upvote(id, VOTER).andExpect(status().isConflict())
                .andExpect(jsonPath("$.title").value("Already upvoted"));

        mvc.perform(get(BASE + "/" + id)).andExpect(jsonPath("$.upvotes").value(1));
    }

    @Test
    void authorUpvoteReturns403() throws Exception {
        String id = createAndGetId("A question worth voting on");

        upvote(id, AUTHOR).andExpect(status().isForbidden());
        mvc.perform(get(BASE + "/" + id)).andExpect(jsonPath("$.upvotes").value(0));
    }

    @Test
    void cursorPaginationHasNoRepeatsOrGapsWithInsertBetweenPages() throws Exception {
        List<String> created = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            created.addFirst(createAndGetId("Paginated question number " + i)); // newest first
        }

        JsonNode page1 = getJson(BASE + "?limit=3");
        createAndGetId("Inserted between page fetches"); // offset paging would now repeat an item
        JsonNode page2 = getJson(BASE + "?limit=3&cursor=" + page1.get("nextCursor").asText());

        List<String> seen = new ArrayList<>();
        page1.get("items").forEach(item -> seen.add(item.get("id").asText()));
        page2.get("items").forEach(item -> seen.add(item.get("id").asText()));

        assertThat(page1.get("items")).hasSize(3);
        assertThat(page2.get("items")).hasSize(2);
        assertThat(page2.get("nextCursor").isNull()).isTrue();
        assertThat(seen).containsExactlyElementsOf(created);
    }

    private ResultActions createQuestion(UUID author, String title) throws Exception {
        return mvc.perform(post(BASE).header(USER_HEADER, author)
                .contentType(MediaType.APPLICATION_JSON).content(validBody(title)));
    }

    private String createAndGetId(String title) throws Exception {
        String response = createQuestion(AUTHOR, title).andExpect(status().isCreated())
                .andReturn().getResponse().getContentAsString();
        return json.readTree(response).get("id").asText();
    }

    private ResultActions upvote(String questionId, UUID voter) throws Exception {
        return mvc.perform(post(BASE + "/" + questionId + "/upvotes").header(USER_HEADER, voter));
    }

    private JsonNode getJson(String url) throws Exception {
        return json.readTree(mvc.perform(get(url)).andExpect(status().isOk()).andReturn().getResponse().getContentAsString());
    }

    private static String validBody(String title) {
        return "{\"title\": \"" + title + "\", \"body\": \"Some details about the problem.\"}";
    }
}
