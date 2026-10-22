package com.example.qabank.web;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateQuestionRequest(
        @NotBlank @Size(min = 15, max = 150) String title,
        @NotBlank @Size(max = 30_000) String body) {
}
