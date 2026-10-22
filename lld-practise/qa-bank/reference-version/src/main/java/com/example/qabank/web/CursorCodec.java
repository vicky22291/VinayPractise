package com.example.qabank.web;

import com.example.qabank.domain.PageCursor;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.UUID;

/**
 * Opaque cursor format: base64url("createdAt|id"). Clients must treat it as a token,
 * which leaves us free to change the sort key later without breaking them.
 */
@Component
public class CursorCodec {
    private static final String SEPARATOR = "|";

    public String encode(PageCursor cursor) {
        String raw = cursor.createdAt() + SEPARATOR + cursor.id();
        return Base64.getUrlEncoder().withoutPadding().encodeToString(raw.getBytes(StandardCharsets.UTF_8));
    }

    public PageCursor decode(String token) {
        try {
            String raw = new String(Base64.getUrlDecoder().decode(token), StandardCharsets.UTF_8);
            int split = raw.indexOf(SEPARATOR);
            return new PageCursor(Instant.parse(raw.substring(0, split)), UUID.fromString(raw.substring(split + 1)));
        } catch (RuntimeException e) {
            throw new InvalidCursorException(token);
        }
    }
}
