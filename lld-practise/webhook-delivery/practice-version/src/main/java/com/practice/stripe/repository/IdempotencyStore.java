package com.practice.stripe.repository;

import com.practice.stripe.domain.Checks;
import com.practice.stripe.exception.ApiException;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Supplier;

/** Called only inside the owning repository's transaction lock. Successful immutable results are retained. */
public final class IdempotencyStore {
    private record Saved(Object request, Object result) {}
    private final Map<String, Saved> saved = new HashMap<>();

    public <T> T execute(String key, Object request, Class<T> type, Supplier<T> operation) {
        Checks.text(key, "Idempotency-Key");
        Saved previous = saved.get(key);
        if (previous != null) {
            if (!previous.request().equals(request))
                throw ApiException.conflict("Idempotency-Key was already used for a different request");
            return type.cast(previous.result());
        }
        T result = operation.get();
        saved.put(key, new Saved(request, result));
        return result;
    }
}
