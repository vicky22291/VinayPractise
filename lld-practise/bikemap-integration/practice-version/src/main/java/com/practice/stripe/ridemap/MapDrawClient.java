package com.practice.stripe.ridemap;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;

/** Small HTTP client for the vendor API described in docs/MAPDRAW_API.md. */
public class MapDrawClient {
    private final String baseUrl;
    private final String apiKey;
    private final Duration timeout;
    private final HttpClient http;

    public MapDrawClient(String baseUrl, String apiKey) {
        this(baseUrl, apiKey, Duration.ofSeconds(10));
    }

    public MapDrawClient(String baseUrl, String apiKey, Duration timeout) {
        this.baseUrl = baseUrl.replaceAll("/+$", "");
        this.apiKey = apiKey;
        this.timeout = timeout;
        this.http = HttpClient.newBuilder().connectTimeout(timeout).build();
    }

    public String baseUrl() {
        return baseUrl;
    }

    public String render(JsonNode body) throws IOException, InterruptedException {
        var request = HttpRequest.newBuilder(URI.create(baseUrl + "/v1/render"))
                .timeout(timeout)
                .header("X-Api-Key", apiKey)
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8))
                .build();
        var response = http.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        if (response.statusCode() >= 400) {
            throw new MapDrawError(response.statusCode(), response.body());
        }
        return response.body();
    }
}
