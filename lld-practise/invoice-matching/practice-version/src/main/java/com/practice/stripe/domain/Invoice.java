package com.practice.stripe.domain;

import java.time.LocalDate;

public record Invoice(String id, long amount, LocalDate dueDate) {}
