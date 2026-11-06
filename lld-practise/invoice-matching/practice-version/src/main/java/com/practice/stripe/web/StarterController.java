package com.practice.stripe.web;

import java.util.Map;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/** Example endpoints proving JSON, validation, and MapStruct are configured. */
@RestController
public class StarterController {
    private final EchoMapper mapper;

    public StarterController(EchoMapper mapper) {
        this.mapper = mapper;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "UP");
    }

    @PostMapping("/echo")
    public EchoResponse echo(@Valid @RequestBody EchoRequest request) {
        return mapper.toResponse(request);
    }
}
