package com.practice.qabank.functional;

import java.net.http.HttpHeaders;
import java.util.Optional;

import com.jayway.jsonpath.JsonPath;

public record ApiResponse(int status, HttpHeaders headers, String body) {

    public Object json(String jsonPath) {
        return JsonPath.read(body, jsonPath);
    }

    public Optional<String> header(String name) {
        return headers.firstValue(name);
    }
}
