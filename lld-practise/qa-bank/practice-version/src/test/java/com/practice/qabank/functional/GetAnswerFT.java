package com.practice.qabank.functional;

import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import java.util.stream.Stream;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

// Black-box tests for GET /questions/{questionId}/answers/{answerId} against a running app (see qabank.baseUrl). Test
// data is created only through the API.
@Tag("api")
class GetAnswerFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final String ANSWER_CONTENT = "Use compute() or merge(). Both run atomically per key.";
    private static final int PARALLEL_REQUESTS = 50;

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void rejectsMalformedId(String name, String path, String segment) {
        ApiResponse response = api.get(path, Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo(segment + " must be a UUID");
    }

    // Each GetQuestionFT row twice: once as questionId and once as answerId, with a random UUID in the other segment.
    static Stream<Arguments> malformedIds() {
        return GetQuestionFT.malformedIds().flatMap(row -> {
            String name = (String) row.get()[0];
            String id = (String) row.get()[1];
            return Stream.of(
                    arguments("questionId: " + name, answerPath(id, randomId()), "questionId"),
                    arguments("answerId: " + name, answerPath(randomId(), id), "answerId"));
        });
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("com.practice.qabank.functional.GetQuestionFT#userHeaders")
    void ignoresUserHeader(String name, String userId) {
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = addAnswer(questionId, RequestSpec.validAnswer());
        Map<String, String> headers = userId == null ? Map.of() : Map.of(USER_ID, userId);

        ApiResponse response = api.get(answerPath(questionId, (String) added.json("$.id")), headers);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$")).isEqualTo(added.json("$"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("unknownIds")
    void rejectsUnknownIds(String name, Function<Fixture, String> path, String error) {
        String requested = path.apply(fixture());
        String[] segments = requested.split("/");
        String questionId = segments[2];
        String answerId = segments[4];

        ApiResponse response = api.get(requested, Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo(error);
        String message = (String) response.json("$.message");
        if (error.equals("QUESTION_NOT_FOUND")) {
            assertThat(message).isEqualTo("Question " + questionId + " not found");
        } else {
            assertThat(message).isEqualTo("Answer " + answerId + " not found on question " + questionId);
        }
    }

    static Stream<Arguments> unknownIds() {
        return Stream.of(
                unknown("unknown question", f -> answerPath(randomId(), f.answerId()), "QUESTION_NOT_FOUND"),
                unknown("unknown answer", f -> answerPath(f.questionId(), randomId()), "ANSWER_NOT_FOUND"),
                unknown("another question's answer", f -> answerPath(f.questionId(), f.otherAnswerId()),
                        "ANSWER_NOT_FOUND"));
    }

    @Test
    void returnsAddedAnswer() {
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = addAnswer(questionId, RequestSpec.validAnswer().withBody(body(ANSWER_CONTENT)));

        ApiResponse response = api.get(answerPath(questionId, (String) added.json("$.id")), Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$")).isEqualTo(added.json("$"));
        assertThat(response.json("$.content")).isEqualTo(ANSWER_CONTENT);
        assertThat(response.header("Location")).isEmpty();
        assertThat(response.header(REPLAYED)).isEmpty();
    }

    @Test
    void followsAddLocation() {
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = addAnswer(questionId, RequestSpec.validAnswer());
        String location = added.header("Location").orElseThrow();

        ApiResponse response = api.get(location, Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(added.json("$.id"));
    }

    @Test
    void matchesEntryInQuestion() {
        String questionId = createQuestion(RequestSpec.freshUser());
        List<String> answerIds = List.of(
                (String) addAnswer(questionId, RequestSpec.validAnswer()).json("$.id"),
                (String) addAnswer(questionId, RequestSpec.validAnswer()).json("$.id"));

        ApiResponse question = api.get(QUESTIONS + "/" + questionId, Map.of());

        assertThat(question.status()).as(question.body()).isEqualTo(200);
        assertThat(question.json("$.answers.length()")).isEqualTo(2);
        for (String answerId : answerIds) {
            ApiResponse response = api.get(answerPath(questionId, answerId), Map.of());
            assertThat(response.status()).as(response.body()).isEqualTo(200);
            Object entry = question.json("$.answers[?(@.id == '" + answerId + "')]");
            assertThat(entry).isEqualTo(List.of(response.json("$")));
        }
    }

    @Test
    void acceptsUpperCaseIds() {
        String questionId = createQuestion(RequestSpec.freshUser());
        String answerId = (String) addAnswer(questionId, RequestSpec.validAnswer()).json("$.id");

        ApiResponse response = api.get(
                answerPath(questionId.toUpperCase(Locale.ROOT), answerId.toUpperCase(Locale.ROOT)), Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(answerId);
    }

    @Test
    void replayDoesNotChangeStoredAnswer() {
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer().withBody(body(ANSWER_CONTENT));
        ApiResponse added = addAnswer(questionId, request);
        ApiResponse replay = addAnswer(questionId, request.withBody(body("A completely different answer.")));
        assertThat(replay.header(REPLAYED)).contains("true");

        ApiResponse response = api.get(answerPath(questionId, (String) added.json("$.id")), Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.content")).isEqualTo(ANSWER_CONTENT);
    }

    @Test
    void parallelAddThenGet() throws Exception {
        String questionId = createQuestion(RequestSpec.freshUser());
        ExecutorService pool = Executors.newFixedThreadPool(PARALLEL_REQUESTS);
        CountDownLatch ready = new CountDownLatch(PARALLEL_REQUESTS);
        CountDownLatch start = new CountDownLatch(1);
        try {
            List<Future<Void>> futures = new ArrayList<>();
            for (int i = 0; i < PARALLEL_REQUESTS; i++) {
                String content = "Parallel answer " + UUID.randomUUID();
                RequestSpec request = RequestSpec.validAnswer().withBody(body(content));
                // Every thread waits on the start latch, so all adds are released together and really overlap.
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();
                    ApiResponse added = addAnswer(questionId, request);
                    String answerId = (String) added.json("$.id");
                    ApiResponse fetched = api.get(answerPath(questionId, answerId), Map.of());
                    assertThat(fetched.status()).as(fetched.body()).isEqualTo(200);
                    assertThat(fetched.json("$.id")).isEqualTo(answerId);
                    assertThat(fetched.json("$.content")).isEqualTo(content);
                    return null;
                }));
            }
            assertThat(ready.await(10, TimeUnit.SECONDS)).isTrue();
            start.countDown();
            for (Future<Void> future : futures) {
                future.get(60, TimeUnit.SECONDS);
            }
        } finally {
            pool.shutdownNow();
        }
    }

    private String createQuestion(String authorId) {
        ApiResponse response = api.post(QUESTIONS, RequestSpec.validCreate().withHeader(USER_ID, authorId));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return (String) response.json("$.id");
    }

    private ApiResponse addAnswer(String questionId, RequestSpec request) {
        ApiResponse response = api.post(QUESTIONS + "/" + questionId + "/answers", request);
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    // Two questions, and one fresh user answers both. The other ids are that user's answer on the second question.
    private Fixture fixture() {
        String userId = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        String otherQuestionId = createQuestion(RequestSpec.freshUser());
        String answerId = (String) addAnswer(questionId, RequestSpec.validAnswer().withHeader(USER_ID, userId))
                .json("$.id");
        String otherAnswerId = (String) addAnswer(otherQuestionId,
                RequestSpec.validAnswer().withHeader(USER_ID, userId)).json("$.id");
        return new Fixture(userId, questionId, answerId, otherQuestionId, otherAnswerId);
    }

    private static Arguments unknown(String name, Function<Fixture, String> path, String error) {
        return arguments(name, path, error);
    }

    private static String answerPath(String questionId, String answerId) {
        return QUESTIONS + "/" + questionId + "/answers/" + answerId;
    }

    private static String randomId() {
        return UUID.randomUUID().toString();
    }

    private static String body(String content) {
        return "{\"content\": \"" + content + "\"}";
    }

    private record Fixture(String userId, String questionId, String answerId, String otherQuestionId,
            String otherAnswerId) {
    }
}
