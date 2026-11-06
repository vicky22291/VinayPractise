package com.practice.stripe;

import com.fasterxml.jackson.databind.ObjectMapper;

/** Plain Java entry point for coding exercises: mvn compile exec:java. */
public class Practice {
    public static void main(String[] args) throws Exception {
        var mapper = new ObjectMapper();
        var input = mapper.readTree("{\"message\":\"Transaction rule evaluator: ready\"}");
        System.out.println(input.get("message").asText());
        // Start your implementation here. Read TASK.md in this attempt first.
    }
}
