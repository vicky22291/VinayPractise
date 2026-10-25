package com.practice.qabank.model;

import static com.practice.qabank.constants.ApiConstants.MAX_CONTENT_LENGTH;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

// Shared by add and update. Answers have no tags; unknown fields, tags included, are ignored by Jackson.
public record AnswerRequest(@NotBlank @Size(max = MAX_CONTENT_LENGTH) String content) {
}
