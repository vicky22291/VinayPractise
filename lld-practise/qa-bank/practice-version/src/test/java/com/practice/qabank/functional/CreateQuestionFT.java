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
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

// Black-box tests for POST /questions against a running app (see qabank.baseUrl). scopesKeyPerOperation also uses
// PUT /questions/{id}.
@Tag("api")
class CreateQuestionFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final int PARALLEL_REQUESTS = 50;

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void rejectsInvalidRequest(String name, RequestSpec request, int status, String error) {
        ApiResponse response = api.post(QUESTIONS, request);

        assertThat(response.status()).as(response.body()).isEqualTo(status);
        assertThat(response.json("$.error")).isEqualTo(error);
        assertThat((String) response.json("$.message")).isNotBlank();
    }

    static Stream<Arguments> invalidRequests() {
        return Stream.of(
                arguments("missing X-User-Id", valid().withoutHeader(USER_ID), 400, "MISSING_HEADER"),
                arguments("missing Idempotency-Key", valid().withoutHeader(IDEMPOTENCY_KEY), 400, "MISSING_HEADER"),
                arguments("blank X-User-Id", valid().withHeader(USER_ID, "   "), 400, "VALIDATION_FAILED"),
                arguments("X-User-Id of 65 chars", valid().withHeader(USER_ID, uniqueOfLength(65)), 400,
                        "VALIDATION_FAILED"),
                arguments("blank Idempotency-Key", valid().withHeader(IDEMPOTENCY_KEY, "   "), 400,
                        "VALIDATION_FAILED"),
                arguments("Idempotency-Key of 65 chars", valid().withHeader(IDEMPOTENCY_KEY, uniqueOfLength(65)), 400,
                        "VALIDATION_FAILED"),
                arguments("no content", valid().withBody("{\"tags\": [\"java\"]}"), 400, "VALIDATION_FAILED"),
                arguments("blank content", valid().withBody(body("   ", null)), 400, "VALIDATION_FAILED"),
                arguments("content of 5001 chars", valid().withBody(body("x".repeat(5001), null)), 400,
                        "VALIDATION_FAILED"),
                arguments("6 tags", valid().withBody(body(VALID_CONTENT, "[\"a\", \"b\", \"c\", \"d\", \"e\", \"f\"]")),
                        400, "VALIDATION_FAILED"),
                arguments("empty tag", valid().withBody(body(VALID_CONTENT, "[\"\"]")), 400, "VALIDATION_FAILED"),
                arguments("null tag", valid().withBody(body(VALID_CONTENT, "[null]")), 400, "VALIDATION_FAILED"),
                arguments("tag with a space", valid().withBody(body(VALID_CONTENT, "[\"spring boot\"]")), 400,
                        "VALIDATION_FAILED"),
                arguments("tag of 36 chars", valid().withBody(body(VALID_CONTENT, "[\"" + "t".repeat(36) + "\"]")), 400,
                        "VALIDATION_FAILED"),
                arguments("body is not JSON", valid().withBody("{not json"), 400, "MALFORMED_REQUEST"),
                arguments("tags is not an array", valid().withBody(body(VALID_CONTENT, "\"java\"")), 400,
                        "MALFORMED_REQUEST"),
                arguments("Content-Type text/plain", valid().withHeader(CONTENT_TYPE, "text/plain"), 415,
                        "UNSUPPORTED_MEDIA_TYPE"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("boundaryValues")
    void acceptsBoundaryValue(String name, RequestSpec request) {
        ApiResponse response = api.post(QUESTIONS, request);

        assertThat(response.status()).as(response.body()).isEqualTo(201);
        assertThat(response.header(REPLAYED)).isEmpty();
    }

    static Stream<Arguments> boundaryValues() {
        return Stream.of(
                arguments("X-User-Id of 64 chars", valid().withHeader(USER_ID, uniqueOfLength(64))),
                arguments("Idempotency-Key of 64 chars", valid().withHeader(IDEMPOTENCY_KEY, uniqueOfLength(64))),
                arguments("content of 5000 chars", valid().withBody(body("x".repeat(5000), null))),
                arguments("5 tags", valid().withBody(body(VALID_CONTENT, "[\"a\", \"b\", \"c\", \"d\", \"e\"]"))),
                arguments("tag of 1 char", valid().withBody(body(VALID_CONTENT, "[\"r\"]"))),
                arguments("tag of 35 chars", valid().withBody(body(VALID_CONTENT, "[\"" + "t".repeat(35) + "\"]"))));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("tagNormalization")
    void normalizesTags(String name, String tagsJson, List<String> expected) {
        ApiResponse response = api.post(QUESTIONS, valid().withBody(body(VALID_CONTENT, tagsJson)));

        assertThat(response.status()).as(response.body()).isEqualTo(201);
        assertThat(response.json("$.tags")).isEqualTo(expected);
    }

    static Stream<Arguments> tagNormalization() {
        return Stream.of(
                arguments("no tags field", null, List.of()),
                arguments("empty array", "[]", List.of()),
                arguments("lowercased and deduplicated", "[\"Java\", \"java\", \"Concurrency\"]",
                        List.of("java", "concurrency")),
                arguments("symbols kept", "[\"C#\", \"c#\", \"C++\"]", List.of("c#", "c++")));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("retryBodies")
    void replaysOriginalForSameKey(String name, String retryBody) {
        RequestSpec request = valid();

        ApiResponse first = api.post(QUESTIONS, request);
        ApiResponse retry = api.post(QUESTIONS, request.withBody(retryBody));

        assertThat(first.status()).as(first.body()).isEqualTo(201);
        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(retry.status()).as(retry.body()).isEqualTo(201);
        assertThat(retry.header(REPLAYED)).contains("true");
        assertThat(retry.json("$.id")).isEqualTo(first.json("$.id"));
        assertThat(retry.json("$.content")).isEqualTo(first.json("$.content"));
        assertThat(retry.json("$.tags")).isEqualTo(first.json("$.tags"));
        assertThat(retry.json("$.createdAt")).isEqualTo(first.json("$.createdAt"));
        assertThat(retry.header("Location")).isEqualTo(first.header("Location"));
    }

    static Stream<Arguments> retryBodies() {
        return Stream.of(
                arguments("same body", RequestSpec.VALID_BODY),
                arguments("different content", body("A completely different question?", "[\"java\", \"concurrency\"]")),
                arguments("different tags", body(VALID_CONTENT, "[\"kotlin\"]")));
    }

    @Test
    void createsQuestion() {
        RequestSpec request = valid();

        Instant before = Instant.now();
        ApiResponse response = api.post(QUESTIONS, request);
        Instant after = Instant.now();

        assertThat(response.status()).as(response.body()).isEqualTo(201);
        String id = (String) response.json("$.id");
        assertThat(UUID.fromString(id)).hasToString(id);
        assertThat(response.json("$.authorId")).isEqualTo(request.header(USER_ID));
        assertThat(response.json("$.content")).isEqualTo(VALID_CONTENT);
        assertThat(response.json("$.tags")).isEqualTo(List.of("java", "concurrency"));
        assertThat(Instant.parse((String) response.json("$.createdAt"))).isBetween(before, after);
        assertThat(response.json("$.updatedAt")).isNull();
        assertThat(response.json("$.upvotes")).isEqualTo(0);
        assertThat(response.json("$.downvotes")).isEqualTo(0);
        assertThat(response.json("$.answers")).isEqualTo(List.of());
        assertThat(response.header("Location")).hasValueSatisfying(location -> assertThat(location).endsWith("/" + id));
        assertThat(response.header(REPLAYED)).isEmpty();
    }

    @Test
    void ignoresClientIdAndCreatedAt() {
        String clientId = "00000000-0000-0000-0000-000000000001";
        String clientCreatedAt = "2000-01-01T00:00:00Z";
        String json = "{\"id\": \"" + clientId + "\", \"createdAt\": \"" + clientCreatedAt + "\", "
                + "\"content\": \"" + VALID_CONTENT + "\", \"tags\": [\"java\"]}";

        Instant before = Instant.now();
        ApiResponse response = api.post(QUESTIONS, valid().withBody(json));

        assertThat(response.status()).as(response.body()).isEqualTo(201);
        assertThat(response.json("$.id")).isNotEqualTo(clientId);
        assertThat(Instant.parse((String) response.json("$.createdAt"))).isAfterOrEqualTo(before);
    }

    @Test
    void differentKeysCreateDifferentQuestions() {
        RequestSpec first = valid();
        RequestSpec second = first.withHeader(IDEMPOTENCY_KEY, UUID.randomUUID().toString());

        ApiResponse firstResponse = api.post(QUESTIONS, first);
        ApiResponse secondResponse = api.post(QUESTIONS, second);

        assertThat(firstResponse.status()).isEqualTo(201);
        assertThat(secondResponse.status()).isEqualTo(201);
        assertThat(secondResponse.header(REPLAYED)).isEmpty();
        assertThat(secondResponse.json("$.id")).isNotEqualTo(firstResponse.json("$.id"));
    }

    @Test
    void scopesKeyPerUser() {
        RequestSpec first = valid();
        RequestSpec otherUser = first.withHeader(USER_ID, "user-" + UUID.randomUUID());

        ApiResponse firstResponse = api.post(QUESTIONS, first);
        ApiResponse otherResponse = api.post(QUESTIONS, otherUser);

        assertThat(firstResponse.status()).isEqualTo(201);
        assertThat(otherResponse.status()).isEqualTo(201);
        assertThat(otherResponse.header(REPLAYED)).isEmpty();
        assertThat(otherResponse.json("$.id")).isNotEqualTo(firstResponse.json("$.id"));
    }

    // The key used to edit the question is a separate entry for create: both writes apply, neither is a replay.
    @Test
    void scopesKeyPerOperation() {
        RequestSpec request = valid();
        ApiResponse created = api.post(QUESTIONS, request);
        RequestSpec update = RequestSpec.validUpdate(request.header(USER_ID));
        ApiResponse updated = api.put(QUESTIONS + "/" + created.json("$.id"), update);

        ApiResponse second = api.post(QUESTIONS, request.withHeader(IDEMPOTENCY_KEY, update.header(IDEMPOTENCY_KEY)));

        assertThat(created.status()).as(created.body()).isEqualTo(201);
        assertThat(updated.status()).as(updated.body()).isEqualTo(200);
        assertThat(updated.header(REPLAYED)).isEmpty();
        assertThat(second.status()).as(second.body()).isEqualTo(201);
        assertThat(second.header(REPLAYED)).isEmpty();
        assertThat(second.json("$.id")).isNotEqualTo(created.json("$.id"));
    }

    @Test
    void failedRequestDoesNotRecordKey() {
        RequestSpec request = valid();

        ApiResponse rejected = api.post(QUESTIONS, request.withBody(body("   ", null)));
        ApiResponse accepted = api.post(QUESTIONS, request);

        assertThat(rejected.status()).as(rejected.body()).isEqualTo(400);
        assertThat(accepted.status()).as(accepted.body()).isEqualTo(201);
        assertThat(accepted.header(REPLAYED)).isEmpty();
    }

    @Test
    void parallelCreatesWithDistinctKeys() throws Exception {
        List<RequestSpec> requests = IntStream.range(0, PARALLEL_REQUESTS).mapToObj(i -> valid()).toList();

        List<ApiResponse> responses = postInParallel(requests);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).isEqualTo(201));
        assertThat(distinctIds(responses)).hasSize(PARALLEL_REQUESTS);
    }

    @Test
    void parallelRetriesCreateOneQuestion() throws Exception {
        RequestSpec request = valid();
        List<RequestSpec> requests = IntStream.range(0, PARALLEL_REQUESTS).mapToObj(i -> request).toList();

        List<ApiResponse> responses = postInParallel(requests);

        assertThat(responses).allSatisfy(response -> assertThat(response.status()).isEqualTo(201));
        assertThat(distinctIds(responses)).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isPresent())
                .hasSize(PARALLEL_REQUESTS - 1);
    }

    // Every thread waits on the start latch, so all requests are released together and really overlap.
    private List<ApiResponse> postInParallel(List<RequestSpec> requests) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(requests.size());
        CountDownLatch ready = new CountDownLatch(requests.size());
        CountDownLatch start = new CountDownLatch(1);
        try {
            List<Future<ApiResponse>> futures = new ArrayList<>();
            for (RequestSpec request : requests) {
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();
                    return api.post(QUESTIONS, request);
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

    private static RequestSpec valid() {
        return RequestSpec.validCreate();
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
