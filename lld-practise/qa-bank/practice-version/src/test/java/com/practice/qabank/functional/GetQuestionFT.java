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
import java.util.stream.Stream;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

// Black-box tests for GET /questions/{id} against a running app (see qabank.baseUrl). Test data is created only
// through POST /questions.
@Tag("api")
class GetQuestionFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final int PARALLEL_REQUESTS = 50;

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void rejectsMalformedId(String name, String id) {
        ApiResponse response = api.get(QUESTIONS + "/" + id, Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo("id must be a UUID");
    }

    // Other FTs reuse these rows through a fully qualified @MethodSource. Lenient forms such as 1-1-1-1-1 are left out
    // on purpose: the JDK parses them (GetQuestion Decision 3).
    static Stream<Arguments> malformedIds() {
        return Stream.of(
                arguments("words", "not-a-uuid"),
                arguments("digits only, no dashes", "12345"),
                arguments("37 chars", "3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11a"),
                arguments("right shape, not hex", "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz"),
                arguments("32 hex chars, no dashes", "3f1c9a528a7e4f0b9d0e2b6c1f6a7e11"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("userHeaders")
    void ignoresUserHeader(String name, String userId) {
        ApiResponse created = create(RequestSpec.validCreate());
        Map<String, String> headers = userId == null ? Map.of() : Map.of(USER_ID, userId);

        ApiResponse response = api.get(path(created), headers);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$")).isEqualTo(created.json("$"));
    }

    // A null row sends no X-User-Id header at all. GetAnswerFT reuses these rows.
    static Stream<Arguments> userHeaders() {
        return Stream.of(
                arguments("absent", null),
                arguments("a different user", RequestSpec.freshUser()),
                arguments("blank", "   "),
                arguments("65 chars", "u".repeat(65)));
    }

    @Test
    void returnsCreatedQuestion() {
        ApiResponse created = create(RequestSpec.validCreate());

        ApiResponse response = api.get(path(created), Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(created.json("$.id"));
        assertThat(response.json("$.authorId")).isEqualTo(created.json("$.authorId"));
        assertThat(response.json("$.content")).isEqualTo(created.json("$.content"));
        assertThat(response.json("$.tags")).isEqualTo(created.json("$.tags"));
        assertThat(response.json("$.createdAt")).isEqualTo(created.json("$.createdAt"));
        assertThat(response.json("$.answers")).isEqualTo(List.of());
        assertThat(response.header("Location")).isEmpty();
        assertThat(response.header(REPLAYED)).isEmpty();
    }

    @Test
    void followsCreateLocation() {
        ApiResponse created = create(RequestSpec.validCreate());
        String location = created.header("Location").orElseThrow();

        ApiResponse response = api.get(location, Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(created.json("$.id"));
    }

    @Test
    void unknownIdIsNotFound() {
        String id = UUID.randomUUID().toString();

        ApiResponse response = api.get(QUESTIONS + "/" + id, Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo("QUESTION_NOT_FOUND");
        assertThat((String) response.json("$.message")).contains(id);
    }

    @Test
    void acceptsUpperCaseId() {
        ApiResponse created = create(RequestSpec.validCreate());
        String id = (String) created.json("$.id");

        ApiResponse response = api.get(QUESTIONS + "/" + id.toUpperCase(Locale.ROOT), Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.id")).isEqualTo(id);
    }

    @Test
    void replayDoesNotChangeStoredQuestion() {
        RequestSpec request = RequestSpec.validCreate();
        ApiResponse created = create(request);
        ApiResponse replay =
                api.post(QUESTIONS, request.withBody("{\"content\": \"A completely different question?\"}"));
        assertThat(replay.header(REPLAYED)).contains("true");

        ApiResponse response = api.get(path(created), Map.of());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.content")).isEqualTo(created.json("$.content"));
    }

    @Test
    void parallelCreateThenGet() throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(PARALLEL_REQUESTS);
        CountDownLatch ready = new CountDownLatch(PARALLEL_REQUESTS);
        CountDownLatch start = new CountDownLatch(1);
        try {
            List<Future<Void>> futures = new ArrayList<>();
            for (int i = 0; i < PARALLEL_REQUESTS; i++) {
                String content = "Parallel question " + UUID.randomUUID();
                RequestSpec request = RequestSpec.validCreate().withBody("{\"content\": \"" + content + "\"}");
                // Every thread waits on the start latch, so all creates are released together and really overlap.
                futures.add(pool.submit(() -> {
                    ready.countDown();
                    start.await();
                    ApiResponse created = create(request);
                    ApiResponse fetched = api.get(path(created), Map.of());
                    assertThat(fetched.status()).as(fetched.body()).isEqualTo(200);
                    assertThat(fetched.json("$.id")).isEqualTo(created.json("$.id"));
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

    private ApiResponse create(RequestSpec request) {
        ApiResponse response = api.post(QUESTIONS, request);
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    private static String path(ApiResponse created) {
        return QUESTIONS + "/" + created.json("$.id");
    }
}
