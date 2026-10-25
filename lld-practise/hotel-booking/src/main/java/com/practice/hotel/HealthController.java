package com.practice.hotel;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

// Sample endpoints proving the server works. Replace or delete during the mock.
@RestController
public class HealthController {

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP");
    }

    @PostMapping("/echo")
    public Map<String, Object> echo(@RequestBody Map<String, Object> body) {
        return body;
    }
}
