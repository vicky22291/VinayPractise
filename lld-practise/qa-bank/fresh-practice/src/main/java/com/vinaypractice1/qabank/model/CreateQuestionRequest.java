package com.vinaypractice1.qabank.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateQuestionRequest(
        @NotBlank(message = "Title is required") @Size(max = 150) String title,
        @NotBlank(message = "Content is required") @Size(max = 5000) String content
) {}
