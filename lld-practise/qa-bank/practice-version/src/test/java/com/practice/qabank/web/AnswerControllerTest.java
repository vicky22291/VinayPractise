package com.practice.qabank.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.aMapWithSize;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.nullValue;
import static org.junit.jupiter.params.provider.Arguments.arguments;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;
import java.util.Locale;
import java.util.UUID;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Vote;
import com.practice.qabank.exception.AnswerAlreadyExistsException;
import com.practice.qabank.exception.AnswerNotFoundException;
import com.practice.qabank.exception.NotAnswerOwnerException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.mapper.QuestionMapperImpl;
import com.practice.qabank.service.QuestionService;

// Also covers ApiExceptionHandler through this endpoint, in its own slice, because Spring itself raises most of these
// exceptions; building them by hand would test a fake.
@WebMvcTest(AnswerController.class)
@Import(QuestionMapperImpl.class)
class AnswerControllerTest {

    private static final String USER = "user-7";
    private static final String KEY = "key-1";
    private static final MediaType JSON = MediaType.APPLICATION_JSON;
    private static final String CONTENT = "Use compute() or merge().";
    private static final String VALID_BODY = "{\"content\": \"" + CONTENT + "\"}";
    private static final UUID QUESTION_ID = UUID.fromString("3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11");
    private static final UUID ANSWER_ID = UUID.fromString("9b2e4d71-0c3a-4f5e-8b6d-1a7c2e9f4b30");
    private static final Answer STORED =
            new Answer(ANSWER_ID, USER, CONTENT, Instant.parse("2026-10-24T06:20:02.481Z"), null, null);
    private static final String LOCATION = "/questions/" + QUESTION_ID + "/answers/" + ANSWER_ID;

    @Autowired
    MockMvc mvc;

    @MockitoBean
    QuestionService service;

    @Test
    void addReturns201WithLocationAndBody() throws Exception {
        given(service.addAnswer(any(), any(), anyString())).willReturn(new IdempotentResult<>(STORED, false));

        mvc.perform(add(QUESTION_ID.toString(), USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", LOCATION))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$", aMapWithSize(7)))
                .andExpect(jsonPath("$.id").value(ANSWER_ID.toString()))
                .andExpect(jsonPath("$.authorId").value(USER))
                .andExpect(jsonPath("$.content").value(CONTENT))
                .andExpect(jsonPath("$.createdAt").value("2026-10-24T06:20:02.481Z"))
                .andExpect(jsonPath("$.updatedAt").value(nullValue()))
                .andExpect(jsonPath("$.upvotes").value(0))
                .andExpect(jsonPath("$.downvotes").value(0));
    }

    @Test
    void replayReturns201WithOriginalAndReplayHeader() throws Exception {
        given(service.addAnswer(any(), any(), anyString())).willReturn(new IdempotentResult<>(STORED, true));

        mvc.perform(add(QUESTION_ID.toString(), USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", LOCATION))
                .andExpect(header().string("Idempotent-Replayed", "true"))
                .andExpect(jsonPath("$.id").value(ANSWER_ID.toString()));
    }

    // The counts are the returned answer's own, so a replay shows them as they were stored.
    @ParameterizedTest(name = "{0}")
    @MethodSource("replayFlags")
    void addShowsTheReturnedAnswersCounts(String name, boolean replayed) throws Exception {
        given(service.addAnswer(any(), any(), anyString()))
                .willReturn(new IdempotentResult<>(voted(STORED, 2, 3), replayed));

        mvc.perform(add(QUESTION_ID.toString(), USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.upvotes").value(2))
                .andExpect(jsonPath("$.downvotes").value(3));
    }

    static Stream<Arguments> replayFlags() {
        return Stream.of(
                arguments("first response", false),
                arguments("replay", true));
    }

    // The body also tries to set the server-owned fields; the draft keeps them null and takes authorId from the header.
    @Test
    void passesPathIdDraftFromBodyAndUserHeaderPlusKeyToService() throws Exception {
        given(service.addAnswer(any(), any(), anyString())).willReturn(new IdempotentResult<>(STORED, false));
        String body = "{\"id\": \"" + UUID.randomUUID() + "\", \"authorId\": \"someone-else\", "
                + "\"createdAt\": \"2000-01-01T00:00:00Z\", \"updatedAt\": \"2000-01-02T00:00:00Z\", "
                + "\"tags\": [\"java\"], \"content\": \"" + CONTENT + "\"}";

        mvc.perform(add(QUESTION_ID.toString(), USER, KEY, JSON, body)).andExpect(status().isCreated());

        ArgumentCaptor<UUID> questionId = ArgumentCaptor.forClass(UUID.class);
        ArgumentCaptor<Answer> draft = ArgumentCaptor.forClass(Answer.class);
        ArgumentCaptor<String> key = ArgumentCaptor.forClass(String.class);
        verify(service).addAnswer(questionId.capture(), draft.capture(), key.capture());
        assertThat(questionId.getValue()).isEqualTo(QUESTION_ID);
        assertThat(key.getValue()).isEqualTo(KEY);
        assertThat(draft.getValue()).isEqualTo(new Answer(null, USER, CONTENT, null, null, null));
    }

    @Test
    void upperCaseQuestionIdIsParsedAndLocationIsLowerCase() throws Exception {
        given(service.addAnswer(eq(QUESTION_ID), any(), anyString())).willReturn(new IdempotentResult<>(STORED, false));

        mvc.perform(add(QUESTION_ID.toString().toUpperCase(Locale.ROOT), USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", LOCATION));
    }

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

    static Stream<Arguments> invalidRequests() {
        String id = QUESTION_ID.toString();
        return Stream.of(
                arguments("missing X-User-Id", add(id, null, KEY, JSON, VALID_BODY), 400, "MISSING_HEADER",
                        "X-User-Id"),
                arguments("missing Idempotency-Key", add(id, USER, null, JSON, VALID_BODY), 400, "MISSING_HEADER",
                        "Idempotency-Key"),
                arguments("blank X-User-Id", add(id, "   ", KEY, JSON, VALID_BODY), 400, "VALIDATION_FAILED",
                        "X-User-Id"),
                arguments("X-User-Id of 65 chars", add(id, "u".repeat(65), KEY, JSON, VALID_BODY), 400,
                        "VALIDATION_FAILED", "X-User-Id"),
                arguments("blank Idempotency-Key", add(id, USER, "   ", JSON, VALID_BODY), 400, "VALIDATION_FAILED",
                        "Idempotency-Key"),
                arguments("Idempotency-Key of 65 chars", add(id, USER, "k".repeat(65), JSON, VALID_BODY), 400,
                        "VALIDATION_FAILED", "Idempotency-Key"),
                arguments("no content", add(id, USER, KEY, JSON, "{}"), 400, "VALIDATION_FAILED", "content"),
                arguments("blank content", add(id, USER, KEY, JSON, "{\"content\": \"   \"}"), 400,
                        "VALIDATION_FAILED", "content"),
                arguments("content of 5001 chars",
                        add(id, USER, KEY, JSON, "{\"content\": \"" + "x".repeat(5001) + "\"}"), 400,
                        "VALIDATION_FAILED", "content"),
                arguments("body is not JSON", add(id, USER, KEY, JSON, "{not json"), 400, "MALFORMED_REQUEST", "JSON"),
                arguments("no body", add(id, USER, KEY, JSON, null), 400, "MALFORMED_REQUEST", "JSON"),
                arguments("Content-Type text/plain", add(id, USER, KEY, MediaType.TEXT_PLAIN, VALID_BODY), 415,
                        "UNSUPPORTED_MEDIA_TYPE", "application/json"));
    }

    // The message names this endpoint's path variable.
    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void malformedQuestionIdGives400WithoutCallingService(String name, String id) throws Exception {
        mvc.perform(add(id, USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value("questionId must be a UUID"));

        verifyNoInteractions(service);
    }

    // The same rows as GetQuestionFT#malformedIds.
    static Stream<Arguments> malformedIds() {
        return Stream.of(
                arguments("words", "not-a-uuid"),
                arguments("digits only, no dashes", "12345"),
                arguments("37 chars", "3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11a"),
                arguments("right shape, not hex", "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"),
                arguments("32 hex chars, no dashes", "3f1c9a528a7e4f0b9d0e2b6c1f6a7e11"));
    }

    @Test
    void unknownQuestionGives404WithTheId() throws Exception {
        given(service.addAnswer(any(), any(), anyString())).willThrow(new QuestionNotFoundException(QUESTION_ID));

        mvc.perform(add(QUESTION_ID.toString(), USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isNotFound())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(jsonPath("$.error").value("QUESTION_NOT_FOUND"))
                .andExpect(jsonPath("$.message").value("Question " + QUESTION_ID + " not found"));
    }

    @Test
    void secondAnswerGives409NamingBothIds() throws Exception {
        given(service.addAnswer(any(), any(), anyString()))
                .willThrow(new AnswerAlreadyExistsException(QUESTION_ID, ANSWER_ID));

        mvc.perform(add(QUESTION_ID.toString(), USER, KEY, JSON, VALID_BODY))
                .andExpect(status().isConflict())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(jsonPath("$.error").value("ANSWER_ALREADY_EXISTS"))
                .andExpect(jsonPath("$.message")
                        .value("Question " + QUESTION_ID + " already has answer " + ANSWER_ID + " by this user"));
    }

    @Test
    void getReturns200WithEveryFieldAndNoLocation() throws Exception {
        Answer edited = new Answer(ANSWER_ID, USER, CONTENT, Instant.parse("2026-10-24T06:20:02.481Z"),
                Instant.parse("2026-10-24T06:25:00Z"), null);
        given(service.getAnswer(QUESTION_ID, ANSWER_ID)).willReturn(edited);

        mvc.perform(getAnswer(QUESTION_ID.toString(), ANSWER_ID.toString()))
                .andExpect(status().isOk())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$", aMapWithSize(7)))
                .andExpect(jsonPath("$.id").value(ANSWER_ID.toString()))
                .andExpect(jsonPath("$.authorId").value(USER))
                .andExpect(jsonPath("$.content").value(CONTENT))
                .andExpect(jsonPath("$.createdAt").value("2026-10-24T06:20:02.481Z"))
                .andExpect(jsonPath("$.updatedAt").value("2026-10-24T06:25:00Z"))
                .andExpect(jsonPath("$.upvotes").value(0))
                .andExpect(jsonPath("$.downvotes").value(0));
    }

    @Test
    void getShowsItsOwnCounts() throws Exception {
        given(service.getAnswer(QUESTION_ID, ANSWER_ID)).willReturn(voted(STORED, 3, 4));

        mvc.perform(getAnswer(QUESTION_ID.toString(), ANSWER_ID.toString()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.upvotes").value(3))
                .andExpect(jsonPath("$.downvotes").value(4));
    }

    @Test
    void getWorksWithoutUserHeader() throws Exception {
        given(service.getAnswer(QUESTION_ID, ANSWER_ID)).willReturn(STORED);

        mvc.perform(getAnswer(QUESTION_ID.toString(), ANSWER_ID.toString()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(ANSWER_ID.toString()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("getIdForms")
    void getPassesTheParsedIdsToService(String name, String questionId, String answerId) throws Exception {
        given(service.getAnswer(QUESTION_ID, ANSWER_ID)).willReturn(STORED);

        mvc.perform(getAnswer(questionId, answerId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(ANSWER_ID.toString()));

        verify(service).getAnswer(QUESTION_ID, ANSWER_ID);
    }

    static Stream<Arguments> getIdForms() {
        return Stream.of(
                arguments("lower case", QUESTION_ID.toString(), ANSWER_ID.toString()),
                arguments("upper case", QUESTION_ID.toString().toUpperCase(Locale.ROOT),
                        ANSWER_ID.toString().toUpperCase(Locale.ROOT)));
    }

    // The message names the path variable that failed.
    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedGetIds")
    void getWithMalformedIdGives400WithoutCallingService(String name, String questionId, String answerId,
            String segment) throws Exception {
        mvc.perform(getAnswer(questionId, answerId))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value(segment + " must be a UUID"));

        verifyNoInteractions(service);
    }

    // Each malformedIds row in each segment, with a valid id in the other.
    static Stream<Arguments> malformedGetIds() {
        return malformedIds().flatMap(row -> {
            String name = (String) row.get()[0];
            String id = (String) row.get()[1];
            return Stream.of(
                    arguments("questionId: " + name, id, ANSWER_ID.toString(), "questionId"),
                    arguments("answerId: " + name, QUESTION_ID.toString(), id, "answerId"));
        });
    }

    @Test
    void getUnknownAnswerGives404NamingBothIds() throws Exception {
        given(service.getAnswer(QUESTION_ID, ANSWER_ID)).willThrow(new AnswerNotFoundException(QUESTION_ID, ANSWER_ID));

        mvc.perform(getAnswer(QUESTION_ID.toString(), ANSWER_ID.toString()))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(jsonPath("$.error").value("ANSWER_NOT_FOUND"))
                .andExpect(jsonPath("$.message")
                        .value("Answer " + ANSWER_ID + " not found on question " + QUESTION_ID));
    }

    private static MockHttpServletRequestBuilder getAnswer(String questionId, String answerId) {
        return get("/questions/" + questionId + "/answers/" + answerId);
    }

    // ---- Update answer ----

    private static final String EDITED_CONTENT = "Use compute() or merge(). No explicit lock is needed.";
    private static final String EDIT_BODY = "{\"content\": \"" + EDITED_CONTENT + "\"}";
    private static final Answer EDITED = new Answer(ANSWER_ID, USER, EDITED_CONTENT,
            Instant.parse("2026-10-24T06:20:02.481Z"), Instant.parse("2026-10-24T06:31:10.204Z"), null);

    @Test
    void updateReturns200WithBodyAndNoLocation() throws Exception {
        given(service.updateAnswer(any(), any(), any(), anyString())).willReturn(new IdempotentResult<>(EDITED, false));

        mvc.perform(update(QUESTION_ID.toString(), ANSWER_ID.toString(), USER, KEY, JSON, EDIT_BODY))
                .andExpect(status().isOk())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$", aMapWithSize(7)))
                .andExpect(jsonPath("$.id").value(ANSWER_ID.toString()))
                .andExpect(jsonPath("$.authorId").value(USER))
                .andExpect(jsonPath("$.content").value(EDITED_CONTENT))
                .andExpect(jsonPath("$.createdAt").value("2026-10-24T06:20:02.481Z"))
                .andExpect(jsonPath("$.updatedAt").value("2026-10-24T06:31:10.204Z"))
                .andExpect(jsonPath("$.upvotes").value(0))
                .andExpect(jsonPath("$.downvotes").value(0));
    }

    @Test
    void updateReplayReturns200WithStoredBodyAndReplayHeader() throws Exception {
        given(service.updateAnswer(any(), any(), any(), anyString())).willReturn(new IdempotentResult<>(EDITED, true));

        mvc.perform(update(QUESTION_ID.toString(), ANSWER_ID.toString(), USER, KEY, JSON, EDIT_BODY))
                .andExpect(status().isOk())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().string("Idempotent-Replayed", "true"))
                .andExpect(jsonPath("$.content").value(EDITED_CONTENT));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("replayFlags")
    void updateShowsTheReturnedAnswersCounts(String name, boolean replayed) throws Exception {
        given(service.updateAnswer(any(), any(), any(), anyString()))
                .willReturn(new IdempotentResult<>(voted(EDITED, 2, 3), replayed));

        mvc.perform(update(QUESTION_ID.toString(), ANSWER_ID.toString(), USER, KEY, JSON, EDIT_BODY))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.upvotes").value(2))
                .andExpect(jsonPath("$.downvotes").value(3));
    }

    // The body also tries to set the server-owned fields; the draft keeps them null and takes authorId from the header.
    @Test
    void updatePassesBothPathIdsDraftFromBodyAndUserHeaderPlusKeyToService() throws Exception {
        given(service.updateAnswer(any(), any(), any(), anyString())).willReturn(new IdempotentResult<>(EDITED, false));
        String body = "{\"id\": \"" + UUID.randomUUID() + "\", \"authorId\": \"someone-else\", "
                + "\"createdAt\": \"2000-01-01T00:00:00Z\", \"updatedAt\": \"2000-01-02T00:00:00Z\", "
                + "\"content\": \"" + EDITED_CONTENT + "\"}";

        mvc.perform(update(QUESTION_ID.toString(), ANSWER_ID.toString(), USER, KEY, JSON, body))
                .andExpect(status().isOk());

        ArgumentCaptor<UUID> questionId = ArgumentCaptor.forClass(UUID.class);
        ArgumentCaptor<UUID> answerId = ArgumentCaptor.forClass(UUID.class);
        ArgumentCaptor<Answer> draft = ArgumentCaptor.forClass(Answer.class);
        ArgumentCaptor<String> key = ArgumentCaptor.forClass(String.class);
        verify(service).updateAnswer(questionId.capture(), answerId.capture(), draft.capture(), key.capture());
        assertThat(questionId.getValue()).isEqualTo(QUESTION_ID);
        assertThat(answerId.getValue()).isEqualTo(ANSWER_ID);
        assertThat(key.getValue()).isEqualTo(KEY);
        assertThat(draft.getValue()).isEqualTo(new Answer(null, USER, EDITED_CONTENT, null, null, null));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidUpdates")
    void mapsInvalidUpdateInputToStatusAndError(String name, MockHttpServletRequestBuilder request, int status,
            String error, String messageContains) throws Exception {
        mvc.perform(request)
                .andExpect(status().is(status))
                .andExpect(jsonPath("$.error").value(error))
                .andExpect(jsonPath("$.message", containsString(messageContains)));

        verifyNoInteractions(service);
    }

    // The add rows, sent as a PUT.
    static Stream<Arguments> invalidUpdates() {
        String q = QUESTION_ID.toString();
        String a = ANSWER_ID.toString();
        return Stream.of(
                arguments("missing X-User-Id", update(q, a, null, KEY, JSON, EDIT_BODY), 400, "MISSING_HEADER",
                        "X-User-Id"),
                arguments("missing Idempotency-Key", update(q, a, USER, null, JSON, EDIT_BODY), 400,
                        "MISSING_HEADER", "Idempotency-Key"),
                arguments("blank X-User-Id", update(q, a, "   ", KEY, JSON, EDIT_BODY), 400, "VALIDATION_FAILED",
                        "X-User-Id"),
                arguments("X-User-Id of 65 chars", update(q, a, "u".repeat(65), KEY, JSON, EDIT_BODY), 400,
                        "VALIDATION_FAILED", "X-User-Id"),
                arguments("blank Idempotency-Key", update(q, a, USER, "   ", JSON, EDIT_BODY), 400,
                        "VALIDATION_FAILED", "Idempotency-Key"),
                arguments("Idempotency-Key of 65 chars", update(q, a, USER, "k".repeat(65), JSON, EDIT_BODY), 400,
                        "VALIDATION_FAILED", "Idempotency-Key"),
                arguments("no content", update(q, a, USER, KEY, JSON, "{}"), 400, "VALIDATION_FAILED", "content"),
                arguments("blank content", update(q, a, USER, KEY, JSON, "{\"content\": \"   \"}"), 400,
                        "VALIDATION_FAILED", "content"),
                arguments("content of 5001 chars",
                        update(q, a, USER, KEY, JSON, "{\"content\": \"" + "x".repeat(5001) + "\"}"), 400,
                        "VALIDATION_FAILED", "content"),
                arguments("body is not JSON", update(q, a, USER, KEY, JSON, "{not json"), 400, "MALFORMED_REQUEST",
                        "JSON"),
                arguments("no body", update(q, a, USER, KEY, JSON, null), 400, "MALFORMED_REQUEST", "JSON"),
                arguments("Content-Type text/plain", update(q, a, USER, KEY, MediaType.TEXT_PLAIN, EDIT_BODY), 415,
                        "UNSUPPORTED_MEDIA_TYPE", "application/json"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void malformedQuestionIdOnUpdateGives400WithoutCallingService(String name, String id) throws Exception {
        mvc.perform(update(id, ANSWER_ID.toString(), USER, KEY, JSON, EDIT_BODY))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value("questionId must be a UUID"));

        verifyNoInteractions(service);
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void malformedAnswerIdOnUpdateGives400WithoutCallingService(String name, String id) throws Exception {
        mvc.perform(update(QUESTION_ID.toString(), id, USER, KEY, JSON, EDIT_BODY))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value("answerId must be a UUID"));

        verifyNoInteractions(service);
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("updateExceptions")
    void mapsUpdateExceptionToStatusAndError(String name, RuntimeException exception, int status, String error,
            String message) throws Exception {
        given(service.updateAnswer(any(), any(), any(), anyString())).willThrow(exception);

        mvc.perform(update(QUESTION_ID.toString(), ANSWER_ID.toString(), USER, KEY, JSON, EDIT_BODY))
                .andExpect(status().is(status))
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(jsonPath("$.error").value(error))
                .andExpect(jsonPath("$.message").value(message));
    }

    static Stream<Arguments> updateExceptions() {
        return Stream.of(
                arguments("question not found", new QuestionNotFoundException(QUESTION_ID), 404, "QUESTION_NOT_FOUND",
                        "Question " + QUESTION_ID + " not found"),
                arguments("answer not found", new AnswerNotFoundException(QUESTION_ID, ANSWER_ID), 404,
                        "ANSWER_NOT_FOUND", "Answer " + ANSWER_ID + " not found on question " + QUESTION_ID),
                arguments("not the answer's owner", new NotAnswerOwnerException(QUESTION_ID, ANSWER_ID), 403,
                        "NOT_ANSWER_OWNER", "Only the author can update answer " + ANSWER_ID));
    }

    // answer with up upvotes and down downvotes, each from its own voter.
    private static Answer voted(Answer answer, int up, int down) {
        Answer voted = answer;
        for (int i = 0; i < up; i++) {
            voted = voted.withVote("up-" + i, Vote.UP);
        }
        for (int i = 0; i < down; i++) {
            voted = voted.withVote("down-" + i, Vote.DOWN);
        }
        return voted;
    }

    // Builds a PUT /questions/{questionId}/answers/{answerId}; a null argument leaves that header or the body out.
    private static MockHttpServletRequestBuilder update(String questionId, String answerId, String userId, String key,
            MediaType type, String body) {
        MockHttpServletRequestBuilder request =
                put("/questions/" + questionId + "/answers/" + answerId).contentType(type);
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

    // Builds a POST /questions/{questionId}/answers; a null argument leaves that header or the body out.
    private static MockHttpServletRequestBuilder add(String questionId, String userId, String key, MediaType type,
            String body) {
        MockHttpServletRequestBuilder request = post("/questions/" + questionId + "/answers").contentType(type);
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
}
