package com.practice.qabank.functional;

import static com.practice.qabank.functional.RequestSpec.CONTENT_TYPE;
import static com.practice.qabank.functional.RequestSpec.IDEMPOTENCY_KEY;
import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
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

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;

// Black-box tests for POST /questions/{questionId}/downvotes and
// POST /questions/{questionId}/answers/{answerId}/downvotes against a running app (see qabank.baseUrl). The upvote
// endpoints are used too, for the rule that a user holds one vote, up or down, per target. Test data is created only
// through the API, and counts are read back through GET question and GET answer. Tests that take a Target run once
// per endpoint. Each test uses fresh users and keys.
@Tag("api")
class DownvoteFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final int PARALLEL_REQUESTS = 50;
    private static final int RACING_REQUESTS = 25;
    private static final int RACING_FIXTURES = 10;

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void rejectsInvalidRequest(String name, Target target, UnaryOperator<RequestSpec> change, int status,
            String error) {
        Fixture fixture = Fixture.create(api);

        ApiResponse response =
                downvote(target.targetPath(fixture), change.apply(RequestSpec.validVote(RequestSpec.freshUser())));

        assertThat(response.status()).as(response.body()).isEqualTo(status);
        assertThat(response.json("$.error")).isEqualTo(error);
        assertThat((String) response.json("$.message")).isNotBlank();
        assertNoVotes(fixture);
    }

    // UpvoteFT's rows, on both downvote endpoints.
    static Stream<Arguments> invalidRequests() {
        return Stream.of(Target.values()).flatMap(target -> Stream.of(
                invalid(target, "missing X-User-Id", r -> r.withoutHeader(USER_ID), 400, "MISSING_HEADER"),
                invalid(target, "missing Idempotency-Key", r -> r.withoutHeader(IDEMPOTENCY_KEY), 400,
                        "MISSING_HEADER"),
                invalid(target, "blank X-User-Id", r -> r.withHeader(USER_ID, "   "), 400, "VALIDATION_FAILED"),
                invalid(target, "X-User-Id of 65 chars", r -> r.withHeader(USER_ID, uniqueOfLength(65)), 400,
                        "VALIDATION_FAILED"),
                invalid(target, "blank Idempotency-Key", r -> r.withHeader(IDEMPOTENCY_KEY, "   "), 400,
                        "VALIDATION_FAILED"),
                invalid(target, "Idempotency-Key of 65 chars",
                        r -> r.withHeader(IDEMPOTENCY_KEY, uniqueOfLength(65)), 400, "VALIDATION_FAILED")));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("malformedIds")
    void rejectsMalformedId(String name, String path, String segment) {
        ApiResponse response = downvote(path, RequestSpec.validVote(RequestSpec.freshUser()));

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo(segment + " must be a UUID");
    }

    // Each GetQuestionFT row three times: as the question endpoint's questionId, and in either segment of the answer
    // endpoint with a random UUID in the other.
    static Stream<Arguments> malformedIds() {
        return GetQuestionFT.malformedIds().flatMap(row -> {
            String name = (String) row.get()[0];
            String id = (String) row.get()[1];
            return Stream.of(
                    arguments("question endpoint, questionId: " + name, questionPath(id), "questionId"),
                    arguments("answer endpoint, questionId: " + name, answerPath(id, randomId()), "questionId"),
                    arguments("answer endpoint, answerId: " + name, answerPath(randomId(), id), "answerId"));
        });
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("unknownIds")
    void rejectsUnknownIds(String name, Function<Fixture, String> path, String error) {
        Fixture fixture = Fixture.create(api);
        String target = path.apply(fixture);
        String[] segments = target.split("/");

        ApiResponse response = downvote(target, RequestSpec.validVote(RequestSpec.freshUser()));

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo(error);
        if (error.equals("QUESTION_NOT_FOUND")) {
            assertThat(response.json("$.message")).isEqualTo("Question " + segments[2] + " not found");
        } else {
            assertThat(response.json("$.message"))
                    .isEqualTo("Answer " + segments[4] + " not found on question " + segments[2]);
        }
        assertNoVotes(fixture);
    }

    static Stream<Arguments> unknownIds() {
        return Stream.of(
                arguments("question endpoint, random question id", path(f -> questionPath(randomId())),
                        "QUESTION_NOT_FOUND"),
                arguments("answer endpoint, random question id, the fixture's answer id",
                        path(f -> answerPath(randomId(), f.answerId())), "QUESTION_NOT_FOUND"),
                arguments("answer endpoint, the fixture's question, random answer id",
                        path(f -> answerPath(f.questionId(), randomId())), "ANSWER_NOT_FOUND"),
                arguments("answer endpoint, the fixture's question, the other question's answer id",
                        path(f -> answerPath(f.questionId(), f.otherAnswerId())), "ANSWER_NOT_FOUND"));
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void downvotesTarget(Target target) {
        String path = target.targetPath(Fixture.create(api));

        ApiResponse first = downvote(path, RequestSpec.validVote(RequestSpec.freshUser()));
        ApiResponse second = downvote(path, RequestSpec.validVote(RequestSpec.freshUser()));

        assertThat(first.status()).as(first.body()).isEqualTo(201);
        assertThat(first.json("$")).isEqualTo(Map.of("downvotes", 1));
        assertThat(first.header("Location")).isEmpty();
        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(second.status()).as(second.body()).isEqualTo(201);
        assertThat(second.json("$")).isEqualTo(Map.of("downvotes", 2));
        assertThat(downvotesOf(path)).isEqualTo(2);
        assertThat(upvotesOf(path)).isZero();
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void rejectsOwnTarget(Target target) {
        Fixture fixture = Fixture.create(api);
        String path = target.targetPath(fixture);

        ApiResponse response = downvote(path, RequestSpec.validVote(target.authorId(fixture)));

        assertThat(response.status()).as(response.body()).isEqualTo(403);
        assertThat(response.json("$.error")).isEqualTo("CANNOT_DOWNVOTE_OWN");
        assertThat(response.json("$.message"))
                .isEqualTo("You can't downvote your own " + noun(target) + " " + idOf(path));
        assertThat(upvotesOf(path)).isZero();
        assertThat(downvotesOf(path)).isZero();
    }

    // The second key's 409 isn't recorded, so its retry is a 409 again, not a replay.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void secondDownvoteConflicts(Target target) {
        String path = target.targetPath(Fixture.create(api));
        RequestSpec first = RequestSpec.validVote(RequestSpec.freshUser());
        RequestSpec second = first.withHeader(IDEMPOTENCY_KEY, UUID.randomUUID().toString());
        downvoteAs(path, first);

        ApiResponse conflict = downvote(path, second);
        ApiResponse retry = downvote(path, second);

        for (ApiResponse response : List.of(conflict, retry)) {
            assertThat(response.status()).as(response.body()).isEqualTo(409);
            assertThat(response.json("$.error")).isEqualTo("ALREADY_DOWNVOTED");
            assertThat(response.json("$.message"))
                    .isEqualTo("You already downvoted " + noun(target) + " " + idOf(path));
            assertThat(response.header(REPLAYED)).isEmpty();
        }
        assertThat(downvotesOf(path)).isEqualTo(1);
        assertThat(upvotesOf(path)).isZero();
    }

    // Switching sides is rejected, and the 409 names the vote the caller holds, not the one they tried.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void downvoteAfterUpvoteConflicts(Target target) {
        String path = target.targetPath(Fixture.create(api));
        String user = RequestSpec.freshUser();
        upvoteAs(path, RequestSpec.validVote(user));

        ApiResponse response = downvote(path, RequestSpec.validVote(user));

        assertThat(response.status()).as(response.body()).isEqualTo(409);
        assertThat(response.json("$.error")).isEqualTo("ALREADY_UPVOTED");
        assertThat(response.json("$.message")).isEqualTo("You already upvoted " + noun(target) + " " + idOf(path));
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(upvotesOf(path)).isEqualTo(1);
        assertThat(downvotesOf(path)).isZero();
    }

    // The mirror, through the upvote endpoint, which gains this 409.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void upvoteAfterDownvoteConflicts(Target target) {
        String path = target.targetPath(Fixture.create(api));
        String user = RequestSpec.freshUser();
        downvoteAs(path, RequestSpec.validVote(user));

        ApiResponse response = upvote(path, RequestSpec.validVote(user));

        assertThat(response.status()).as(response.body()).isEqualTo(409);
        assertThat(response.json("$.error")).isEqualTo("ALREADY_DOWNVOTED");
        assertThat(response.json("$.message"))
                .isEqualTo("You already downvoted " + noun(target) + " " + idOf(path));
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(upvotesOf(path)).isZero();
        assertThat(downvotesOf(path)).isEqualTo(1);
    }

    // The replay returns the stored count, not the live one.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void replaysOriginalForSameKey(Target target) {
        String path = target.targetPath(Fixture.create(api));
        RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());
        ApiResponse first = downvoteAs(path, request);
        downvoteAs(path, RequestSpec.validVote(RequestSpec.freshUser()));

        ApiResponse retry = downvote(path, request);

        assertThat(first.json("$.downvotes")).isEqualTo(1);
        assertThat(first.header(REPLAYED)).isEmpty();
        assertThat(retry.status()).as(retry.body()).isEqualTo(201);
        assertThat(retry.json("$")).isEqualTo(Map.of("downvotes", 1));
        assertThat(retry.header(REPLAYED)).contains("true");
        assertThat(downvotesOf(path)).isEqualTo(2);
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void scopesKeyPerTarget(Target target) {
        String firstPath = target.targetPath(Fixture.create(api));
        String secondPath = target.targetPath(Fixture.create(api));
        RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());

        ApiResponse first = downvote(firstPath, request);
        ApiResponse second = downvote(secondPath, request);

        for (ApiResponse response : List.of(first, second)) {
            assertThat(response.status()).as(response.body()).isEqualTo(201);
            assertThat(response.json("$.downvotes")).isEqualTo(1);
            assertThat(response.header(REPLAYED)).isEmpty();
        }
        assertThat(downvotesOf(firstPath)).isEqualTo(1);
        assertThat(downvotesOf(secondPath)).isEqualTo(1);
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void scopesKeyPerUser(Target target) {
        String path = target.targetPath(Fixture.create(api));
        RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());
        downvoteAs(path, request);

        ApiResponse other = downvote(path, request.withHeader(USER_ID, RequestSpec.freshUser()));

        assertThat(other.status()).as(other.body()).isEqualTo(201);
        assertThat(other.json("$.downvotes")).isEqualTo(2);
        assertThat(other.header(REPLAYED)).isEmpty();
        assertThat(downvotesOf(path)).isEqualTo(2);
    }

    // An upvote and a downvote are separate operations: the downvote under the upvote's key runs and gets the 409,
    // not a replay of the upvote's 201.
    @Test
    void scopesKeyPerOperation() {
        String path = questionPath(createQuestion(RequestSpec.freshUser()));
        RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());
        upvoteAs(path, request);

        ApiResponse response = downvote(path, request);

        assertThat(response.status()).as(response.body()).isEqualTo(409);
        assertThat(response.json("$.error")).isEqualTo("ALREADY_UPVOTED");
        assertThat(response.header(REPLAYED)).isEmpty();
        assertThat(upvotesOf(path)).isEqualTo(1);
        assertThat(downvotesOf(path)).isZero();
    }

    // Both requests share the stored key (user, DOWNVOTE_ANSWER, the answer id, key), so a recorded 404 would replay.
    @Test
    void failedRequestDoesNotRecordKey() {
        Fixture fixture = Fixture.create(api);
        RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());

        ApiResponse rejected = downvote(answerPath(fixture.questionId(), fixture.otherAnswerId()), request);
        ApiResponse accepted = downvote(answerPath(fixture.otherQuestionId(), fixture.otherAnswerId()), request);

        assertThat(rejected.status()).as(rejected.body()).isEqualTo(404);
        assertThat(rejected.json("$.error")).isEqualTo("ANSWER_NOT_FOUND");
        assertThat(accepted.status()).as(accepted.body()).isEqualTo(201);
        assertThat(accepted.json("$.downvotes")).isEqualTo(1);
        assertThat(accepted.header(REPLAYED)).isEmpty();
    }

    @Test
    void validatesBeforeLookup() {
        ApiResponse response = downvote(questionPath(randomId()), RequestSpec.validVote("   "));

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
    }

    // The answer's own author, under the wrong question: the lookup fails before the self-vote check.
    @Test
    void checksLookupBeforeOwnTarget() {
        Fixture fixture = Fixture.create(api);

        ApiResponse response = downvote(answerPath(fixture.otherQuestionId(), fixture.answerId()),
                RequestSpec.validVote(fixture.answerAuthor()));

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo("ANSWER_NOT_FOUND");
    }

    // The JSON body tries to set the count, and text/plain would be a 415 on an endpoint that reads a body.
    @Test
    void ignoresBody() {
        String path = questionPath(createQuestion(RequestSpec.freshUser()));
        RequestSpec json = RequestSpec.validVote(RequestSpec.freshUser())
                .withHeader(CONTENT_TYPE, "application/json")
                .withBody("{\"downvotes\": 100}");
        RequestSpec text = RequestSpec.validVote(RequestSpec.freshUser())
                .withHeader(CONTENT_TYPE, "text/plain")
                .withBody("downvote");

        ApiResponse first = downvote(path, json);
        ApiResponse second = downvote(path, text);

        assertThat(first.status()).as(first.body()).isEqualTo(201);
        assertThat(first.json("$.downvotes")).isEqualTo(1);
        assertThat(second.status()).as(second.body()).isEqualTo(201);
        assertThat(second.json("$.downvotes")).isEqualTo(2);
    }

    @Test
    void questionAuthorCanDownvoteAnswer() {
        Fixture fixture = Fixture.create(api);
        String path = answerPath(fixture.questionId(), fixture.answerId());

        ApiResponse response = downvote(path, RequestSpec.validVote(fixture.questionAuthor()));

        assertThat(response.status()).as(response.body()).isEqualTo(201);
        assertThat(response.json("$.downvotes")).isEqualTo(1);
        assertThat(downvotesOf(path)).isEqualTo(1);
    }

    // Each target counts its own votes per direction. U3 holds an upvote on the question and a downvote on answer A.
    @Test
    void countsShowInGetQuestionAndGetAnswer() {
        String questionId = createQuestion(RequestSpec.freshUser());
        String answerA = answerAs(questionId, RequestSpec.freshUser());
        String answerB = answerAs(questionId, RequestSpec.freshUser());
        ApiResponse before = getQuestion(questionId);
        assertThat(before.json("$.upvotes")).isEqualTo(0);
        assertThat(before.json("$.downvotes")).isEqualTo(0);
        assertThat(before.json("$.answers[*].upvotes")).isEqualTo(List.of(0, 0));
        assertThat(before.json("$.answers[*].downvotes")).isEqualTo(List.of(0, 0));

        String question = questionPath(questionId);
        String answer = answerPath(questionId, answerA);
        List<String> users = IntStream.range(0, 4).mapToObj(i -> RequestSpec.freshUser()).toList();
        downvoteAs(question, RequestSpec.validVote(users.get(0)));
        downvoteAs(question, RequestSpec.validVote(users.get(1)));
        upvoteAs(question, RequestSpec.validVote(users.get(2)));
        for (String user : users.subList(0, 3)) {
            downvoteAs(answer, RequestSpec.validVote(user));
        }
        upvoteAs(answer, RequestSpec.validVote(users.get(3)));

        ApiResponse after = getQuestion(questionId);
        assertThat(after.json("$.upvotes")).isEqualTo(1);
        assertThat(after.json("$.downvotes")).isEqualTo(2);
        assertThat(after.json("$.answers[*].id")).isEqualTo(List.of(answerA, answerB));
        assertThat(after.json("$.answers[*].upvotes")).isEqualTo(List.of(1, 0));
        assertThat(after.json("$.answers[*].downvotes")).isEqualTo(List.of(3, 0));
        assertThat(upvotesOf(answer)).isEqualTo(1);
        assertThat(downvotesOf(answer)).isEqualTo(3);
    }

    // As writeResponsesShowTheCountsTheyProduced in UpvoteFT, for downvotes: an edit shows the votes cast before it, and
    // a create or add replay is the original body, counts included.
    @Test
    void writeResponsesShowTheDownvotesTheyProduced() {
        RequestSpec create = RequestSpec.validCreate();
        ApiResponse created = api.post(QUESTIONS, create);
        assertThat(created.status()).as(created.body()).isEqualTo(201);
        assertThat(created.json("$.downvotes")).isEqualTo(0);
        String questionId = (String) created.json("$.id");
        RequestSpec add = RequestSpec.validAnswer();
        ApiResponse added = addAnswer(questionId, add);
        assertThat(added.json("$.downvotes")).isEqualTo(0);
        String answerId = (String) added.json("$.id");
        for (int i = 0; i < 2; i++) {
            String user = RequestSpec.freshUser();
            downvoteAs(questionPath(questionId), RequestSpec.validVote(user));
            downvoteAs(answerPath(questionId, answerId), RequestSpec.validVote(user));
        }

        ApiResponse createReplay = api.post(QUESTIONS, create);
        ApiResponse questionEdit = api.put(questionPath(questionId), RequestSpec.validUpdate(create.header(USER_ID)));
        ApiResponse addReplay = api.post(answersPath(questionId), add);
        ApiResponse answerEdit =
                api.put(answerPath(questionId, answerId), RequestSpec.validAnswerUpdate(add.header(USER_ID)));

        assertThat(createReplay.status()).as(createReplay.body()).isEqualTo(201);
        assertThat(createReplay.header(REPLAYED)).contains("true");
        assertThat(createReplay.body()).isEqualTo(created.body());
        assertThat(createReplay.json("$.downvotes")).isEqualTo(0);
        assertThat(questionEdit.status()).as(questionEdit.body()).isEqualTo(200);
        assertThat(questionEdit.json("$.downvotes")).isEqualTo(2);
        assertThat(questionEdit.json("$.answers[0].downvotes")).isEqualTo(2);
        assertThat(addReplay.status()).as(addReplay.body()).isEqualTo(201);
        assertThat(addReplay.header(REPLAYED)).contains("true");
        assertThat(addReplay.body()).isEqualTo(added.body());
        assertThat(addReplay.json("$.downvotes")).isEqualTo(0);
        assertThat(answerEdit.status()).as(answerEdit.body()).isEqualTo(200);
        assertThat(answerEdit.json("$.downvotes")).isEqualTo(2);
    }

    // Each response may also count votes that landed at the same moment, so only the range is fixed.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void parallelDownvotesByDifferentUsersAreAllCounted(Target target) throws Exception {
        String path = target.targetPath(Fixture.create(api));
        List<Callable<ApiResponse>> votes = IntStream.range(0, PARALLEL_REQUESTS)
                .mapToObj(i -> RequestSpec.validVote(RequestSpec.freshUser()))
                .<Callable<ApiResponse>>map(request -> () -> downvote(path, request))
                .toList();

        List<ApiResponse> responses = runTogether(votes);

        assertThat(responses).allSatisfy(response -> {
            assertThat(response.status()).as(response.body()).isEqualTo(201);
            assertThat((Integer) response.json("$.downvotes")).isBetween(1, PARALLEL_REQUESTS);
        });
        assertThat(downvotesOf(path)).isEqualTo(PARALLEL_REQUESTS);
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void parallelDownvotesBySameUserCountOnce(Target target) throws Exception {
        String path = target.targetPath(Fixture.create(api));
        String user = RequestSpec.freshUser();
        List<Callable<ApiResponse>> votes = IntStream.range(0, PARALLEL_REQUESTS)
                .mapToObj(i -> RequestSpec.validVote(user))
                .<Callable<ApiResponse>>map(request -> () -> downvote(path, request))
                .toList();

        List<ApiResponse> responses = runTogether(votes);

        List<ApiResponse> created = responses.stream().filter(response -> response.status() == 201).toList();
        assertThat(created).hasSize(1);
        assertThat(created.get(0).json("$.downvotes")).isEqualTo(1);
        assertThat(responses).filteredOn(response -> response.status() == 409)
                .hasSize(PARALLEL_REQUESTS - 1)
                .allSatisfy(response -> assertThat(response.json("$.error")).isEqualTo("ALREADY_DOWNVOTED"));
        assertThat(downvotesOf(path)).isEqualTo(1);
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void parallelRetriesDownvoteOnce(Target target) throws Exception {
        String path = target.targetPath(Fixture.create(api));
        RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());
        List<Callable<ApiResponse>> retries = IntStream.range(0, PARALLEL_REQUESTS)
                .<Callable<ApiResponse>>mapToObj(i -> () -> downvote(path, request))
                .toList();

        List<ApiResponse> responses = runTogether(retries);

        assertThat(responses).allSatisfy(response -> {
            assertThat(response.status()).as(response.body()).isEqualTo(201);
            assertThat(response.json("$")).isEqualTo(Map.of("downvotes", 1));
        });
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isEmpty()).hasSize(1);
        assertThat(responses).filteredOn(response -> response.header(REPLAYED).isPresent())
                .hasSize(PARALLEL_REQUESTS - 1);
        assertThat(downvotesOf(path)).isEqualTo(1);
    }

    // "Never both" under a race: whichever vote lands first is the only one, and every other request, in either
    // direction, gets the 409 naming it. Repeated on new targets, so both outcomes get a chance to show up.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void parallelUpAndDownvotesBySameUserKeepOne(Target target) throws Exception {
        for (int round = 0; round < RACING_FIXTURES; round++) {
            String path = target.targetPath(Fixture.create(api));
            String user = RequestSpec.freshUser();
            List<Callable<ApiResponse>> votes = new ArrayList<>();
            for (int i = 0; i < RACING_REQUESTS; i++) {
                RequestSpec up = RequestSpec.validVote(user);
                RequestSpec down = RequestSpec.validVote(user);
                votes.add(() -> upvote(path, up));
                votes.add(() -> downvote(path, down));
            }

            List<ApiResponse> responses = runTogether(votes);

            List<ApiResponse> created = responses.stream().filter(response -> response.status() == 201).toList();
            assertThat(created).as(path).hasSize(1);
            boolean upWon = created.get(0).json("$").equals(Map.of("upvotes", 1));
            if (!upWon) {
                assertThat(created.get(0).json("$")).isEqualTo(Map.of("downvotes", 1));
            }
            assertThat(responses).filteredOn(response -> response.status() == 409)
                    .hasSize(2 * RACING_REQUESTS - 1)
                    .allSatisfy(response -> assertThat(response.json("$.error"))
                            .isEqualTo(upWon ? "ALREADY_UPVOTED" : "ALREADY_DOWNVOTED"));
            assertThat(upvotesOf(path)).isEqualTo(upWon ? 1 : 0);
            assertThat(downvotesOf(path)).isEqualTo(upWon ? 0 : 1);
        }
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Target.class)
    void parallelUpAndDownvotesByDifferentUsersCountSeparately(Target target) throws Exception {
        String path = target.targetPath(Fixture.create(api));
        List<Callable<ApiResponse>> votes = new ArrayList<>();
        for (int i = 0; i < RACING_REQUESTS; i++) {
            RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());
            votes.add(() -> upvote(path, request));
        }
        for (int i = 0; i < RACING_REQUESTS; i++) {
            RequestSpec request = RequestSpec.validVote(RequestSpec.freshUser());
            votes.add(() -> downvote(path, request));
        }

        List<ApiResponse> responses = runTogether(votes);

        assertThat(responses.subList(0, RACING_REQUESTS)).allSatisfy(response -> {
            assertThat(response.status()).as(response.body()).isEqualTo(201);
            assertThat((Integer) response.json("$.upvotes")).isBetween(1, RACING_REQUESTS);
        });
        assertThat(responses.subList(RACING_REQUESTS, responses.size())).allSatisfy(response -> {
            assertThat(response.status()).as(response.body()).isEqualTo(201);
            assertThat((Integer) response.json("$.downvotes")).isBetween(1, RACING_REQUESTS);
        });
        assertThat(upvotesOf(path)).isEqualTo(RACING_REQUESTS);
        assertThat(downvotesOf(path)).isEqualTo(RACING_REQUESTS);
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

    // targetPath is a question or answer path; the votes paths are that plus /downvotes or /upvotes.
    private ApiResponse downvote(String targetPath, RequestSpec request) {
        return api.post(targetPath + "/downvotes", request);
    }

    private ApiResponse downvoteAs(String targetPath, RequestSpec request) {
        ApiResponse response = downvote(targetPath, request);
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    private ApiResponse upvote(String targetPath, RequestSpec request) {
        return api.post(targetPath + "/upvotes", request);
    }

    private ApiResponse upvoteAs(String targetPath, RequestSpec request) {
        ApiResponse response = upvote(targetPath, request);
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    // GET question or GET answer, whichever targetPath names.
    private int upvotesOf(String targetPath) {
        return countOf(targetPath, "upvotes");
    }

    private int downvotesOf(String targetPath) {
        return countOf(targetPath, "downvotes");
    }

    private int countOf(String targetPath, String field) {
        ApiResponse response = api.get(targetPath, Map.of());
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return (Integer) response.json("$." + field);
    }

    private void assertNoVotes(Fixture f) {
        List<String> paths = List.of(questionPath(f.questionId()), answerPath(f.questionId(), f.answerId()),
                questionPath(f.otherQuestionId()), answerPath(f.otherQuestionId(), f.otherAnswerId()));
        for (String path : paths) {
            assertThat(upvotesOf(path)).as(path).isZero();
            assertThat(downvotesOf(path)).as(path).isZero();
        }
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

    private String answerAs(String questionId, String userId) {
        return (String) addAnswer(questionId, RequestSpec.validAnswer().withHeader(USER_ID, userId)).json("$.id");
    }

    private ApiResponse getQuestion(String questionId) {
        ApiResponse response = api.get(questionPath(questionId), Map.of());
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return response;
    }

    private static String questionPath(String questionId) {
        return QUESTIONS + "/" + questionId;
    }

    private static String answersPath(String questionId) {
        return questionPath(questionId) + "/answers";
    }

    private static String answerPath(String questionId, String answerId) {
        return answersPath(questionId) + "/" + answerId;
    }

    // The target's id is the last segment of its path.
    private static String idOf(String targetPath) {
        return targetPath.substring(targetPath.lastIndexOf('/') + 1);
    }

    // As the error messages name it.
    private static String noun(Target target) {
        return target.name().toLowerCase(Locale.ROOT);
    }

    private static String randomId() {
        return UUID.randomUUID().toString();
    }

    private static Arguments invalid(Target target, String name, UnaryOperator<RequestSpec> change, int status,
            String error) {
        return arguments(target + ": " + name, target, change, status, error);
    }

    // Gives a lambda its target type inside arguments(...).
    private static Function<Fixture, String> path(Function<Fixture, String> path) {
        return path;
    }

    private static String uniqueOfLength(int length) {
        String seed = UUID.randomUUID().toString().replace("-", "");
        return (seed + "x".repeat(length)).substring(0, length);
    }
}
