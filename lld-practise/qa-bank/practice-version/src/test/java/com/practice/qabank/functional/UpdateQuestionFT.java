package com.practice.qabank.functional;

import static com.practice.qabank.functional.RequestSpec.CONTENT_TYPE;
import static com.practice.qabank.functional.RequestSpec.IDEMPOTENCY_KEY;
import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static com.practice.qabank.functional.RequestSpec.VALID_CONTENT;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.UnaryOperator;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import com.jayway.jsonpath.JsonPath;

// Black-box tests for PUT /questions/{id} against a running app (see qabank.baseUrl). Test data is created only through
// POST /questions and read back only through GET /questions/{id}. Each test creates its own question as a fresh user.
@Tag("api")
class UpdateQuestionFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final int PARALLEL_REQUESTS = 50;

    private static final String CREATED_TAGS = "[\"java\", \"concurrency\"]";
    private static final String EDITED_CONTENT = "How do I make a ConcurrentHashMap value update atomic without locks?";
    private static final String EDITED_TAGS = "[\"java\", \"concurrency\", \"concurrenthashmap\"]";
    private static final String EDIT_BODY = body(EDITED_CONTENT, EDITED_TAGS);

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void rejectsInvalidRequest(String name, UnaryOperator<RequestSpec> change, int status, String error) {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);

        ApiResponse response = api.put(path(created), change.apply(RequestSpec.validUpdate(author)));

        assertThat(response.status()).as(response.body()).isEqualTo(status);
        assertThat(response.json("$.error")).isEqualTo(error);
        assertThat((String) response.json("$.message")).isNotBlank();
        assertThat(get(created).json("$")).isEqualTo(created.json("$"));
    }

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
                arguments("no content", change(spec -> spec.withBody("{\"tags\": [\"java\"]}")), 400,
                        "VALIDATION_FAILED"),
                arguments("blank content", change(spec -> spec.withBody(body("   ", null))), 400, "VALIDATION_FAILED"),
                arguments("content of 5001 chars", change(spec -> spec.withBody(body("x".repeat(5001), null))), 400,
                        "VALIDATION_FAILED"),
                arguments("6 tags", change(spec -> spec.withBody(
                        body(EDITED_CONTENT, "[\"a\", \"b\", \"c\", \"d\", \"e\", \"f\"]"))), 400, "VALIDATION_FAILED"),
                arguments("empty tag", change(spec -> spec.withBody(body(EDITED_CONTENT, "[\"\"]"))), 400,
                        "VALIDATION_FAILED"),
                arguments("null tag", change(spec -> spec.withBody(body(EDITED_CONTENT, "[null]"))), 400,
                        "VALIDATION_FAILED"),
                arguments("tag with a space", change(spec -> spec.withBody(body(EDITED_CONTENT, "[\"spring boot\"]"))),
                        400, "VALIDATION_FAILED"),
                arguments("tag of 36 chars",
                        change(spec -> spec.withBody(body(EDITED_CONTENT, "[\"" + "t".repeat(36) + "\"]"))), 400,
                        "VALIDATION_FAILED"),
                arguments("body is not JSON", change(spec -> spec.withBody("{not json")), 400, "MALFORMED_REQUEST"),
                arguments("tags is not an array", change(spec -> spec.withBody(body(EDITED_CONTENT, "\"java\""))), 400,
                        "MALFORMED_REQUEST"),
                arguments("Content-Type text/plain", change(spec -> spec.withHeader(CONTENT_TYPE, "text/plain")), 415,
                        "UNSUPPORTED_MEDIA_TYPE"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("com.practice.qabank.functional.GetQuestionFT#malformedIds")
    void rejectsMalformedId(String name, String id) {
        ApiResponse response = api.put(QUESTIONS + "/" + id, RequestSpec.validUpdate(RequestSpec.freshUser()));

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo("id must be a UUID");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("boundaryValues")
    void acceptsBoundaryValue(String name, UnaryOperator<RequestSpec> change) {
        RequestSpec request = change.apply(RequestSpec.validUpdate(RequestSpec.freshUser()));
        ApiResponse created = create(request.header(USER_ID));

        ApiResponse response = api.put(path(created), request);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.header(REPLAYED)).isEmpty();
    }

    static Stream<Arguments> boundaryValues() {
        return Stream.of(
                arguments("X-User-Id of 64 chars", change(spec -> spec.withHeader(USER_ID, uniqueOfLength(64)))),
                arguments("Idempotency-Key of 64 chars",
                        change(spec -> spec.withHeader(IDEMPOTENCY_KEY, uniqueOfLength(64)))),
                arguments("content of 5000 chars", change(spec -> spec.withBody(body("x".repeat(5000), null)))),
                arguments("5 tags",
                        change(spec -> spec.withBody(body(EDITED_CONTENT, "[\"a\", \"b\", \"c\", \"d\", \"e\"]")))),
                arguments("tag of 1 char", change(spec -> spec.withBody(body(EDITED_CONTENT, "[\"r\"]")))),
                arguments("tag of 35 chars",
                        change(spec -> spec.withBody(body(EDITED_CONTENT, "[\"" + "t".repeat(35) + "\"]")))));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("tagNormalization")
    void normalizesTags(String name, String tagsJson, List<String> expected) {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);

        RequestSpec request = RequestSpec.validUpdate(author).withBody(body(EDITED_CONTENT, tagsJson));

        ApiResponse response = api.put(path(created), request);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.tags")).isEqualTo(expected);
        assertThat(get(created).json("$.tags")).isEqualTo(expected);
    }

    static Stream<Arguments> tagNormalization() {
        return Stream.of(
                arguments("no tags field clears the created tags", null, List.of()),
                arguments("empty array", "[]", List.of()),
                arguments("lowercased and deduplicated", "[\"Java\", \"java\", \"Concurrency\"]",
                        List.of("java", "concurrency")),
                arguments("symbols kept", "[\"C#\", \"c#\", \"C++\"]", List.of("c#", "c++")));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("updatedAtCases")
    void setsUpdatedAtOnlyOnChange(String name, String body, boolean changed) {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);

        Instant before = Instant.now();
        ApiResponse response = api.put(path(created), RequestSpec.validUpdate(author).withBody(body));
        Instant after = Instant.now();

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        if (changed) {
            assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBetween(before, after);
        } else {
            assertThat(response.json("$")).isEqualTo(created.json("$"));
            assertThat(response.json("$.updatedAt")).isNull();
        }
    }

    // The question was created with VALID_CONTENT and ["java", "concurrency"].
    static Stream<Arguments> updatedAtCases() {
        return Stream.of(
                arguments("same content and tags is a no-op", body(VALID_CONTENT, CREATED_TAGS), false),
                arguments("tags differing only by case and duplicates is a no-op",
                        body(VALID_CONTENT, "[\"JAVA\", \"Java\", \"concurrency\"]"), false),
                arguments("new content is a change", body(VALID_CONTENT + "!", CREATED_TAGS), true),
                arguments("fewer tags is a change", body(VALID_CONTENT, "[\"java\"]"), true),
                arguments("reordered tags is a change", body(VALID_CONTENT, "[\"concurrency\", \"java\"]"), true),
                arguments("no tags field is a change", body(VALID_CONTENT, null), true));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("retryBodies")
    void replaysOriginalForSameKey(String name, String retryBody) {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec request = RequestSpec.validUpdate(author).withBody(EDIT_BODY);

        ApiResponse first = api.put(path(created), request);
        ApiResponse retry = api.put(path(created), request.withBody(retryBody));

        assertThat(first.status()).as(first.body()).isEqualTo(200);
        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(retry.status()).as(retry.body()).isEqualTo(200);
        assertThat(retry.header(REPLAYED)).contains("true");
        assertThat(retry.json("$")).isEqualTo(first.json("$"));
        assertThat(get(created).json("$")).isEqualTo(first.json("$"));
    }

    static Stream<Arguments> retryBodies() {
        return Stream.of(
                arguments("same body", EDIT_BODY),
                arguments("different content", body("A completely different edit?", EDITED_TAGS)),
                arguments("different tags", body(EDITED_CONTENT, "[\"kotlin\"]")));
    }

    @Test
    void updatesQuestion() {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec request = RequestSpec.validUpdate(author)
                .withBody(body(EDITED_CONTENT, "[\"Java\", \"java\", \"ConcurrentHashMap\"]"));

        Instant before = Instant.now();
        ApiResponse response = api.put(path(created), request);
        Instant after = Instant.now();

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(created.json("$.id"));
        assertThat(response.json("$.authorId")).isEqualTo(author);
        assertThat(response.json("$.createdAt")).isEqualTo(created.json("$.createdAt"));
        assertThat(response.json("$.content")).isEqualTo(EDITED_CONTENT);
        assertThat(response.json("$.tags")).isEqualTo(List.of("java", "concurrenthashmap"));
        assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBetween(before, after);
        assertThat(response.header("Location")).isEmpty();
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(get(created).json("$")).isEqualTo(response.json("$"));
    }

    @Test
    void repeatedPutIsNoOp() {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec request = RequestSpec.validUpdate(author);

        ApiResponse first = api.put(path(created), request);
        ApiResponse second = api.put(path(created), request.withHeader(IDEMPOTENCY_KEY, UUID.randomUUID().toString()));

        assertThat(first.status()).as(first.body()).isEqualTo(200);
        assertThat(second.status()).as(second.body()).isEqualTo(200);
        assertThat(second.json("$")).isEqualTo(first.json("$"));
        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(second.header(REPLAYED)).isEmpty();
    }

    @Test
    void laterEditMovesUpdatedAt() {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);

        ApiResponse first = api.put(path(created), RequestSpec.validUpdate(author));
        ApiResponse second = api.put(path(created), RequestSpec.validUpdate(author));

        assertThat(first.status()).as(first.body()).isEqualTo(200);
        assertThat(second.status()).as(second.body()).isEqualTo(200);
        assertThat(Instant.parse((String) second.json("$.updatedAt")))
                .isAfter(Instant.parse((String) first.json("$.updatedAt")));
    }

    @Test
    void ignoresServerFieldsInBody() {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        String clientTime = "2000-01-01T00:00:00Z";
        String json = "{\"id\": \"" + UUID.randomUUID() + "\", \"authorId\": \"" + RequestSpec.freshUser() + "\", "
                + "\"createdAt\": \"" + clientTime + "\", \"updatedAt\": \"" + clientTime + "\", "
                + "\"content\": \"" + EDITED_CONTENT + "\", \"tags\": [\"java\"]}";

        Instant before = Instant.now();
        ApiResponse response = api.put(path(created), RequestSpec.validUpdate(author).withBody(json));
        Instant after = Instant.now();

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(created.json("$.id"));
        assertThat(response.json("$.authorId")).isEqualTo(author);
        assertThat(response.json("$.createdAt")).isEqualTo(created.json("$.createdAt"));
        assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBetween(before, after);
        assertThat(response.json("$.content")).isEqualTo(EDITED_CONTENT);
    }

    @Test
    void unknownIdIsNotFound() {
        String id = UUID.randomUUID().toString();

        ApiResponse response = api.put(QUESTIONS + "/" + id, RequestSpec.validUpdate(RequestSpec.freshUser()));

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo("QUESTION_NOT_FOUND");
        assertThat((String) response.json("$.message")).contains(id);
    }

    @Test
    void nonAuthorIsForbidden() {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec authorEdit = RequestSpec.validUpdate(author);
        ApiResponse edited = api.put(path(created), authorEdit);
        assertThat(edited.status()).as(edited.body()).isEqualTo(200);

        RequestSpec otherEdit = RequestSpec.validUpdate(RequestSpec.freshUser())
                .withHeader(IDEMPOTENCY_KEY, authorEdit.header(IDEMPOTENCY_KEY));
        ApiResponse response = api.put(path(created), otherEdit);

        assertThat(response.status()).as(response.body()).isEqualTo(403);
        assertThat(response.json("$.error")).isEqualTo("NOT_QUESTION_OWNER");
        assertThat(response.json("$.message")).isEqualTo("Only the author can update question " + created.json("$.id"));
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(get(created).json("$")).isEqualTo(edited.json("$"));
    }

    @Test
    void validatesBeforeLookup() {
        RequestSpec request = RequestSpec.validUpdate(RequestSpec.freshUser()).withBody(body("   ", null));

        ApiResponse response = api.put(QUESTIONS + "/" + UUID.randomUUID(), request);

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
    }

    @Test
    void validatesBeforeOwnership() {
        ApiResponse created = create(RequestSpec.freshUser());
        RequestSpec request = RequestSpec.validUpdate(RequestSpec.freshUser()).withBody(body("   ", null));

        ApiResponse response = api.put(path(created), request);

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
    }

    @Test
    void scopesKeyPerQuestion() {
        String author = RequestSpec.freshUser();
        ApiResponse firstQuestion = create(author);
        ApiResponse secondQuestion = create(author);
        RequestSpec firstEdit = RequestSpec.validUpdate(author);
        RequestSpec secondEdit = RequestSpec.validUpdate(author)
                .withHeader(IDEMPOTENCY_KEY, firstEdit.header(IDEMPOTENCY_KEY));

        ApiResponse first = api.put(path(firstQuestion), firstEdit);
        ApiResponse second = api.put(path(secondQuestion), secondEdit);

        assertApplied(first, firstQuestion, firstEdit);
        assertApplied(second, secondQuestion, secondEdit);
    }

    @Test
    void scopesKeyPerOperation() {
        RequestSpec createRequest = RequestSpec.validCreate();
        ApiResponse created = api.post(QUESTIONS, createRequest);
        assertThat(created.status()).as(created.body()).isEqualTo(201);
        RequestSpec edit = RequestSpec.validUpdate(createRequest.header(USER_ID))
                .withHeader(IDEMPOTENCY_KEY, createRequest.header(IDEMPOTENCY_KEY));

        ApiResponse response = api.put(path(created), edit);

        assertApplied(response, created, edit);
    }

    @Test
    void failedRequestDoesNotRecordKey() {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec request = RequestSpec.validUpdate(author);

        ApiResponse rejected = api.put(path(created), request.withBody(body("   ", null)));
        ApiResponse accepted = api.put(path(created), request);

        assertThat(rejected.status()).as(rejected.body()).isEqualTo(400);
        assertApplied(accepted, created, request);
    }

    @Test
    void retriedOldPutDoesNotRevert() {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec editA = RequestSpec.validUpdate(author);
        RequestSpec editB = RequestSpec.validUpdate(author);

        ApiResponse responseA = api.put(path(created), editA);
        ApiResponse responseB = api.put(path(created), editB);
        ApiResponse retryA = api.put(path(created), editA);

        assertThat(responseA.status()).as(responseA.body()).isEqualTo(200);
        assertThat(responseB.status()).as(responseB.body()).isEqualTo(200);
        assertThat(retryA.status()).as(retryA.body()).isEqualTo(200);
        assertThat(retryA.header(REPLAYED)).contains("true");
        assertThat(retryA.json("$")).isEqualTo(responseA.json("$"));
        assertThat(get(created).json("$")).isEqualTo(responseB.json("$"));
    }

    @Test
    void createReplayAfterUpdateReturnsOriginal() {
        RequestSpec createRequest = RequestSpec.validCreate();
        ApiResponse created = api.post(QUESTIONS, createRequest);
        assertThat(created.status()).as(created.body()).isEqualTo(201);
        ApiResponse edited = api.put(path(created), RequestSpec.validUpdate(createRequest.header(USER_ID)));
        assertThat(edited.status()).as(edited.body()).isEqualTo(200);

        ApiResponse replay = api.post(QUESTIONS, createRequest);

        assertThat(replay.status()).as(replay.body()).isEqualTo(201);
        assertThat(replay.header(REPLAYED)).contains("true");
        assertThat(replay.json("$.content")).isEqualTo(VALID_CONTENT);
        assertThat(replay.json("$.tags")).isEqualTo(List.of("java", "concurrency"));
        assertThat(replay.json("$.updatedAt")).isNull();
        assertThat(replay.json("$")).isEqualTo(created.json("$"));
        assertThat(get(created).json("$")).isEqualTo(edited.json("$"));
    }

    @Test
    void parallelEditsEndInOneSubmittedState() throws Exception {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        List<RequestSpec> requests = IntStream.range(0, PARALLEL_REQUESTS)
                .mapToObj(i -> RequestSpec.validUpdate(author).withBody(body("edit-" + i, "[\"tag-" + i + "\"]")))
                .toList();

        List<ApiResponse> responses = putInParallel(path(created), requests);
        ApiResponse finalState = get(created);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).isEqualTo(200));
        assertThat(responses).filteredOn(response -> response.json("$").equals(finalState.json("$"))).hasSize(1);
        Instant finalUpdatedAt = Instant.parse((String) finalState.json("$.updatedAt"));
        assertThat(responses).allSatisfy(response ->
                assertThat(Instant.parse((String) response.json("$.updatedAt"))).isBeforeOrEqualTo(finalUpdatedAt));
    }

    @Test
    void parallelIdenticalPutsAgree() throws Exception {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec request = RequestSpec.validUpdate(author);
        List<RequestSpec> requests = IntStream.range(0, PARALLEL_REQUESTS)
                .mapToObj(i -> request.withHeader(IDEMPOTENCY_KEY, UUID.randomUUID().toString()))
                .toList();

        List<ApiResponse> responses = putInParallel(path(created), requests);

        assertThat(responses).allSatisfy(response -> {
            assertThat(response.status()).isEqualTo(200);
            assertThat(response.header(REPLAYED)).isEmpty();
        });
        assertThat(responses.stream().map(response -> response.json("$")).distinct()).hasSize(1);
    }

    @Test
    void parallelRetriesApplyOnce() throws Exception {
        String author = RequestSpec.freshUser();
        ApiResponse created = create(author);
        RequestSpec request = RequestSpec.validUpdate(author);
        List<RequestSpec> requests = IntStream.range(0, PARALLEL_REQUESTS).mapToObj(i -> request).toList();

        List<ApiResponse> responses = putInParallel(path(created), requests);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).isEqualTo(200));
        assertThat(responses.stream().map(response -> response.json("$")).distinct()).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isEmpty()).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isPresent())
                .hasSize(PARALLEL_REQUESTS - 1);
    }

    // A fresh, real edit: 200, the sent content, no replay header, and GET shows it.
    private void assertApplied(ApiResponse response, ApiResponse created, RequestSpec request) {
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(response.json("$.id")).isEqualTo(created.json("$.id"));
        assertThat(response.json("$.content")).isEqualTo(JsonPath.read(request.body(), "$.content"));
        assertThat(response.json("$.updatedAt")).isNotNull();
        assertThat(get(created).json("$")).isEqualTo(response.json("$"));
    }

    // Every thread waits on the start latch, so all requests are released together and really overlap.
    private List<ApiResponse> putInParallel(String path, List<RequestSpec> requests) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(requests.size());
        CountDownLatch ready = new CountDownLatch(requests.size());
        CountDownLatch start = new CountDownLatch(1);
        try {
            List<Future<ApiResponse>> futures = new ArrayList<>();
            for (RequestSpec request : requests) {
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();
                    return api.put(path, request);
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

    // Creates a question as authorId with VALID_CONTENT and ["java", "concurrency"].
    private ApiResponse create(String authorId) {
        ApiResponse response = api.post(QUESTIONS, RequestSpec.validCreate().withHeader(USER_ID, authorId));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    private ApiResponse get(ApiResponse created) {
        ApiResponse response = api.get(path(created), Map.of());
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return response;
    }

    private static String path(ApiResponse created) {
        return QUESTIONS + "/" + created.json("$.id");
    }

    // Gives a lambda its target type inside arguments(...).
    private static UnaryOperator<RequestSpec> change(UnaryOperator<RequestSpec> change) {
        return change;
    }

    // A JSON body with the given content, plus a "tags" field holding tagsJson as-is (omitted when null).
    private static String body(String content, String tagsJson) {
        String tags = tagsJson == null ? "" : ", \"tags\": " + tagsJson;
        return "{\"content\": \"" + content + "\"" + tags + "}";
    }

    private static String uniqueOfLength(int length) {
        String seed = UUID.randomUUID().toString().replace("-", "");
        return (seed + "x".repeat(length)).substring(0, length);
    }
}
