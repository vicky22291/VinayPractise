package com.practice.stripe;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.NullNode;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.request;

/** Sends serialized requests through Spring MVC; never invokes services or repositories directly. */
final class MockMvcTestClient {
    record Response(int status, JsonNode body) {}
    private final MockMvc mvc;
    private final ObjectMapper mapper;
    MockMvcTestClient(MockMvc mvc, ObjectMapper mapper) { this.mvc = mvc; this.mapper = mapper; }

    Response send(String method, String path, Object body, String key) {
        try {
            var builder = request(HttpMethod.valueOf(method), path).contentType(MediaType.APPLICATION_JSON);
            if (key != null) builder.header("Idempotency-Key", key);
            if (body != null) builder.content(mapper.writeValueAsBytes(body));
            var response = mvc.perform(builder).andReturn().getResponse();
            String content = response.getContentAsString();
            return new Response(response.getStatus(), content.isEmpty() ? NullNode.instance : mapper.readTree(content));
        } catch (Exception error) { throw new AssertionError(method + " " + path + " failed", error); }
    }

    JsonNode expect(String method, String path, Object body, String key, int status) {
        Response response = send(method, path, body, key);
        assertThat(response.status()).as("%s %s: %s", method, path, response.body()).isEqualTo(status);
        return response.body();
    }
    JsonNode get(String path) { return expect("GET", path, null, null, 200); }
}
