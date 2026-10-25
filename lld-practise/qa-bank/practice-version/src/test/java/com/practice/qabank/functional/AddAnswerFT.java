package com.practice.qabank.functional;

import static com.practice.qabank.functional.RequestSpec.CONTENT_TYPE;
import static com.practice.qabank.functional.RequestSpec.IDEMPOTENCY_KEY;
import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.UnaryOperator;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.assertj.core.api.InstanceOfAssertFactories;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

// Black-box tests for POST /questions/{questionId}/answers against a running app (see qabank.baseUrl). Test data is
// created only through the API and read back through GET /questions/{id}.
@Tag("api")
class AddAnswerFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final String ANSWER_CONTENT = "Use compute() or merge(). Both run atomically per key.";
    private static final int PARALLEL_REQUESTS = 50;
    private static final int RACING_REQUESTS = 25;

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void rejectsInvalidRequest(String name, UnaryOperator<RequestSpec> change, int status, String error) {
        String questionId = createQuestion(RequestSpec.freshUser());

        ApiResponse response = postAnswer(questionId, change.apply(RequestSpec.validAnswer()));

        assertThat(response.status()).as(response.body()).isEqualTo(status);
        assertThat(response.json("$.error")).isEqualTo(error);
        assertThat((String) response.json("$.message")).isNotBlank();
        assertThat(getQuestion(questionId).json("$.answers")).isEqualTo(List.of());
    }

    static Stream<Arguments> invalidRequests() {
        return Stream.of(
                invalid("missing X-User-Id", r -> r.withoutHeader(USER_ID), 400, "MISSING_HEADER"),
                invalid("missing Idempotency-Key", r -> r.withoutHeader(IDEMPOTENCY_KEY), 400, "MISSING_HEADER"),
                invalid("blank X-User-Id", r -> r.withHeader(USER_ID, "   "), 400, "VALIDATION_FAILED"),
                invalid("X-User-Id of 65 chars", r -> r.withHeader(USER_ID, uniqueOfLength(65)), 400,
                        "VALIDATION_FAILED"),
                invalid("blank Idempotency-Key", r -> r.withHeader(IDEMPOTENCY_KEY, "   "), 400, "VALIDATION_FAILED"),
                invalid("Idempotency-Key of 65 chars", r -> r.withHeader(IDEMPOTENCY_KEY, uniqueOfLength(65)), 400,
                        "VALIDATION_FAILED"),
                invalid("no content", r -> r.withBody("{}"), 400, "VALIDATION_FAILED"),
                invalid("blank content", r -> r.withBody(body("   ")), 400, "VALIDATION_FAILED"),
                invalid("content of 5001 chars", r -> r.withBody(body("x".repeat(5001))), 400, "VALIDATION_FAILED"),
                invalid("body is not JSON", r -> r.withBody("{not json"), 400, "MALFORMED_REQUEST"),
                invalid("Content-Type text/plain", r -> r.withHeader(CONTENT_TYPE, "text/plain"), 415,
                        "UNSUPPORTED_MEDIA_TYPE"));
    }

    // The same rows as GetQuestionFT, but the path segment is named questionId here.
    @ParameterizedTest(name = "{0}")
    @MethodSource("com.practice.qabank.functional.GetQuestionFT#malformedIds")
    void rejectsMalformedId(String name, String id) {
        ApiResponse response = postAnswer(id, RequestSpec.validAnswer());

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo("questionId must be a UUID");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("boundaryValues")
    void acceptsBoundaryValue(String name, UnaryOperator<RequestSpec> change) {
        String questionId = createQuestion(RequestSpec.freshUser());

        ApiResponse response = postAnswer(questionId, change.apply(RequestSpec.validAnswer()));

        assertThat(response.status()).as(response.body()).isEqualTo(201);
        assertThat(response.header(REPLAYED)).isEmpty();
    }

    static Stream<Arguments> boundaryValues() {
        return Stream.of(
                boundary("X-User-Id of 64 chars", r -> r.withHeader(USER_ID, uniqueOfLength(64))),
                boundary("Idempotency-Key of 64 chars", r -> r.withHeader(IDEMPOTENCY_KEY, uniqueOfLength(64))),
                boundary("content of 5000 chars", r -> r.withBody(body("x".repeat(5000)))));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("retryBodies")
    void replaysOriginalForSameKey(String name, String retryBody) {
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer().withBody(body(ANSWER_CONTENT));

        ApiResponse first = addAnswer(questionId, request);
        ApiResponse retry = postAnswer(questionId, request.withBody(retryBody));

        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(retry.status()).as(retry.body()).isEqualTo(201);
        assertThat(retry.header(REPLAYED)).contains("true");
        assertThat(retry.json("$.id")).isEqualTo(first.json("$.id"));
        assertThat(retry.json("$.content")).isEqualTo(ANSWER_CONTENT);
        assertThat(retry.json("$.createdAt")).isEqualTo(first.json("$.createdAt"));
        assertThat(retry.header("Location")).isEqualTo(first.header("Location"));
        ApiResponse question = getQuestion(questionId);
        assertThat(question.json("$.answers[*].id")).isEqualTo(List.of(first.json("$.id")));
        assertThat(question.json("$.answers[0].content")).isEqualTo(ANSWER_CONTENT);
    }

    static Stream<Arguments> retryBodies() {
        return Stream.of(
                arguments("same body", body(ANSWER_CONTENT)),
                arguments("different content", body("A completely different answer.")));
    }

    @Test
    void addsAnswer() {
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer().withBody(body(ANSWER_CONTENT));

        Instant before = Instant.now();
        ApiResponse response = addAnswer(questionId, request);
        Instant after = Instant.now();

        String id = (String) response.json("$.id");
        assertThat(UUID.fromString(id)).hasToString(id);
        assertThat(response.json("$.authorId")).isEqualTo(request.header(USER_ID));
        assertThat(response.json("$.content")).isEqualTo(ANSWER_CONTENT);
        Instant createdAt = Instant.parse((String) response.json("$.createdAt"));
        assertThat(createdAt).isBetween(before, after);
        assertThat(response.json("$.updatedAt")).isNull();
        assertThat(response.json("$.upvotes")).isEqualTo(0);
        assertThat(response.json("$.downvotes")).isEqualTo(0);
        assertThat(response.header("Location")).contains(answersPath(questionId) + "/" + id);
        assertThat(response.header(REPLAYED)).isEmpty();

        ApiResponse question = getQuestion(questionId);
        assertThat(question.json("$.updatedAt")).isNull();
        assertThat(question.json("$.answers.length()")).isEqualTo(1);
        assertThat(question.json("$.answers[0]")).isEqualTo(response.json("$"));
    }

    @Test
    void ignoresServerFieldsInBody() {
        String questionId = createQuestion(RequestSpec.freshUser());
        String clientId = "00000000-0000-0000-0000-000000000001";
        String json = "{\"id\": \"" + clientId + "\", \"authorId\": \"someone-else\", "
                + "\"createdAt\": \"2000-01-01T00:00:00Z\", \"updatedAt\": \"2000-01-02T00:00:00Z\", "
                + "\"tags\": [\"java\"], \"content\": \"" + ANSWER_CONTENT + "\"}";
        RequestSpec request = RequestSpec.validAnswer().withBody(json);

        Instant before = Instant.now();
        ApiResponse response = addAnswer(questionId, request);

        assertThat(response.json("$.id")).isNotEqualTo(clientId);
        assertThat(response.json("$.authorId")).isEqualTo(request.header(USER_ID));
        assertThat(response.json("$.content")).isEqualTo(ANSWER_CONTENT);
        assertThat(Instant.parse((String) response.json("$.createdAt"))).isAfterOrEqualTo(before);
        assertThat(response.json("$.updatedAt")).isNull();
        assertThat(response.json("$")).asInstanceOf(InstanceOfAssertFactories.MAP).doesNotContainKey("tags");
    }

    @Test
    void questionAuthorCanAnswer() {
        String author = RequestSpec.freshUser();
        String questionId = createQuestion(author);

        ApiResponse response = addAnswer(questionId, RequestSpec.validAnswer().withHeader(USER_ID, author));

        assertThat(response.json("$.authorId")).isEqualTo(author);
    }

    @Test
    void unknownQuestionIsNotFound() {
        String questionId = UUID.randomUUID().toString();

        ApiResponse response = postAnswer(questionId, RequestSpec.validAnswer());

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo("QUESTION_NOT_FOUND");
        assertThat(response.json("$.message")).isEqualTo("Question " + questionId + " not found");
    }

    @Test
    void validatesBeforeLookup() {
        ApiResponse response =
                postAnswer(UUID.randomUUID().toString(), RequestSpec.validAnswer().withBody(body("   ")));

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
    }

    @Test
    void secondAnswerConflicts() {
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer();
        ApiResponse first = addAnswer(questionId, request);
        String firstId = (String) first.json("$.id");

        ApiResponse second = postAnswer(questionId, request.withHeader(IDEMPOTENCY_KEY, UUID.randomUUID().toString()));

        assertThat(second.status()).as(second.body()).isEqualTo(409);
        assertThat(second.json("$.error")).isEqualTo("ANSWER_ALREADY_EXISTS");
        assertThat(second.json("$.message"))
                .isEqualTo("Question " + questionId + " already has answer " + firstId + " by this user");
        assertThat(second.header("Location")).isEmpty();
        assertThat(storedAnswerIds(questionId)).isEqualTo(List.of(firstId));
    }

    @Test
    void failedRequestDoesNotRecordKey() {
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer();

        ApiResponse rejected = postAnswer(questionId, request.withBody(body("   ")));
        ApiResponse accepted = postAnswer(questionId, request);

        assertThat(rejected.status()).as(rejected.body()).isEqualTo(400);
        assertThat(accepted.status()).as(accepted.body()).isEqualTo(201);
        assertThat(accepted.header(REPLAYED)).isEmpty();
    }

    @Test
    void scopesKeyPerQuestion() {
        String firstQuestion = createQuestion(RequestSpec.freshUser());
        String secondQuestion = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer();

        ApiResponse first = addAnswer(firstQuestion, request);
        ApiResponse second = addAnswer(secondQuestion, request);

        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(second.header(REPLAYED)).isEmpty();
        assertThat(second.json("$.id")).isNotEqualTo(first.json("$.id"));
        assertThat(storedAnswerIds(firstQuestion)).isEqualTo(List.of(first.json("$.id")));
        assertThat(storedAnswerIds(secondQuestion)).isEqualTo(List.of(second.json("$.id")));
    }

    @Test
    void scopesKeyPerUser() {
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer();

        ApiResponse first = addAnswer(questionId, request);
        ApiResponse other = addAnswer(questionId, request.withHeader(USER_ID, RequestSpec.freshUser()));

        assertThat(other.header(REPLAYED)).isEmpty();
        assertThat(other.json("$.id")).isNotEqualTo(first.json("$.id"));
        assertThat(storedAnswerIds(questionId))
                .isEqualTo(List.of(first.json("$.id"), other.json("$.id")));
    }

    @Test
    void scopesKeyPerOperation() {
        String user = RequestSpec.freshUser();
        String key = UUID.randomUUID().toString();
        ApiResponse question =
                api.post(QUESTIONS, RequestSpec.validCreate().withHeader(USER_ID, user).withHeader(IDEMPOTENCY_KEY, key));
        assertThat(question.status()).as(question.body()).isEqualTo(201);
        String questionId = (String) question.json("$.id");

        ApiResponse answer = addAnswer(questionId,
                RequestSpec.validAnswer().withHeader(USER_ID, user).withHeader(IDEMPOTENCY_KEY, key));

        assertThat(question.header(REPLAYED)).isEmpty();
        assertThat(answer.header(REPLAYED)).isEmpty();
        assertThat(answer.json("$.id")).isNotEqualTo(questionId);
        assertThat(answer.json("$.authorId")).isEqualTo(user);
    }

    @Test
    void listsAnswersOldestFirst() {
        String questionId = createQuestion(RequestSpec.freshUser());

        List<Object> ids = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            ids.add(addAnswer(questionId, RequestSpec.validAnswer()).json("$.id"));
        }

        assertThat(storedAnswerIds(questionId)).isEqualTo(ids);
    }

    @Test
    void parallelAnswersByDifferentUsersAreAllKept() throws Exception {
        String questionId = createQuestion(RequestSpec.freshUser());
        List<RequestSpec> requests =
                IntStream.range(0, PARALLEL_REQUESTS).mapToObj(i -> RequestSpec.validAnswer()).toList();

        List<ApiResponse> responses = postInParallel(answersPath(questionId), requests);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).as(response.body()).isEqualTo(201));
        Set<Object> ids = distinctIds(responses);
        assertThat(ids).hasSize(PARALLEL_REQUESTS);
        assertThat(storedAnswerIds(questionId)).hasSize(PARALLEL_REQUESTS).containsExactlyInAnyOrderElementsOf(ids);
    }

    @Test
    void parallelAnswersBySameUserCreateOne() throws Exception {
        String questionId = createQuestion(RequestSpec.freshUser());
        String user = RequestSpec.freshUser();
        List<RequestSpec> requests = IntStream.range(0, PARALLEL_REQUESTS)
                .mapToObj(i -> RequestSpec.validAnswer().withHeader(USER_ID, user))
                .toList();

        List<ApiResponse> responses = postInParallel(answersPath(questionId), requests);

        List<ApiResponse> created = responses.stream().filter(response -> response.status() == 201).toList();
        assertThat(created).hasSize(1);
        Object id = created.get(0).json("$.id");
        assertThat(responses).filteredOn(response -> response.status() == 409)
                .hasSize(PARALLEL_REQUESTS - 1)
                .allSatisfy(response -> {
                    assertThat(response.json("$.error")).isEqualTo("ANSWER_ALREADY_EXISTS");
                    assertThat((String) response.json("$.message")).contains((String) id);
                });
        assertThat(storedAnswerIds(questionId)).isEqualTo(List.of(id));
    }

    @Test
    void parallelRetriesCreateOneAnswer() throws Exception {
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswer();
        List<RequestSpec> requests = IntStream.range(0, PARALLEL_REQUESTS).mapToObj(i -> request).toList();

        List<ApiResponse> responses = postInParallel(answersPath(questionId), requests);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).as(response.body()).isEqualTo(201));
        Set<Object> ids = distinctIds(responses);
        assertThat(ids).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isEmpty()).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isPresent())
                .hasSize(PARALLEL_REQUESTS - 1);
        assertThat(storedAnswerIds(questionId)).containsExactlyElementsOf(ids);
    }

    // Each edit builds on the stored question, so it keeps the answers added around it.
    @Test
    void questionEditsRacingAnswersKeepBoth() throws Exception {
        String author = RequestSpec.freshUser();
        String questionId = createQuestion(author);
        List<String> edits = IntStream.range(0, RACING_REQUESTS).mapToObj(i -> "edit-" + i).toList();
        String questionPath = QUESTIONS + "/" + questionId;
        List<Callable<ApiResponse>> calls = new ArrayList<>();
        for (String edit : edits) {
            calls.add(() -> api.put(questionPath, RequestSpec.validUpdate(author).withBody(body(edit))));
        }
        for (int i = 0; i < RACING_REQUESTS; i++) {
            calls.add(() -> api.post(answersPath(questionId), RequestSpec.validAnswer()));
        }

        List<ApiResponse> responses = runTogether(calls);

        List<ApiResponse> editResponses = responses.subList(0, RACING_REQUESTS);
        List<ApiResponse> addResponses = responses.subList(RACING_REQUESTS, responses.size());
        assertThat(editResponses).allSatisfy(response -> assertThat(response.status()).isEqualTo(200));
        assertThat(addResponses).allSatisfy(response -> assertThat(response.status()).isEqualTo(201));
        assertThat(getQuestion(questionId).json("$.content")).isIn(edits);
        assertThat(storedAnswerIds(questionId)).hasSize(RACING_REQUESTS)
                .containsExactlyInAnyOrderElementsOf(distinctIds(addResponses));
    }

    private String createQuestion(String authorId) {
        ApiResponse response = api.post(QUESTIONS, RequestSpec.validCreate().withHeader(USER_ID, authorId));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return (String) response.json("$.id");
    }

    private ApiResponse addAnswer(String questionId, RequestSpec request) {
        ApiResponse response = postAnswer(questionId, request);
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    private ApiResponse postAnswer(String questionId, RequestSpec request) {
        return api.post(answersPath(questionId), request);
    }

    private ApiResponse getQuestion(String questionId) {
        ApiResponse response = api.get(QUESTIONS + "/" + questionId, Map.of());
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return response;
    }

    @SuppressWarnings("unchecked")
    private List<Object> storedAnswerIds(String questionId) {
        return (List<Object>) getQuestion(questionId).json("$.answers[*].id");
    }

    private List<ApiResponse> postInParallel(String path, List<RequestSpec> requests) throws Exception {
        List<Callable<ApiResponse>> calls = new ArrayList<>();
        for (RequestSpec request : requests) {
            calls.add(() -> api.post(path, request));
        }
        return runTogether(calls);
    }

    // Every thread waits on the start latch, so all requests are released together and really overlap.
    private static List<ApiResponse> runTogether(List<Callable<ApiResponse>> calls) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(calls.size());
        CountDownLatch ready = new CountDownLatch(calls.size());
        CountDownLatch start = new CountDownLatch(1);
        try {
            List<Future<ApiResponse>> futures = new ArrayList<>();
            for (Callable<ApiResponse> call : calls) {
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();
                    return call.call();
                }));
            }
            assertThat(ready.await(10, TimeUnit.SECONDS)).isTrue();
            start.countDown();

            List<ApiResponse> responses = new ArrayList<>();
            for (Future<ApiResponse> future : futures) {
                responses.add(future.get(60, TimeUnit.SECONDS));
            }
            return responses;
        } finally {
            pool.shutdownNow();
        }
    }

    private static Set<Object> distinctIds(List<ApiResponse> responses) {
        return responses.stream().map(response -> response.json("$.id")).collect(Collectors.toSet());
    }

    private static String answersPath(String questionId) {
        return QUESTIONS + "/" + questionId + "/answers";
    }

    private static Arguments invalid(String name, UnaryOperator<RequestSpec> change, int status, String error) {
        return arguments(name, change, status, error);
    }

    private static Arguments boundary(String name, UnaryOperator<RequestSpec> change) {
        return arguments(name, change);
    }

    private static String body(String content) {
        return "{\"content\": \"" + content + "\"}";
    }

    private static String uniqueOfLength(int length) {
        String seed = UUID.randomUUID().toString().replace("-", "");
        return (seed + "x".repeat(length)).substring(0, length);
    }
}
