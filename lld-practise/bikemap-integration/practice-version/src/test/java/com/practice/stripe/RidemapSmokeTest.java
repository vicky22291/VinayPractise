package com.practice.stripe;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.practice.stripe.ridemap.Config;
import com.practice.stripe.ridemap.MapDrawClient;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.util.Map;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/** Environment checks only. Add exercise behavior tests as you implement it. */
class RidemapSmokeTest {
    @Test
    void defaultsPointAtTheLocalVendor() {
        var config = Config.fromEnvironment(Map.of());
        assertThat(config.baseUrl()).isEqualTo("http://127.0.0.1:8080");
        assertThat(config.apiKey()).startsWith("md_test_");
    }

    @Test
    void environmentOverridesVendorConnection() {
        var config = Config.fromEnvironment(Map.of(
                "MAPDRAW_URL", "http://localhost:9000", "MAPDRAW_API_KEY", "md_test_other"));
        assertThat(config.baseUrl()).isEqualTo("http://localhost:9000");
        assertThat(config.apiKey()).isEqualTo("md_test_other");
    }

    @Test
    void sampleRideIsAvailableFromTheProjectRoot() throws Exception {
        var config = Config.fromEnvironment(Map.of());
        var ride = new ObjectMapper().readTree(config.defaultTrack().toFile());
        assertThat(ride.path("type").asText()).isEqualTo("Feature");
        assertThat(ride.path("geometry").path("type").asText()).isEqualTo("LineString");
        assertThat(ride.path("geometry").path("coordinates").size()).isGreaterThan(2);
    }

    @Test
    void clientNormalizesBaseUrlWithoutMakingARequest() {
        var client = new MapDrawClient("http://localhost:8080/", "md_test_ridemap");
        assertThat(client.baseUrl()).isEqualTo("http://localhost:8080");
    }

    @Test
    void helpDoesNotNeedTheVendorServer() throws Exception {
        var output = new ByteArrayOutputStream();
        var errors = new ByteArrayOutputStream();
        var status = Practice.run(new String[]{"--help"}, new PrintStream(output), new PrintStream(errors));
        assertThat(status).isZero();
        assertThat(output.toString()).contains("Usage:", "part1");
        assertThat(errors.toString()).isEmpty();
    }
}
