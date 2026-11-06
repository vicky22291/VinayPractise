package com.practice.stripe.domain;

import com.practice.stripe.exception.ApiException;
import java.util.Locale;

public final class Checks {
    private Checks() {}
    public static String text(String value, String name) {
        if (value == null || value.isBlank()) throw ApiException.invalid(name + " is required");
        return value;
    }
    public static String currency(String value) {
        if (value == null || !value.matches("[a-zA-Z]{3}"))
            throw ApiException.invalid("currency must be a three-letter code");
        return value.toUpperCase(Locale.ROOT);
    }
    public static long positive(long value, String name) {
        if (value <= 0) throw ApiException.invalid(name + " must be positive");
        return value;
    }
}
