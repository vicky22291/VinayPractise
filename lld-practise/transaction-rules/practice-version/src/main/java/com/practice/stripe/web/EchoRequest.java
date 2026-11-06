package com.practice.stripe.web;

import jakarta.validation.constraints.NotBlank;

public record EchoRequest(@NotBlank String message) {}
