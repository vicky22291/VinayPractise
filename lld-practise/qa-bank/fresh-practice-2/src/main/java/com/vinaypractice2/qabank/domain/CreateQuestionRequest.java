package com.vinaypractice2.qabank.domain;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateQuestionRequest(
        @NotBlank @Size(max = 150) String title,
        @NotBlank @Size(max = 5000) String description
) {}
