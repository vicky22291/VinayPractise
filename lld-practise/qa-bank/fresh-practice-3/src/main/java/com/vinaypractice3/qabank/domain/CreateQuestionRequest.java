package com.vinaypractice3.qabank.domain;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateQuestionRequest(
        @NotBlank @Size(max = 100) String title,
        @NotBlank @Size(max = 5000) String description
) {}
