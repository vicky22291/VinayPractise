package com.vinaypractice2.qabank.controllers;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vinaypractice2.qabank.domain.CreateQuestionRequest;
import com.vinaypractice2.qabank.domain.QuestionResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.annotation.DirtiesContext.MethodMode;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import org.springframework.test.web.servlet.assertj.MvcTestResult;

import java.util.Arrays;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

// Full-stack test: @SpringBootTest starts the whole app (controller, service, mapper, in-memory repo).
// Nothing is mocked, so each test only drives HTTP requests and checks the responses.
// The app (and its repo) is shared by every test, so a test only asserts on questions it created itself.
// MockMvcTester converts the JSON body back into an object, so we assert on data, not JSON paths.
@SpringBootTest
@AutoConfigureMockMvc
class QuestionsControllerTest {
    private static final String BASE_URL = "/api/v1/questions";
    private static final String USER_ID = "u1";

    @Autowired
    MockMvcTester mvc;

    @Autowired
    ObjectMapper objectMapper;

    // ---------- POST /api/v1/questions ----------

    @Test
    void testCreate() throws Exception {
        final CreateQuestionRequest request = new CreateQuestionRequest("How to run tests?", "How to run junit tests?");

        final QuestionResponse created = create(request);

        // The server assigns the id and both timestamps; a new question has createdAt == updatedAt.
        assertThat(created.id()).isNotNull();
        assertThat(created.createdAt()).isNotNull().isEqualTo(created.updatedAt());
        assertThat(created).usingRecursiveComparison().ignoringFields("id", "createdAt", "updatedAt")
                .isEqualTo(new QuestionResponse(null, request.title(), request.description(), USER_ID, null, null));
    }

    @Test
    void testCreateWithBlankTitleReturns400() throws Exception {
        final CreateQuestionRequest request = new CreateQuestionRequest(" ", "How to run junit tests?");

        assertThat(postQuestion(request).header("X-User-Id", USER_ID)).hasStatus(HttpStatus.BAD_REQUEST);
    }

    @Test
    void testCreateWithTooLongTitleReturns400() throws Exception {
        final CreateQuestionRequest request = new CreateQuestionRequest("t".repeat(151), "How to run junit tests?");

        assertThat(postQuestion(request).header("X-User-Id", USER_ID)).hasStatus(HttpStatus.BAD_REQUEST);
    }

    @Test
    void testCreateWithoutUserHeaderReturns400() throws Exception {
        final CreateQuestionRequest request = new CreateQuestionRequest("How to run tests?", "How to run junit tests?");

        assertThat(postQuestion(request)).hasStatus(HttpStatus.BAD_REQUEST);
    }

    @Test
    void testCreateWithTooLongUserIdReturns400() throws Exception {
        final CreateQuestionRequest request = new CreateQuestionRequest("How to run tests?", "How to run junit tests?");

        assertThat(postQuestion(request).header("X-User-Id", "u".repeat(65))).hasStatus(HttpStatus.BAD_REQUEST);
    }

    @Test
    void testCreateWithMalformedJsonReturns400() {
        assertThat(mvc.post().uri(BASE_URL)
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-User-Id", USER_ID)
                .content("{\"title\":"))
                .hasStatus(HttpStatus.BAD_REQUEST);
    }

    // ---------- GET /api/v1/questions/{id} ----------

    @Test
    void testGetReturnsWhatWasCreated() throws Exception {
        final QuestionResponse created = create(new CreateQuestionRequest("How to run tests?", "How to run junit tests?"));

        final QuestionResponse found = assertThat(mvc.get().uri(BASE_URL + "/" + created.id()))
                .hasStatusOk()
                .bodyJson()
                .convertTo(QuestionResponse.class)
                .actual();

        assertThat(found).isEqualTo(created);
    }

    @Test
    void testGetUnknownIdReturns404() {
        final UUID unknownId = UUID.randomUUID();

        final ProblemDetail problem = assertThat(mvc.get().uri(BASE_URL + "/" + unknownId))
                .hasStatus(HttpStatus.NOT_FOUND)
                .bodyJson()
                .convertTo(ProblemDetail.class)
                .actual();

        assertThat(problem.getStatus()).isEqualTo(404);
        assertThat(problem.getDetail()).isEqualTo("No question with id: " + unknownId);
    }

    @Test
    void testGetWithInvalidUuidReturns400() {
        assertThat(mvc.get().uri(BASE_URL + "/not-a-uuid")).hasStatus(HttpStatus.BAD_REQUEST);
    }

    // ---------- GET /api/v1/questions ----------

    @Test
    void testListIsNewestFirst() throws Exception {
        final QuestionResponse older = create(new CreateQuestionRequest("Older", "Created first"));
        final QuestionResponse newer = create(new CreateQuestionRequest("Newer", "Created second"));

        // Other tests add questions too, so keep only the two created here before checking order.
        final QuestionResponse[] mine = Arrays.stream(listAll())
                .filter(q -> q.id().equals(older.id()) || q.id().equals(newer.id()))
                .toArray(QuestionResponse[]::new);

        assertThat(mine).containsExactly(newer, older);
    }

    @Test
    @DirtiesContext(methodMode = MethodMode.BEFORE_METHOD) // fresh app, so the repo starts empty
    void testListEmpty() {
        assertThat(listAll()).isEmpty();
    }

    // ---------- helpers ----------

    // POSTs the request, checks 201 + Location header, and returns the saved question.
    private QuestionResponse create(final CreateQuestionRequest request) throws Exception {
        final MvcTestResult result = postQuestion(request).header("X-User-Id", USER_ID).exchange();
        final QuestionResponse created = assertThat(result)
                .hasStatus(HttpStatus.CREATED)
                .bodyJson()
                .convertTo(QuestionResponse.class)
                .actual();
        assertThat(result).hasHeader("Location", BASE_URL + "/" + created.id());
        return created;
    }

    private QuestionResponse[] listAll() {
        return assertThat(mvc.get().uri(BASE_URL))
                .hasStatusOk()
                .bodyJson()
                .convertTo(QuestionResponse[].class)
                .actual();
    }

    private MockMvcTester.MockMvcRequestBuilder postQuestion(final CreateQuestionRequest request) throws Exception {
        return mvc.post().uri(BASE_URL)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request));
    }
}
