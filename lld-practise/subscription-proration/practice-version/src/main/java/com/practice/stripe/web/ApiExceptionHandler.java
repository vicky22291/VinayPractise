package com.practice.stripe.web;

import com.practice.stripe.exception.ApiException;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(ApiException.class)
    ResponseEntity<Map<String, String>> domain(ApiException error) {
        return ResponseEntity.status(error.status()).body(Map.of("error", error.getMessage()));
    }
    @ExceptionHandler({IllegalArgumentException.class, ArithmeticException.class})
    ResponseEntity<Map<String, String>> invalid(RuntimeException error) {
        return ResponseEntity.badRequest().body(Map.of("error", "Invalid input: " + error.getMessage()));
    }
}
