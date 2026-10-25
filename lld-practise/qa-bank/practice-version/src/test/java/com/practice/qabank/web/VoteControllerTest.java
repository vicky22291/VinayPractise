package com.practice.qabank.web;

import static org.hamcrest.Matchers.aMapWithSize;
import static org.hamcrest.Matchers.containsString;
import static org.junit.jupiter.params.provider.Arguments.arguments;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Locale;
import java.util.UUID;
import java.util.stream.Stream;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.BDDMockito.BDDMyOngoingStubbing;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Vote;
import com.practice.qabank.domain.VoteResult;
import com.practice.qabank.exception.AlreadyVotedException;
import com.practice.qabank.exception.AnswerNotFoundException;
import com.practice.qabank.exception.CannotVoteOwnException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.mapper.VoteMapperImpl;
import com.practice.qabank.service.QuestionService;

// Also covers ApiExceptionHandler through all four endpoints, in their own slice, because Spring itself raises most
// of these exceptions; building them by hand would test a fake. Tests that take an Endpoint run once per endpoint.
@WebMvcTest(VoteController.class)
@Import(VoteMapperImpl.class)
class VoteControllerTest {

    private static final String USER = "user-7";
    private static final String KEY = "key-1";
    private static final UUID QUESTION_ID = UUID.fromString("3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11");
    private static final UUID ANSWER_ID = UUID.fromString("9b2e4d71-0c3a-4f5e-8b6d-1a7c2e9f4b30");

    @Autowired
    MockMvc mvc;

    @MockitoBean
    QuestionService service;

    // The body is exactly the endpoint's own count: {"upvotes": n} or {"downvotes": n}.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Endpoint.class)
    void returns201WithTheCountOnly(Endpoint endpoint) throws Exception {
        givenVote(endpoint).willReturn(new IdempotentResult<>(new VoteResult(5), false));

        mvc.perform(vote(endpoint, USER, KEY))
                .andExpect(status().isCreated())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$", aMapWithSize(1)))
                .andExpect(jsonPath("$." + endpoint.field()).value(5));
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Endpoint.class)
    void replayReturns201WithTheStoredCountAndReplayHeader(Endpoint endpoint) throws Exception {
        givenVote(endpoint).willReturn(new IdempotentResult<>(new VoteResult(1), true));

        mvc.perform(vote(endpoint, USER, KEY))
                .andExpect(status().isCreated())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().string("Idempotent-Replayed", "true"))
                .andExpect(jsonPath("$", aMapWithSize(1)))
                .andExpect(jsonPath("$." + endpoint.field()).value(1));
    }

    // Any case parses to the same UUIDs. The service gets the endpoint's Vote.
    @ParameterizedTest(name = "{0}")
    @MethodSource("idForms")
    void passesParsedPathIdsUserHeaderKeyAndVoteToService(String name, Endpoint endpoint, String questionId,
            String answerId) throws Exception {
        givenVote(endpoint).willReturn(new IdempotentResult<>(new VoteResult(1), false));

        mvc.perform(vote(endpoint, questionId, answerId, USER, KEY)).andExpect(status().isCreated());

        if (endpoint.onAnswer()) {
            verify(service).voteAnswer(QUESTION_ID, ANSWER_ID, USER, KEY, endpoint.vote());
        } else {
            verify(service).voteQuestion(QUESTION_ID, USER, KEY, endpoint.vote());
        }
    }

    static Stream<Arguments> idForms() {
        return Stream.of(Endpoint.values()).flatMap(endpoint -> Stream.of(
                arguments(endpoint + ": lower case", endpoint, QUESTION_ID.toString(), ANSWER_ID.toString()),
                arguments(endpoint + ": upper case", endpoint, QUESTION_ID.toString().toUpperCase(Locale.ROOT),
                        ANSWER_ID.toString().toUpperCase(Locale.ROOT))));
    }

    // There's no consumes and no @RequestBody, so neither a body nor a Content-Type is read.
    @ParameterizedTest(name = "{0}")
    @MethodSource("bodies")
    void ignoresBody(String name, Endpoint endpoint, MediaType type, String body) throws Exception {
        givenVote(endpoint).willReturn(new IdempotentResult<>(new VoteResult(1), false));

        mvc.perform(vote(endpoint, USER, KEY).contentType(type).content(body))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$." + endpoint.field()).value(1));
    }

    static Stream<Arguments> bodies() {
        return Stream.of(Endpoint.values()).flatMap(endpoint -> Stream.of(
                arguments(endpoint + ": JSON body", endpoint, MediaType.APPLICATION_JSON,
                        "{\"" + endpoint.field() + "\": 100}"),
                arguments(endpoint + ": Content-Type text/plain", endpoint, MediaType.TEXT_PLAIN, "vote")));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidHeaders")
    void invalidHeaderGives400NamingItWithoutCallingService(String name, MockHttpServletRequestBuilder request,
            String error, String headerName) throws Exception {
        mvc.perform(request)
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value(error))
                .andExpect(jsonPath("$.message", containsString(headerName)));

        verifyNoInteractions(service);
    }

    static Stream<Arguments> invalidHeaders() {
        return Stream.of(Endpoint.values()).flatMap(endpoint -> Stream.of(
                arguments(endpoint + ": missing X-User-Id", vote(endpoint, null, KEY), "MISSING_HEADER",
                        "X-User-Id"),
                arguments(endpoint + ": missing Idempotency-Key", vote(endpoint, USER, null), "MISSING_HEADER",
                        "Idempotency-Key"),
                arguments(endpoint + ": blank X-User-Id", vote(endpoint, "   ", KEY), "VALIDATION_FAILED",
                        "X-User-Id"),
                arguments(endpoint + ": X-User-Id of 65 chars", vote(endpoint, "u".repeat(65), KEY),
                        "VALIDATION_FAILED", "X-User-Id"),
                arguments(endpoint + ": blank Idempotency-Key", vote(endpoint, USER, "   "), "VALIDATION_FAILED",
                        "Idempotency-Key"),
                arguments(endpoint + ": Idempotency-Key of 65 chars", vote(endpoint, USER, "k".repeat(65)),
                        "VALIDATION_FAILED", "Idempotency-Key")));
    }

    // The message names the path variable that failed.
    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void malformedIdGives400WithoutCallingService(String name, Endpoint endpoint, String questionId, String answerId,
            String segment) throws Exception {
        mvc.perform(vote(endpoint, questionId, answerId, USER, KEY))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_FAILED"))
                .andExpect(jsonPath("$.message").value(segment + " must be a UUID"));

        verifyNoInteractions(service);
    }

    // The GetQuestionFT#malformedIds rows as each endpoint's questionId, and as the answer endpoints' answerId, with
    // a valid id in the other segment.
    static Stream<Arguments> malformedIds() {
        String q = QUESTION_ID.toString();
        String a = ANSWER_ID.toString();
        return Stream.of(
                arguments("words", "not-a-uuid"),
                arguments("digits only, no dashes", "12345"),
                arguments("37 chars", "3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11a"),
                arguments("right shape, not hex", "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"),
                arguments("32 hex chars, no dashes", "3f1c9a528a7e4f0b9d0e2b6c1f6a7e11")).flatMap(row -> {
                    String name = (String) row.get()[0];
                    String id = (String) row.get()[1];
                    return Stream.of(Endpoint.values()).flatMap(endpoint -> {
                        Arguments onQuestionId =
                                arguments(endpoint + " questionId: " + name, endpoint, id, a, "questionId");
                        Arguments onAnswerId =
                                arguments(endpoint + " answerId: " + name, endpoint, q, id, "answerId");
                        return endpoint.onAnswer() ? Stream.of(onQuestionId, onAnswerId) : Stream.of(onQuestionId);
                    });
                });
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("serviceExceptions")
    void mapsServiceExceptionToStatusAndError(String name, Endpoint endpoint, RuntimeException exception, int status,
            String error, String message) throws Exception {
        givenVote(endpoint).willThrow(exception);

        mvc.perform(vote(endpoint, USER, KEY))
                .andExpect(status().is(status))
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(jsonPath("$.error").value(error))
                .andExpect(jsonPath("$.message").value(message));
    }

    // The 403 carries the endpoint's own Vote. Either 409 can come from any endpoint: its code names the vote held.
    static Stream<Arguments> serviceExceptions() {
        return Stream.of(Endpoint.values()).flatMap(endpoint -> {
            Vote vote = endpoint.vote();
            String verb = vote == Vote.UP ? "upvote" : "downvote";
            String ownCode = vote == Vote.UP ? "CANNOT_UPVOTE_OWN" : "CANNOT_DOWNVOTE_OWN";
            Stream<Arguments> notFound = Stream.of(arguments(endpoint + ": question not found", endpoint,
                    new QuestionNotFoundException(QUESTION_ID), 404, "QUESTION_NOT_FOUND",
                    "Question " + QUESTION_ID + " not found"));
            if (!endpoint.onAnswer()) {
                return Stream.concat(notFound, Stream.of(
                        arguments(endpoint + ": own question", endpoint,
                                CannotVoteOwnException.question(vote, QUESTION_ID), 403, ownCode,
                                "You can't " + verb + " your own question " + QUESTION_ID),
                        arguments(endpoint + ": already upvoted", endpoint,
                                AlreadyVotedException.question(Vote.UP, QUESTION_ID), 409, "ALREADY_UPVOTED",
                                "You already upvoted question " + QUESTION_ID),
                        arguments(endpoint + ": already downvoted", endpoint,
                                AlreadyVotedException.question(Vote.DOWN, QUESTION_ID), 409, "ALREADY_DOWNVOTED",
                                "You already downvoted question " + QUESTION_ID)));
            }
            return Stream.concat(notFound, Stream.of(
                    arguments(endpoint + ": answer not found", endpoint,
                            new AnswerNotFoundException(QUESTION_ID, ANSWER_ID), 404, "ANSWER_NOT_FOUND",
                            "Answer " + ANSWER_ID + " not found on question " + QUESTION_ID),
                    arguments(endpoint + ": own answer", endpoint, CannotVoteOwnException.answer(vote, ANSWER_ID),
                            403, ownCode, "You can't " + verb + " your own answer " + ANSWER_ID),
                    arguments(endpoint + ": already upvoted", endpoint,
                            AlreadyVotedException.answer(Vote.UP, ANSWER_ID), 409, "ALREADY_UPVOTED",
                            "You already upvoted answer " + ANSWER_ID),
                    arguments(endpoint + ": already downvoted", endpoint,
                            AlreadyVotedException.answer(Vote.DOWN, ANSWER_ID), 409, "ALREADY_DOWNVOTED",
                            "You already downvoted answer " + ANSWER_ID)));
        });
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Endpoint.class)
    void getGives405AllowingOnlyPost(Endpoint endpoint) throws Exception {
        mvc.perform(get(endpoint.path(QUESTION_ID.toString(), ANSWER_ID.toString())))
                .andExpect(status().isMethodNotAllowed())
                .andExpect(header().string("Allow", "POST"))
                .andExpect(jsonPath("$.error").value("METHOD_NOT_ALLOWED"));

        verifyNoInteractions(service);
    }

    // Stubs only the endpoint's own Vote, so a handler that passed the wrong one would get null and fail.
    private BDDMyOngoingStubbing<IdempotentResult<VoteResult>> givenVote(Endpoint endpoint) {
        return endpoint.onAnswer()
                ? given(service.voteAnswer(any(), any(), anyString(), anyString(), eq(endpoint.vote())))
                : given(service.voteQuestion(any(), anyString(), anyString(), eq(endpoint.vote())));
    }

    private static MockHttpServletRequestBuilder vote(Endpoint endpoint, String userId, String key) {
        return vote(endpoint, QUESTION_ID.toString(), ANSWER_ID.toString(), userId, key);
    }

    // Builds a POST to the endpoint with no body; a null userId or key leaves that header out.
    private static MockHttpServletRequestBuilder vote(Endpoint endpoint, String questionId, String answerId,
            String userId, String key) {
        MockHttpServletRequestBuilder request = post(endpoint.path(questionId, answerId));
        if (userId != null) {
            request.header("X-User-Id", userId);
        }
        if (key != null) {
            request.header("Idempotency-Key", key);
        }
        return request;
    }

    // The four vote endpoints. answerId is used only by the answer ones.
    enum Endpoint {
        UPVOTE_QUESTION,
        UPVOTE_ANSWER,
        DOWNVOTE_QUESTION,
        DOWNVOTE_ANSWER;

        String path(String questionId, String answerId) {
            return switch (this) {
                case UPVOTE_QUESTION -> "/questions/" + questionId + "/upvotes";
                case UPVOTE_ANSWER -> "/questions/" + questionId + "/answers/" + answerId + "/upvotes";
                case DOWNVOTE_QUESTION -> "/questions/" + questionId + "/downvotes";
                case DOWNVOTE_ANSWER -> "/questions/" + questionId + "/answers/" + answerId + "/downvotes";
            };
        }

        Vote vote() {
            return this == UPVOTE_QUESTION || this == UPVOTE_ANSWER ? Vote.UP : Vote.DOWN;
        }

        boolean onAnswer() {
            return this == UPVOTE_ANSWER || this == DOWNVOTE_ANSWER;
        }

        // The response body's one field.
        String field() {
            return vote() == Vote.UP ? "upvotes" : "downvotes";
        }
    }
}
