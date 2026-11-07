package com.practice.stripe.ridemap;

import java.nio.file.Path;
import java.util.Map;

/** Local defaults and environment overrides for the vendor connection. */
public record Config(String baseUrl, String apiKey, Path defaultTrack) {
    public static Config fromEnvironment() {
        return fromEnvironment(System.getenv());
    }

    public static Config fromEnvironment(Map<String, String> environment) {
        return new Config(
                environment.getOrDefault("MAPDRAW_URL", "http://127.0.0.1:8080"),
                environment.getOrDefault("MAPDRAW_API_KEY", "md_test_ridemap"),
                Path.of("data", "ride-simple.json"));
    }
}
