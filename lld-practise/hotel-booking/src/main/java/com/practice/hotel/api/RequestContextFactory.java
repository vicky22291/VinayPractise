package com.practice.hotel.api;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Arrays;
import java.util.HexFormat;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import com.practice.hotel.service.RequestContext;

// Builds the RequestContext of a write, so controllers don't know how the request hash is made.
@Component
public class RequestContextFactory {

    private final ObjectMapper objectMapper;

    public RequestContextFactory(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    // The RequestContext constructor rejects a blank actorId (401) and a blank or too-long idempotencyKey (400).
    public RequestContext create(String actorId, Instant requestTime, String idempotencyKey, String path, Object body) {
        return new RequestContext(actorId, requestTime, idempotencyKey, hash(actorId, path, body));
    }

    // SHA-256 hex of [actorId, path, body] as one JSON array, so no input can bleed into another.
    String hash(String actorId, String path, Object body) {
        try {
            byte[] json = objectMapper.writeValueAsBytes(Arrays.asList(actorId, path, body));
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(json));
        } catch (JsonProcessingException | NoSuchAlgorithmException e) {
            throw new IllegalStateException("Cannot hash the request", e);
        }
    }
}
