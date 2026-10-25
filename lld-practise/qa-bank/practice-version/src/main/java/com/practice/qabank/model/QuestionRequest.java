package com.practice.qabank.model;

import static com.practice.qabank.constants.ApiConstants.MAX_CONTENT_LENGTH;
import static com.practice.qabank.constants.ApiConstants.MAX_TAGS;
import static com.practice.qabank.constants.ApiConstants.TAG_PATTERN;

import java.util.List;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

// Shared by create and update, so the rules live in one place. Only content and tags are read from the body; unknown
// fields such as id or createdAt are ignored by Jackson.
public record QuestionRequest(
        @NotBlank @Size(max = MAX_CONTENT_LENGTH) String content,
        @Size(max = MAX_TAGS) List<@NotBlank @Pattern(regexp = TAG_PATTERN) String> tags) {
}
