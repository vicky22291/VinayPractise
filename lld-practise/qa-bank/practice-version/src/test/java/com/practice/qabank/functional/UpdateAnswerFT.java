package com.practice.qabank.functional;

import static com.practice.qabank.functional.RequestSpec.CONTENT_TYPE;
import static com.practice.qabank.functional.RequestSpec.IDEMPOTENCY_KEY;
import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import java.util.function.UnaryOperator;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.assertj.core.api.InstanceOfAssertFactories;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.jayway.jsonpath.JsonPath;

// Black-box tests for PUT /questions/{questionId}/answers/{answerId} against a running app (see qabank.baseUrl). Test
// data is created only through the API. It's read back through GET /questions/{id}, whose answers entries are the
// same AnswerResponse that GET answer returns. Each test uses fresh users and keys.
@Tag("api")
class UpdateAnswerFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final String ANSWER_CONTENT = "Use compute() or merge(). Both run atomically per key.";
    private static final String EDITED_CONTENT =
            "Use compute() or merge(). Both run atomically per key, so no explicit lock is needed.";
    private static final int PARALLEL_REQUESTS = 50;
    private static final int RACING_REQUESTS = 25;

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void rejectsInvalidRequest(String name, UnaryOperator<RequestSpec> change, int status, String error) {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);

        ApiResponse response =
                api.put(answerPath(questionId, added), change.apply(RequestSpec.validAnswerUpdate(user)));

        assertThat(response.status()).as(response.body()).isEqualTo(status);
        assertThat(response.json("$.error")).isEqualTo(error);
        assertThat((String) response.json("$.message")).isNotBlank();
        assertThat(storedAnswer(questionId, added)).isEqualTo(added.json("$"));
    }

    // AddAnswerFT's rows.
    static Stream<Arguments> invalidRequests() {
        return Stream.of(
                arguments("missing X-User-Id", change(spec -> spec.withoutHeader(USER_ID)), 400, "MISSING_HEADER"),
                arguments("missing Idempotency-Key", change(spec -> spec.withoutHeader(IDEMPOTENCY_KEY)), 400,
                        "MISSING_HEADER"),
                arguments("blank X-User-Id", change(spec -> spec.withHeader(USER_ID, "   ")), 400,
                        "VALIDATION_FAILED"),
                arguments("X-User-Id of 65 chars", change(spec -> spec.withHeader(USER_ID, uniqueOfLength(65))), 400,
                        "VALIDATION_FAILED"),
                arguments("blank Idempotency-Key", change(spec -> spec.withHeader(IDEMPOTENCY_KEY, "   ")), 400,
                        "VALIDATION_FAILED"),
                arguments("Idempotency-Key of 65 chars",
                        change(spec -> spec.withHeader(IDEMPOTENCY_KEY, uniqueOfLength(65))), 400,
                        "VALIDATION_FAILED"),
                arguments("no content", change(spec -> spec.withBody("{}")), 400, "VALIDATION_FAILED"),
                arguments("blank content", change(spec -> spec.withBody(body("   "))), 400, "VALIDATION_FAILED"),
                arguments("content of 5001 chars", change(spec -> spec.withBody(body("x".repeat(5001)))), 400,
                        "VALIDATION_FAILED"),
                arguments("body is not JSON", change(spec -> spec.withBody("{not json")), 400, "MALFORMED_REQUEST"),
                arguments("Content-Type text/plain", change(spec -> spec.withHeader(CONTENT_TYPE, "text/plain")), 415,
                        "UNSUPPORTED_MEDIA_TYPE"));
    }

    // GetQuestionFT's rows, once as each path segment with a random UUID in the other.
    @ParameterizedTest(name = "{0}")
    @MethodSource("com.practice.qabank.functional.GetQuestionFT#malformedIds")
    void rejectsMalformedQuestionId(String name, String id) {
        ApiResponse response = api.put(answerPath(id, UUID.randomUUID().toString()),
                RequestSpec.validAnswerUpdate(RequestSpec.freshUser()));

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo("questionId must be a UUID");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("com.practice.qabank.functional.GetQuestionFT#malformedIds")
    void rejectsMalformedAnswerId(String name, String id) {
        ApiResponse response = api.put(answerPath(UUID.randomUUID().toString(), id),
                RequestSpec.validAnswerUpdate(RequestSpec.freshUser()));

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo("answerId must be a UUID");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("boundaryValues")
    void acceptsBoundaryValue(String name, UnaryOperator<RequestSpec> change) {
        RequestSpec request = change.apply(RequestSpec.validAnswerUpdate(RequestSpec.freshUser()));
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, request.header(USER_ID));

        ApiResponse response = api.put(answerPath(questionId, added), request);

        assertApplied(response, questionId, added, request);
    }

    static Stream<Arguments> boundaryValues() {
        return Stream.of(
                arguments("X-User-Id of 64 chars", change(spec -> spec.withHeader(USER_ID, uniqueOfLength(64)))),
                arguments("Idempotency-Key of 64 chars",
                        change(spec -> spec.withHeader(IDEMPOTENCY_KEY, uniqueOfLength(64)))),
                arguments("content of 5000 chars", change(spec -> spec.withBody(body("x".repeat(5000))))));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("unknownIds")
    void rejectsUnknownIds(String name, Function<Fixture, String> path, String error) {
        Fixture fixture = fixture();
        Object answer = storedAnswerById(fixture.questionId(), fixture.answerId());
        Object otherAnswer = storedAnswerById(fixture.otherQuestionId(), fixture.otherAnswerId());
        String target = path.apply(fixture);

        ApiResponse response = api.put(target, RequestSpec.validAnswerUpdate(fixture.userId()));

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo(error);
        assertThat((String) response.json("$.message")).contains(target.split("/")[2]);
        assertThat(storedAnswerById(fixture.questionId(), fixture.answerId())).isEqualTo(answer);
        assertThat(storedAnswerById(fixture.otherQuestionId(), fixture.otherAnswerId())).isEqualTo(otherAnswer);
    }

    // The fixture's user wrote both answers, so only the lookup can fail.
    static Stream<Arguments> unknownIds() {
        return Stream.of(
                arguments("random question id, the fixture's answer id",
                        path(f -> answerPath(UUID.randomUUID().toString(), f.answerId())), "QUESTION_NOT_FOUND"),
                arguments("the fixture's question, a random answer id",
                        path(f -> answerPath(f.questionId(), UUID.randomUUID().toString())), "ANSWER_NOT_FOUND"),
                arguments("the fixture's question, the other question's answer id",
                        path(f -> answerPath(f.questionId(), f.otherAnswerId())), "ANSWER_NOT_FOUND"));
    }

    // The caller reuses the author's key: a 403, not a replay of the author's edit.
    @ParameterizedTest(name = "{0}")
    @MethodSource("nonOwners")
    void rejectsNonOwner(String name, boolean questionAuthor) {
        String questionAuthorId = RequestSpec.freshUser();
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(questionAuthorId);
        ApiResponse added = answerAs(questionId, user);
        RequestSpec ownerEdit = RequestSpec.validAnswerUpdate(user);
        ApiResponse edited = api.put(answerPath(questionId, added), ownerEdit);
        assertThat(edited.status()).as(edited.body()).isEqualTo(200);

        String caller = questionAuthor ? questionAuthorId : RequestSpec.freshUser();
        RequestSpec otherEdit = RequestSpec.validAnswerUpdate(caller)
                .withHeader(IDEMPOTENCY_KEY, ownerEdit.header(IDEMPOTENCY_KEY));
        ApiResponse response = api.put(answerPath(questionId, added), otherEdit);

        assertThat(response.status()).as(response.body()).isEqualTo(403);
        assertThat(response.json("$.error")).isEqualTo("NOT_ANSWER_OWNER");
        assertThat(response.json("$.message")).isEqualTo("Only the author can update answer " + added.json("$.id"));
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(storedAnswer(questionId, added)).isEqualTo(edited.json("$"));
    }

    static Stream<Arguments> nonOwners() {
        return Stream.of(
                arguments("another user", false),
                arguments("the question's author", true));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("updatedAtCases")
    void setsUpdatedAtOnlyOnChange(String name, String suffix, boolean changed) {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = addAnswer(questionId,
                RequestSpec.validAnswer().withHeader(USER_ID, user).withBody(body(ANSWER_CONTENT)));

        Instant before = Instant.now();
        ApiResponse response = api.put(answerPath(questionId, added),
                RequestSpec.validAnswerUpdate(user).withBody(body(ANSWER_CONTENT + suffix)));
        Instant after = Instant.now();

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(response.json("$.content")).isEqualTo(ANSWER_CONTENT + suffix);
        if (changed) {
            assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBetween(before, after);
        } else {
            assertThat(response.json("$")).isEqualTo(added.json("$"));
            assertThat(response.json("$.updatedAt")).isNull();
        }
        assertThat(storedAnswer(questionId, added)).isEqualTo(response.json("$"));
    }

    // The answer was added with ANSWER_CONTENT. Content isn't trimmed, so a trailing space is a change.
    static Stream<Arguments> updatedAtCases() {
        return Stream.of(
                arguments("same content is a no-op", "", false),
                arguments("an added \"!\" is a change", "!", true),
                arguments("an added trailing space is a change", " ", true));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("retryBodies")
    void replaysOriginalForSameKey(String name, String retryBody) {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        RequestSpec request = RequestSpec.validAnswerUpdate(user).withBody(body(EDITED_CONTENT));

        ApiResponse first = api.put(answerPath(questionId, added), request);
        ApiResponse retry = api.put(answerPath(questionId, added), request.withBody(retryBody));

        assertThat(first.status()).as(first.body()).isEqualTo(200);
        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(retry.status()).as(retry.body()).isEqualTo(200);
        assertThat(retry.header(REPLAYED)).contains("true");
        assertThat(retry.json("$")).isEqualTo(first.json("$"));
        assertThat(storedAnswer(questionId, added)).isEqualTo(first.json("$"));
    }

    static Stream<Arguments> retryBodies() {
        return Stream.of(
                arguments("same body", body(EDITED_CONTENT)),
                arguments("different content", body("A completely different edit.")));
    }

    @Test
    void updatesAnswer() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);

        Instant before = Instant.now();
        ApiResponse response = api.put(answerPath(questionId, added),
                RequestSpec.validAnswerUpdate(user).withBody(body(EDITED_CONTENT)));
        Instant after = Instant.now();

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(added.json("$.id"));
        assertThat(response.json("$.authorId")).isEqualTo(user);
        assertThat(response.json("$.createdAt")).isEqualTo(added.json("$.createdAt"));
        assertThat(response.json("$.content")).isEqualTo(EDITED_CONTENT);
        assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBetween(before, after);
        assertThat(response.header("Location")).isEmpty();
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(storedAnswer(questionId, added)).isEqualTo(response.json("$"));
    }

    @Test
    void keepsOtherAnswersAndQuestion() {
        String questionId = createQuestion(RequestSpec.freshUser());
        String userB = RequestSpec.freshUser();
        ApiResponse answerA = answerAs(questionId, RequestSpec.freshUser());
        ApiResponse answerB = answerAs(questionId, userB);
        ApiResponse answerC = answerAs(questionId, RequestSpec.freshUser());
        ApiResponse beforeEdit = getQuestion(questionId);

        ApiResponse edited = api.put(answerPath(questionId, answerB), RequestSpec.validAnswerUpdate(userB));

        assertThat(edited.status()).as(edited.body()).isEqualTo(200);
        ApiResponse afterEdit = getQuestion(questionId);
        assertThat(afterEdit.json("$.answers"))
                .isEqualTo(List.of(answerA.json("$"), edited.json("$"), answerC.json("$")));
        assertThat(withoutAnswers(afterEdit)).isEqualTo(withoutAnswers(beforeEdit));
        assertThat(afterEdit.json("$.updatedAt")).isNull();
    }

    @Test
    void repeatedPutIsNoOp() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        RequestSpec request = RequestSpec.validAnswerUpdate(user);

        ApiResponse first = api.put(answerPath(questionId, added), request);
        ApiResponse second = api.put(answerPath(questionId, added),
                request.withHeader(IDEMPOTENCY_KEY, UUID.randomUUID().toString()));

        assertThat(first.status()).as(first.body()).isEqualTo(200);
        assertThat(second.status()).as(second.body()).isEqualTo(200);
        assertThat(first.json("$.updatedAt")).isNotNull();
        assertThat(second.json("$")).isEqualTo(first.json("$"));
        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(second.header(REPLAYED)).isEmpty();
    }

    @Test
    void laterEditMovesUpdatedAt() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);

        ApiResponse first = api.put(answerPath(questionId, added), RequestSpec.validAnswerUpdate(user));
        ApiResponse second = api.put(answerPath(questionId, added), RequestSpec.validAnswerUpdate(user));

        assertThat(first.status()).as(first.body()).isEqualTo(200);
        assertThat(second.status()).as(second.body()).isEqualTo(200);
        assertThat(Instant.parse((String) second.json("$.updatedAt")))
                .isAfter(Instant.parse((String) first.json("$.updatedAt")));
    }

    @Test
    void ignoresServerFieldsInBody() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        String clientTime = "2000-01-01T00:00:00Z";
        String json = "{\"id\": \"" + UUID.randomUUID() + "\", \"authorId\": \"" + RequestSpec.freshUser() + "\", "
                + "\"createdAt\": \"" + clientTime + "\", \"updatedAt\": \"" + clientTime + "\", "
                + "\"content\": \"" + EDITED_CONTENT + "\"}";

        Instant before = Instant.now();
        ApiResponse response =
                api.put(answerPath(questionId, added), RequestSpec.validAnswerUpdate(user).withBody(json));
        Instant after = Instant.now();

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(added.json("$.id"));
        assertThat(response.json("$.authorId")).isEqualTo(user);
        assertThat(response.json("$.createdAt")).isEqualTo(added.json("$.createdAt"));
        assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBetween(before, after);
        assertThat(response.json("$.content")).isEqualTo(EDITED_CONTENT);
    }

    @Test
    void validatesBeforeLookup() {
        RequestSpec request = RequestSpec.validAnswerUpdate(RequestSpec.freshUser()).withBody(body("   "));

        ApiResponse response =
                api.put(answerPath(UUID.randomUUID().toString(), UUID.randomUUID().toString()), request);

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
    }

    @Test
    void validatesBeforeOwnership() {
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validAnswerUpdate(RequestSpec.freshUser()).withBody(body("   "));

        ApiResponse response = api.put(answerPath(questionId, added), request);

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(storedAnswer(questionId, added)).isEqualTo(added.json("$"));
    }

    @Test
    void scopesKeyPerAnswer() {
        String user = RequestSpec.freshUser();
        String firstQuestion = createQuestion(RequestSpec.freshUser());
        String secondQuestion = createQuestion(RequestSpec.freshUser());
        ApiResponse firstAnswer = answerAs(firstQuestion, user);
        ApiResponse secondAnswer = answerAs(secondQuestion, user);
        RequestSpec firstEdit = RequestSpec.validAnswerUpdate(user);
        RequestSpec secondEdit =
                RequestSpec.validAnswerUpdate(user).withHeader(IDEMPOTENCY_KEY, firstEdit.header(IDEMPOTENCY_KEY));

        ApiResponse first = api.put(answerPath(firstQuestion, firstAnswer), firstEdit);
        ApiResponse second = api.put(answerPath(secondQuestion, secondAnswer), secondEdit);

        assertApplied(first, firstQuestion, firstAnswer, firstEdit);
        assertApplied(second, secondQuestion, secondAnswer, secondEdit);
    }

    @Test
    void scopesKeyPerOperation() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec add = RequestSpec.validAnswer().withHeader(USER_ID, user);
        ApiResponse added = addAnswer(questionId, add);
        RequestSpec edit = RequestSpec.validAnswerUpdate(user).withHeader(IDEMPOTENCY_KEY, add.header(IDEMPOTENCY_KEY));

        ApiResponse response = api.put(answerPath(questionId, added), edit);

        assertApplied(response, questionId, added, edit);
    }

    @Test
    void failedRequestDoesNotRecordKey() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        RequestSpec request = RequestSpec.validAnswerUpdate(user);

        ApiResponse rejected = api.put(answerPath(questionId, added), request.withBody(body("   ")));
        ApiResponse accepted = api.put(answerPath(questionId, added), request);

        assertThat(rejected.status()).as(rejected.body()).isEqualTo(400);
        assertApplied(accepted, questionId, added, request);
    }

    @Test
    void retriedOldPutDoesNotRevert() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        RequestSpec editA = RequestSpec.validAnswerUpdate(user);
        RequestSpec editB = RequestSpec.validAnswerUpdate(user);

        ApiResponse responseA = api.put(answerPath(questionId, added), editA);
        ApiResponse responseB = api.put(answerPath(questionId, added), editB);
        ApiResponse retryA = api.put(answerPath(questionId, added), editA);

        assertThat(responseA.status()).as(responseA.body()).isEqualTo(200);
        assertThat(responseB.status()).as(responseB.body()).isEqualTo(200);
        assertThat(retryA.status()).as(retryA.body()).isEqualTo(200);
        assertThat(retryA.header(REPLAYED)).contains("true");
        assertThat(retryA.json("$")).isEqualTo(responseA.json("$"));
        assertThat(storedAnswer(questionId, added)).isEqualTo(responseB.json("$"));
    }

    @Test
    void addReplayAfterEditReturnsOriginal() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        RequestSpec add = RequestSpec.validAnswer().withHeader(USER_ID, user).withBody(body(ANSWER_CONTENT));
        ApiResponse added = addAnswer(questionId, add);
        ApiResponse edited = api.put(answerPath(questionId, added), RequestSpec.validAnswerUpdate(user));
        assertThat(edited.status()).as(edited.body()).isEqualTo(200);

        ApiResponse replay = api.post(answersPath(questionId), add);

        assertThat(replay.status()).as(replay.body()).isEqualTo(201);
        assertThat(replay.header(REPLAYED)).contains("true");
        assertThat(replay.json("$.content")).isEqualTo(ANSWER_CONTENT);
        assertThat(replay.json("$.updatedAt")).isNull();
        assertThat(replay.json("$")).isEqualTo(added.json("$"));
        assertThat(storedAnswer(questionId, added)).isEqualTo(edited.json("$"));
    }

    @Test
    void parallelEditsEndInOneSubmittedState() throws Exception {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        String path = answerPath(questionId, added);
        List<Callable<ApiResponse>> edits = IntStream.range(0, PARALLEL_REQUESTS)
                .mapToObj(i -> RequestSpec.validAnswerUpdate(user).withBody(body("edit-" + i)))
                .<Callable<ApiResponse>>map(request -> () -> api.put(path, request))
                .toList();

        List<ApiResponse> responses = runTogether(edits);
        Object finalState = storedAnswer(questionId, added);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).isEqualTo(200));
        assertThat(responses).filteredOn(response -> response.json("$").equals(finalState)).hasSize(1);
        Instant finalUpdatedAt = Instant.parse((String) JsonPath.read(finalState, "$.updatedAt"));
        assertThat(responses).allSatisfy(response ->
                assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBeforeOrEqualTo(finalUpdatedAt));
    }

    @Test
    void parallelRetriesApplyOnce() throws Exception {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        String path = answerPath(questionId, added);
        RequestSpec request = RequestSpec.validAnswerUpdate(user);
        List<Callable<ApiResponse>> retries = IntStream.range(0, PARALLEL_REQUESTS)
                .<Callable<ApiResponse>>mapToObj(i -> () -> api.put(path, request))
                .toList();

        List<ApiResponse> responses = runTogether(retries);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).isEqualTo(200));
        assertThat(responses.stream().map(response -> response.json("$")).distinct()).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isEmpty()).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isPresent())
                .hasSize(PARALLEL_REQUESTS - 1);
        assertThat(storedAnswer(questionId, added)).isEqualTo(responses.get(0).json("$"));
    }

    @Test
    void answerEditsRacingAnswerAddsKeepAll() throws Exception {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        ApiResponse added = answerAs(questionId, user);
        String path = answerPath(questionId, added);
        List<String> edits = IntStream.range(0, RACING_REQUESTS).mapToObj(i -> "edit-" + i).toList();
        List<Callable<ApiResponse>> calls = new ArrayList<>();
        for (String edit : edits) {
            calls.add(() -> api.put(path, RequestSpec.validAnswerUpdate(user).withBody(body(edit))));
        }
        for (int i = 0; i < RACING_REQUESTS; i++) {
            calls.add(() -> api.post(answersPath(questionId), RequestSpec.validAnswer()));
        }

        List<ApiResponse> responses = runTogether(calls);

        List<ApiResponse> editResponses = responses.subList(0, RACING_REQUESTS);
        List<ApiResponse> addResponses = responses.subList(RACING_REQUESTS, responses.size());
        assertThat(editResponses).allSatisfy(response -> assertThat(response.status()).isEqualTo(200));
        assertThat(addResponses).allSatisfy(response -> assertThat(response.status()).isEqualTo(201));
        ApiResponse question = getQuestion(questionId);
        assertThat(question.json("$.answers.length()")).isEqualTo(RACING_REQUESTS + 1);
        assertThat(question.json("$.answers[0].id")).isEqualTo(added.json("$.id"));
        assertThat(question.json("$.answers[0].content")).isIn(edits);
        List<Object> addedIds = addResponses.stream().map(response -> response.json("$.id")).toList();
        assertThat(question.json("$.answers[1:].id")).asInstanceOf(InstanceOfAssertFactories.LIST)
                .containsExactlyInAnyOrderElementsOf(addedIds);
    }

    // A fresh, real edit: 200, the sent content, no replay header, and GET question shows it.
    private void assertApplied(ApiResponse response, String questionId, ApiResponse added, RequestSpec request) {
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(response.json("$.id")).isEqualTo(added.json("$.id"));
        assertThat(response.json("$.content")).isEqualTo(JsonPath.read(request.body(), "$.content"));
        assertThat(response.json("$.updatedAt")).isNotNull();
        assertThat(storedAnswer(questionId, added)).isEqualTo(response.json("$"));
    }

    // Every task waits on the start latch, so all requests are released together and really overlap.
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

    // Two questions, both answered by one fresh user.
    private Fixture fixture() {
        String user = RequestSpec.freshUser();
        String questionId = createQuestion(RequestSpec.freshUser());
        String otherQuestionId = createQuestion(RequestSpec.freshUser());
        ApiResponse answer = answerAs(questionId, user);
        ApiResponse otherAnswer = answerAs(otherQuestionId, user);
        return new Fixture(user, questionId, (String) answer.json("$.id"), otherQuestionId,
                (String) otherAnswer.json("$.id"));
    }

    private String createQuestion(String authorId) {
        ApiResponse response = api.post(QUESTIONS, RequestSpec.validCreate().withHeader(USER_ID, authorId));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return (String) response.json("$.id");
    }

    private ApiResponse addAnswer(String questionId, RequestSpec request) {
        ApiResponse response = api.post(answersPath(questionId), request);
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    private ApiResponse answerAs(String questionId, String userId) {
        return addAnswer(questionId, RequestSpec.validAnswer().withHeader(USER_ID, userId));
    }

    private ApiResponse getQuestion(String questionId) {
        ApiResponse response = api.get(QUESTIONS + "/" + questionId, Map.of());
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return response;
    }

    private Object storedAnswer(String questionId, ApiResponse added) {
        return storedAnswerById(questionId, (String) added.json("$.id"));
    }

    // The answer's entry in GET question, the same AnswerResponse that GET answer returns.
    private Object storedAnswerById(String questionId, String answerId) {
        List<?> matches = (List<?>) getQuestion(questionId).json("$.answers[?(@.id == '" + answerId + "')]");
        assertThat(matches).hasSize(1);
        return matches.get(0);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> withoutAnswers(ApiResponse question) {
        Map<String, Object> fields = new LinkedHashMap<>((Map<String, Object>) question.json("$"));
        fields.remove("answers");
        return fields;
    }

    private static String answersPath(String questionId) {
        return QUESTIONS + "/" + questionId + "/answers";
    }

    private static String answerPath(String questionId, ApiResponse added) {
        return answerPath(questionId, (String) added.json("$.id"));
    }

    private static String answerPath(String questionId, String answerId) {
        return answersPath(questionId) + "/" + answerId;
    }

    // Give lambdas their target type inside arguments(...).
    private static UnaryOperator<RequestSpec> change(UnaryOperator<RequestSpec> change) {
        return change;
    }

    private static Function<Fixture, String> path(Function<Fixture, String> path) {
        return path;
    }

    private static String body(String content) {
        return "{\"content\": \"" + content + "\"}";
    }

    private static String uniqueOfLength(int length) {
        String seed = UUID.randomUUID().toString().replace("-", "");
        return (seed + "x".repeat(length)).substring(0, length);
    }

    // The other ids are the same user's answer on a second question.
    record Fixture(String userId, String questionId, String answerId, String otherQuestionId, String otherAnswerId) {
    }
}
