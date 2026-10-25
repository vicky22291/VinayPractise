package com.practice.qabank.functional;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Map;

// Thin wrapper over the JDK HttpClient so FTs talk to the app exactly like an external client would.
public class ApiClient {

    private static final String DEFAULT_BASE_URL = "http://localhost:8080";
    private static final Duration TIMEOUT = Duration.ofSeconds(30);

    private final HttpClient http;
    private final URI baseUrl;

    public ApiClient() {
        this(System.getProperty("qabank.baseUrl", DEFAULT_BASE_URL));
    }

    public ApiClient(String baseUrl) {
        this.baseUrl = URI.create(baseUrl);
        // HTTP/1.1 keeps the JDK client from trying an h2c upgrade against a plain Tomcat.
        this.http = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }

    public ApiResponse post(String path, Map<String, String> headers, String body) {
        HttpRequest.Builder builder = request(path, headers)
                .POST(HttpRequest.BodyPublishers.ofString(body == null ? "" : body));
        return send(builder.build());
    }

    public ApiResponse post(String path, RequestSpec request) {
        return post(path, request.headers(), request.body());
    }

    public ApiResponse put(String path, Map<String, String> headers, String body) {
        HttpRequest.Builder builder = request(path, headers)
                .PUT(HttpRequest.BodyPublishers.ofString(body == null ? "" : body));
        return send(builder.build());
    }

    public ApiResponse put(String path, RequestSpec request) {
        return put(path, request.headers(), request.body());
    }

    public ApiResponse get(String path, Map<String, String> headers) {
        return send(request(path, headers).GET().build());
    }

    private HttpRequest.Builder request(String path, Map<String, String> headers) {
        HttpRequest.Builder builder = HttpRequest.newBuilder(baseUrl.resolve(path)).timeout(TIMEOUT);
        headers.forEach(builder::header);
        return builder;
    }

    private ApiResponse send(HttpRequest request) {
        try {
            HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
            return new ApiResponse(response.statusCode(), response.headers(), response.body());
        } catch (IOException e) {
            throw new UncheckedIOException("Request to " + request.uri() + " failed", e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Interrupted while calling " + request.uri(), e);
        }
    }
}
