package com.practice.qabank.handler;

import static org.hamcrest.Matchers.aMapWithSize;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.not;
import static org.junit.jupiter.params.provider.Arguments.arguments;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.net.URI;
import java.util.UUID;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

import com.practice.qabank.exception.AnswerAlreadyExistsException;
import com.practice.qabank.exception.AnswerNotFoundException;
import com.practice.qabank.exception.NotAnswerOwnerException;
import com.practice.qabank.exception.NotQuestionOwnerException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.mapper.QuestionMapperImpl;
import com.practice.qabank.service.QuestionService;
import com.practice.qabank.web.QuestionController;

// Runs in the MVC slice because Spring itself raises these exceptions; building them by hand would test a fake.
@WebMvcTest(QuestionController.class)
@Import(QuestionMapperImpl.class)
class ApiExceptionHandlerTest {

    private static final String USER = "user-42";
    private static final String KEY = "key-1";
    private static final MediaType JSON = MediaType.APPLICATION_JSON;
    private static final String VALID_BODY = "{\"content\": \"How?\", \"tags\": [\"java\"]}";
    private static final UUID QUESTION_ID = UUID.fromString("3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11");
    private static final UUID ANSWER_ID = UUID.fromString("9b2e4d71-0c3a-4f5e-8b6d-1a7c2e9f4b30");

    @Autowired
    MockMvc mvc;

    @MockitoBean
    QuestionService service;

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void mapsInvalidInputToStatusAndError(String name, MockHttpServletRequestBuilder request, int status, String error,
            String messageContains) throws Exception {
        mvc.perform(request)
                .andExpect(status().is(status))
                .andExpect(jsonPath("$.error").value(error))
                .andExpect(jsonPath("$.message", containsString(messageContains)));

        verifyNoInteractions(service);
    }

    // POST and PUT take the same headers and body, so both get every row, named after the method.
    static Stream<Arguments> invalidRequests() {
        return Stream.concat(
                invalidRows("POST", ApiExceptionHandlerTest::create),
                invalidRows("PUT", ApiExceptionHandlerTest::update));
    }

    private static Stream<Arguments> invalidRows(String method, RequestFactory request) {
        return Stream.of(
                arguments("missing X-User-Id", request.build(null, KEY, JSON, VALID_BODY), 400, "MISSING_HEADER",
                        "X-User-Id"),
                arguments("missing Idempotency-Key", request.build(USER, null, JSON, VALID_BODY), 400,
                        "MISSING_HEADER", "Idempotency-Key"),
                arguments("blank X-User-Id", request.build("   ", KEY, JSON, VALID_BODY), 400, "VALIDATION_FAILED",
                        "X-User-Id"),
                arguments("X-User-Id of 65 chars", request.build("u".repeat(65), KEY, JSON, VALID_BODY), 400,
                        "VALIDATION_FAILED", "X-User-Id"),
                arguments("blank Idempotency-Key", request.build(USER, "   ", JSON, VALID_BODY), 400,
                        "VALIDATION_FAILED", "Idempotency-Key"),
                arguments("Idempotency-Key of 65 chars", request.build(USER, "k".repeat(65), JSON, VALID_BODY), 400,
                        "VALIDATION_FAILED", "Idempotency-Key"),
                arguments("no content", request.build(USER, KEY, JSON, "{\"tags\": [\"java\"]}"), 400,
                        "VALIDATION_FAILED", "content"),
                arguments("blank content", request.build(USER, KEY, JSON, "{\"content\": \"   \"}"), 400,
                        "VALIDATION_FAILED", "content"),
                arguments("content of 5001 chars", request.build(USER, KEY, JSON, body("x".repeat(5001), "[]")), 400,
                        "VALIDATION_FAILED", "content"),
                arguments("6 tags",
                        request.build(USER, KEY, JSON, body("How?", "[\"a\",\"b\",\"c\",\"d\",\"e\",\"f\"]")), 400,
                        "VALIDATION_FAILED", "tags"),
                arguments("empty tag", request.build(USER, KEY, JSON, body("How?", "[\"\"]")), 400,
                        "VALIDATION_FAILED", "tags[0]"),
                arguments("null tag", request.build(USER, KEY, JSON, body("How?", "[\"java\", null]")), 400,
                        "VALIDATION_FAILED", "tags[1]"),
                arguments("tag with a space", request.build(USER, KEY, JSON, body("How?", "[\"spring boot\"]")), 400,
                        "VALIDATION_FAILED", "tags[0]"),
                arguments("tag of 36 chars",
                        request.build(USER, KEY, JSON, body("How?", "[\"" + "t".repeat(36) + "\"]")), 400,
                        "VALIDATION_FAILED", "tags[0]"),
                arguments("body is not JSON", request.build(USER, KEY, JSON, "{not json"), 400, "MALFORMED_REQUEST",
                        "JSON"),
                arguments("tags is not an array", request.build(USER, KEY, JSON, body("How?", "\"java\"")), 400,
                        "MALFORMED_REQUEST", "JSON"),
                arguments("no body", request.build(USER, KEY, JSON, null), 400, "MALFORMED_REQUEST", "JSON"),
                arguments("Content-Type text/plain", request.build(USER, KEY, MediaType.TEXT_PLAIN, VALID_BODY), 415,
                        "UNSUPPORTED_MEDIA_TYPE", "application/json"))
                .map(row -> {
                    Object[] values = row.get();
                    values[0] = method + " " + values[0];
                    return arguments(values);
                });
    }

    // The same rows as GetQuestionFT#malformedIds.
    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void malformedIdGives400WithoutCallingService(String name, String id) throws Exception {
        mvc.perform(get("/questions/" + id))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value("id must be a UUID"));

        verifyNoInteractions(service);
    }

    static Stream<Arguments> malformedIds() {
        return Stream.of(
                arguments("words", "not-a-uuid"),
                arguments("digits only, no dashes", "12345"),
                arguments("37 chars", "3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11a"),
                arguments("right shape, not hex", "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"),
                arguments("32 hex chars, no dashes", "3f1c9a528a7e4f0b9d0e2b6c1f6a7e11"));
    }

    // Built from a URI so the query is sent as written, not re-encoded as a template.
    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidListQueries")
    void invalidListQueryGives400WithoutCallingService(String name, String query, String message) throws Exception {
        mvc.perform(get(URI.create("/questions?" + query)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value(message));

        verifyNoInteractions(service);
    }

    // The same rows as ListQuestionsFT#invalidQueries, but tag=c++ is sent as Tomcat decodes it, c and two spaces:
    // MockMvc decodes %XX in a query but leaves a + as it is.
    static Stream<Arguments> invalidListQueries() {
        String tooSmall = "limit: must be greater than or equal to 1";
        String tooLarge = "limit: must be less than or equal to 100";
        String notInteger = "limit must be an integer";
        String tagRule = "tag: must match \"[A-Za-z0-9+#.-]{1,35}\"";
        return Stream.of(
                arguments("limit=0", "limit=0", tooSmall),
                arguments("limit=-1", "limit=-1", tooSmall),
                arguments("limit=101", "limit=101", tooLarge),
                arguments("limit=abc", "limit=abc", notInteger),
                arguments("limit=1.5", "limit=1.5", notInteger),
                arguments("limit=99999999999, above int", "limit=99999999999", notInteger),
                arguments("tag= (empty)", "tag=", tagRule),
                arguments("tag=spring%20boot", "tag=spring%20boot", tagRule),
                arguments("tag=c++, where + is a space", "tag=c%20%20", tagRule),
                arguments("tag of 36 chars", "tag=" + "t".repeat(36), tagRule),
                arguments("limit=0&tag=a%20b, both reported", "limit=0&tag=a%20b", tooSmall + "; " + tagRule),
                arguments("after=not-a-uuid&limit=0, conversion first", "after=not-a-uuid&limit=0",
                        "after must be a UUID"));
    }

    @Test
    void unknownAfterGives404WithTheId() throws Exception {
        given(service.list(null, QUESTION_ID, 20)).willThrow(new QuestionNotFoundException(QUESTION_ID));

        mvc.perform(get("/questions?after=" + QUESTION_ID))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("QUESTION_NOT_FOUND"))
                .andExpect(jsonPath("$.message").value("Question " + QUESTION_ID + " not found"))
                .andExpect(jsonPath("$", aMapWithSize(2)));

        verify(service).list(null, QUESTION_ID, 20);
    }

    @Test
    void unknownQuestionGives404WithTheId() throws Exception {
        given(service.get(QUESTION_ID)).willThrow(new QuestionNotFoundException(QUESTION_ID));

        mvc.perform(get("/questions/" + QUESTION_ID))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("QUESTION_NOT_FOUND"))
                .andExpect(jsonPath("$.message").value("Question " + QUESTION_ID + " not found"));

        verify(service).get(QUESTION_ID);
    }

    // The endpoints that throw most of these come in later APIs, so the mocked service throws each one from create.
    @ParameterizedTest(name = "{0}")
    @MethodSource("serviceExceptions")
    void mapsServiceExceptionToStatusAndError(String name, RuntimeException exception, int status, String error,
            String message) throws Exception {
        given(service.create(any(), anyString())).willThrow(exception);

        mvc.perform(create(USER, KEY, JSON, VALID_BODY))
                .andExpect(status().is(status))
                .andExpect(jsonPath("$.error").value(error))
                .andExpect(jsonPath("$.message").value(message))
                .andExpect(jsonPath("$", aMapWithSize(2)));
    }

    static Stream<Arguments> serviceExceptions() {
        return Stream.of(
                arguments("question not found", new QuestionNotFoundException(QUESTION_ID), 404, "QUESTION_NOT_FOUND",
                        "Question " + QUESTION_ID + " not found"),
                arguments("answer not found", new AnswerNotFoundException(QUESTION_ID, ANSWER_ID), 404,
                        "ANSWER_NOT_FOUND", "Answer " + ANSWER_ID + " not found on question " + QUESTION_ID),
                arguments("not the question's owner", new NotQuestionOwnerException(QUESTION_ID), 403,
                        "NOT_QUESTION_OWNER", "Only the author can update question " + QUESTION_ID),
                arguments("not the answer's owner", new NotAnswerOwnerException(QUESTION_ID, ANSWER_ID), 403,
                        "NOT_ANSWER_OWNER", "Only the author can update answer " + ANSWER_ID),
                arguments("answer already exists", new AnswerAlreadyExistsException(QUESTION_ID, ANSWER_ID), 409,
                        "ANSWER_ALREADY_EXISTS",
                        "Question " + QUESTION_ID + " already has answer " + ANSWER_ID + " by this user"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("updateExceptions")
    void mapsUpdateExceptionToStatusAndError(String name, RuntimeException exception, int status, String error,
            String message) throws Exception {
        given(service.update(any(), any(), anyString())).willThrow(exception);

        mvc.perform(update(USER, KEY, JSON, VALID_BODY))
                .andExpect(status().is(status))
                .andExpect(jsonPath("$.error").value(error))
                .andExpect(jsonPath("$.message").value(message))
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(header().doesNotExist("Idempotent-Replayed"));

        verify(service).update(any(), any(), anyString());
    }

    static Stream<Arguments> updateExceptions() {
        return Stream.of(
                arguments("question not found", new QuestionNotFoundException(QUESTION_ID), 404, "QUESTION_NOT_FOUND",
                        "Question " + QUESTION_ID + " not found"),
                arguments("not the question's owner", new NotQuestionOwnerException(QUESTION_ID), 403,
                        "NOT_QUESTION_OWNER", "Only the author can update question " + QUESTION_ID));
    }

    @Test
    void unexpectedServiceErrorGives500WithoutDetails() throws Exception {
        given(service.create(any(), anyString())).willThrow(new IllegalStateException("secret internal detail"));

        mvc.perform(create(USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").value("INTERNAL_ERROR"))
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(content().string(not(containsString("secret"))))
                .andExpect(content().string(not(containsString("Exception"))));
    }

    @Test
    void unknownPathStays404() throws Exception {
        mvc.perform(get("/no-such-path"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("NOT_FOUND"));
    }

    // GET /questions is the list now, so DELETE stands in for a wrong method.
    @Test
    void wrongMethodStays405() throws Exception {
        mvc.perform(delete("/questions"))
                .andExpect(status().isMethodNotAllowed())
                .andExpect(header().string("Allow", allOf(containsString("GET"), containsString("POST"))))
                .andExpect(jsonPath("$.error").value("METHOD_NOT_ALLOWED"));
    }

    // Builds a POST /questions; a null argument leaves that header or the body out.
    private static MockHttpServletRequestBuilder create(String userId, String key, MediaType type, String body) {
        return withParts(post("/questions"), userId, key, type, body);
    }

    // Builds a PUT /questions/{QUESTION_ID}; a null argument leaves that header or the body out.
    private static MockHttpServletRequestBuilder update(String userId, String key, MediaType type, String body) {
        return withParts(put("/questions/" + QUESTION_ID), userId, key, type, body);
    }

    private static MockHttpServletRequestBuilder withParts(MockHttpServletRequestBuilder request, String userId,
            String key, MediaType type, String body) {
        request.contentType(type);
        if (userId != null) {
            request.header("X-User-Id", userId);
        }
        if (key != null) {
            request.header("Idempotency-Key", key);
        }
        if (body != null) {
            request.content(body);
        }
        return request;
    }

    private static String body(String content, String tagsJson) {
        return "{\"content\": \"" + content + "\", \"tags\": " + tagsJson + "}";
    }

    @FunctionalInterface
    private interface RequestFactory {
        MockHttpServletRequestBuilder build(String userId, String key, MediaType type, String body);
    }
}
