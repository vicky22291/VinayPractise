package com.practice.qabank.functional.journey;

import static com.practice.qabank.functional.RequestSpec.CONTENT_TYPE;
import static com.practice.qabank.functional.RequestSpec.IDEMPOTENCY_KEY;
import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static org.assertj.core.api.Assertions.assertThat;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import com.practice.qabank.functional.ApiClient;
import com.practice.qabank.functional.ApiResponse;
import com.practice.qabank.functional.RequestSpec;

// One user of a journey: a fresh user-<uuid> id over a shared ApiClient. Every write gets a fresh Idempotency-Key and
// is kept in sent, so a journey can retry it later with its own key. Reads are public, so they send no headers.
final class TestUser {

    // A write as it was sent, and the response it first got. A retry sends request to path again, key included.
    record Sent(String method, String path, RequestSpec request, ApiResponse first) {
    }

    private static final String QUESTIONS = "/questions";

    private final ApiClient api;
    private final String id;
    // Synchronized: a CONCURRENT round can send several writes as one user at once.
    private final List<Sent> sent = Collections.synchronizedList(new ArrayList<>());

    private TestUser(ApiClient api, String id) {
        this.api = api;
        this.id = id;
    }

    static TestUser fresh(ApiClient api) {
        return new TestUser(api, RequestSpec.freshUser());
    }

    // ft- and 24 random hex chars, as in ListQuestionsFT: a tag no other test or run uses.
    static String freshTag() {
        return "ft-" + UUID.randomUUID().toString().replace("-", "").substring(0, 24);
    }

    String id() {
        return id;
    }

    ApiResponse ask(String content, String... tags) {
        return send("POST", QUESTIONS, json(questionBody(content, tags)));
    }

    ApiResponse answer(String questionId, String content) {
        return send("POST", answersPath(questionId), json(answerBody(content)));
    }

    ApiResponse editQuestion(String questionId, String content, String... tags) {
        return send("PUT", questionPath(questionId), json(questionBody(content, tags)));
    }

    ApiResponse editAnswer(String questionId, String answerId, String content) {
        return send("PUT", answerPath(questionId, answerId), json(answerBody(content)));
    }

    // answerId null votes on the question itself.
    ApiResponse vote(Direction direction, String questionId, String answerId) {
        String target = answerId == null ? questionPath(questionId) : answerPath(questionId, answerId);
        return send("POST", target + direction.pathSuffix(), RequestSpec.validVote(id));
    }

    // Sends that exact request again, key included, and doesn't add it to sent: it isn't a new write.
    ApiResponse retry(Sent write) {
        return call(write.method(), write.path(), write.request());
    }

    ApiResponse getQuestion(String questionId) {
        return api.get(questionPath(questionId), Map.of());
    }

    ApiResponse getAnswer(String questionId, String answerId) {
        return api.get(answerPath(questionId, answerId), Map.of());
    }

    // GET /questions?tag=...&limit=..., following nextCursor as after. Returns every page as it came, and stops after a
    // null cursor, a non-200, or a cursor seen before, so a broken cursor can't loop forever. The caller checks the
    // pages, with items.
    List<ApiResponse> walk(String tag, int limit) {
        List<ApiResponse> pages = new ArrayList<>();
        Set<String> cursors = new HashSet<>();
        String after = null;
        while (true) {
            String query = "?tag=" + tag + "&limit=" + limit + (after == null ? "" : "&after=" + after);
            ApiResponse page = api.get(QUESTIONS + query, Map.of());
            pages.add(page);
            if (page.status() != 200) {
                return pages;
            }
            after = (String) page.json("$.nextCursor");
            if (after == null || !cursors.add(after)) {
                return pages;
            }
        }
    }

    // A copy, in the order this user's writes returned.
    List<Sent> sent() {
        synchronized (sent) {
            return List.copyOf(sent);
        }
    }

    // A walk's items, joined, after checking every page: 200, full and ending on its nextCursor whenever one follows,
    // and the last page ends the walk.
    @SuppressWarnings("unchecked")
    static List<Map<String, Object>> items(List<ApiResponse> pages, int limit) {
        List<Map<String, Object>> items = new ArrayList<>();
        for (int i = 0; i < pages.size(); i++) {
            ApiResponse page = pages.get(i);
            assertThat(page.status()).as("page %d: %s", i, page.body()).isEqualTo(200);
            List<Map<String, Object>> pageItems = (List<Map<String, Object>>) page.json("$.items");
            String next = (String) page.json("$.nextCursor");
            if (i == pages.size() - 1) {
                assertThat(next).as("page %d is the last, but has a cursor seen before", i).isNull();
                assertThat(pageItems).as("page %d", i).hasSizeLessThanOrEqualTo(limit);
            } else {
                assertThat(pageItems).as("page %d is not the last, so it's full", i).hasSize(limit);
                assertThat(next).as("page %d's cursor", i).isEqualTo(pageItems.get(limit - 1).get("id"));
            }
            items.addAll(pageItems);
        }
        return items;
    }

    private ApiResponse send(String method, String path, RequestSpec request) {
        ApiResponse response = call(method, path, request);
        sent.add(new Sent(method, path, request, response));
        return response;
    }

    private ApiResponse call(String method, String path, RequestSpec request) {
        return switch (method) {
            case "POST" -> api.post(path, request);
            case "PUT" -> api.put(path, request);
            default -> throw new IllegalArgumentException("Not a write: " + method);
        };
    }

    // As this user, with a fresh key.
    private RequestSpec json(String body) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put(USER_ID, id);
        headers.put(IDEMPOTENCY_KEY, UUID.randomUUID().toString());
        headers.put(CONTENT_TYPE, "application/json");
        return new RequestSpec(headers, body);
    }

    private static String questionBody(String content, String... tags) {
        String tagList = Stream.of(tags).map(tag -> "\"" + tag + "\"").collect(Collectors.joining(", "));
        return "{\"content\": \"" + content + "\", \"tags\": [" + tagList + "]}";
    }

    private static String answerBody(String content) {
        return "{\"content\": \"" + content + "\"}";
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
}
