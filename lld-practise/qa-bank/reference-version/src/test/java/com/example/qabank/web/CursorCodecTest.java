package com.example.qabank.web;

import com.example.qabank.domain.PageCursor;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CursorCodecTest {
    private final CursorCodec codec = new CursorCodec();

    @Test
    void roundTrips() {
        PageCursor cursor = new PageCursor(Instant.parse("2026-01-01T10:15:30.123456Z"), UUID.randomUUID());

        String token = codec.encode(cursor);

        assertThat(token).doesNotContain("|", "=", "+", "/");
        assertThat(codec.decode(token)).isEqualTo(cursor);
    }

    @ParameterizedTest
    @ValueSource(strings = {"", "not-base64!!", "aGVsbG8", "MjAyNi0wMS0wMVQwMDowMDowMFp8bm90LWEtdXVpZA"})
    void rejectsGarbage(String token) {
        assertThatThrownBy(() -> codec.decode(token)).isInstanceOf(InvalidCursorException.class);
    }
}
