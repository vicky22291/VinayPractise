package com.vinaypractice4.qabank.controllers;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

// GET /hello -> {"message":"Hello, World!"}, GET /hello?name=Vinay -> {"message":"Hello, Vinay!"}
@RestController
public class HelloWorldController {

    @GetMapping("/hello")
    public Map<String, String> hello(@RequestParam(defaultValue = "World") String name) {
        return Map.of("message", "Hello, " + name + "!");
    }
}
