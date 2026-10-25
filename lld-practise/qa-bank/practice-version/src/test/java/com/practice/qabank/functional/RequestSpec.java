package com.practice.qabank.functional;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

// An immutable request description. Each with* method returns a changed copy, so a test changes one thing at a time.
public record RequestSpec(Map<String, String> headers, String body) {

    public static final String USER_ID = "X-User-Id";
    public static final String IDEMPOTENCY_KEY = "Idempotency-Key";
    public static final String CONTENT_TYPE = "Content-Type";

    public static final String VALID_CONTENT = "How do I make a ConcurrentHashMap value update atomic?";
    public static final String VALID_BODY =
            "{\"content\": \"" + VALID_CONTENT + "\", \"tags\": [\"java\", \"concurrency\"]}";

    public static final String VALID_UPDATE_TAGS = "[\"java\", \"concurrency\", \"atomic\"]";

    public RequestSpec {
        headers = Map.copyOf(headers);
    }

    // Fresh user and key every time: the app keeps state across tests and runs, so tests must not share them.
    public static RequestSpec validCreate() {
        return new RequestSpec(jsonHeaders(freshUser()), VALID_BODY);
    }

    // PUT /questions/{id} as userId, who must be the author. Fresh key and fresh content, so it's always a real edit.
    public static RequestSpec validUpdate(String userId) {
        String content = "Edited question " + UUID.randomUUID();
        String body = "{\"content\": \"" + content + "\", \"tags\": " + VALID_UPDATE_TAGS + "}";
        return new RequestSpec(jsonHeaders(userId), body);
    }

    // POST /questions/{questionId}/answers as a fresh user with a fresh key and fresh content.
    public static RequestSpec validAnswer() {
        return new RequestSpec(jsonHeaders(freshUser()), answerBody("Answer " + UUID.randomUUID()));
    }

    // PUT /questions/{questionId}/answers/{answerId} as userId, who must be the answer's author. Fresh key and content.
    public static RequestSpec validAnswerUpdate(String userId) {
        return new RequestSpec(jsonHeaders(userId), answerBody("Edited answer " + UUID.randomUUID()));
    }

    // POST .../upvotes or .../downvotes as userId with a fresh key. No Content-Type and no body: the endpoints take
    // none.
    public static RequestSpec validVote(String userId) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put(USER_ID, userId);
        headers.put(IDEMPOTENCY_KEY, UUID.randomUUID().toString());
        return new RequestSpec(headers, null);
    }

    public RequestSpec withHeader(String name, String value) {
        Map<String, String> copy = new LinkedHashMap<>(headers);
        copy.put(name, value);
        return new RequestSpec(copy, body);
    }

    public RequestSpec withoutHeader(String name) {
        Map<String, String> copy = new LinkedHashMap<>(headers);
        copy.remove(name);
        return new RequestSpec(copy, body);
    }

    public RequestSpec withBody(String json) {
        return new RequestSpec(headers, json);
    }

    public String header(String name) {
        return headers.get(name);
    }

    public static String freshUser() {
        return "user-" + UUID.randomUUID();
    }

    private static Map<String, String> jsonHeaders(String userId) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put(USER_ID, userId);
        headers.put(IDEMPOTENCY_KEY, UUID.randomUUID().toString());
        headers.put(CONTENT_TYPE, "application/json");
        return headers;
    }

    private static String answerBody(String content) {
        return "{\"content\": \"" + content + "\"}";
    }
}
