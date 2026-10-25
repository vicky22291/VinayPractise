package com.practice.qabank.constants;

// Shared by the controllers and request bodies, so each header name and limit is written once and the endpoints can't
// drift apart.
public final class ApiConstants {

    public static final String USER_ID_HEADER = "X-User-Id";
    public static final String IDEMPOTENCY_KEY_HEADER = "Idempotency-Key";
    public static final String REPLAYED_HEADER = "Idempotent-Replayed";
    // The longest X-User-Id or Idempotency-Key value. Every write endpoint checks both headers against it.
    public static final int MAX_HEADER_LENGTH = 64;

    // The longest question or answer content.
    public static final int MAX_CONTENT_LENGTH = 5000;
    public static final int MAX_TAGS = 5;
    // The tag rule. The list's tag parameter uses it too, so create, update and the filter share it.
    public static final String TAG_PATTERN = "[A-Za-z0-9+#.-]{1,35}";

    // A String because @RequestParam's defaultValue is one.
    public static final String DEFAULT_LIMIT = "20";
    public static final int MAX_LIMIT = 100;

    private ApiConstants() {
    }
}
