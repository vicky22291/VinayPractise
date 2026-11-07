package com.practice.stripe.web;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class EchoController {
    private final EchoMapper mapper;

    public EchoController(EchoMapper mapper) {
        this.mapper = mapper;
    }

    @PostMapping("/echo")
    public EchoResponse echo(@RequestBody EchoRequest request) {
        return mapper.toResponse(request);
    }

    public record EchoRequest(String message) {}

    public record EchoResponse(String message) {}
}
