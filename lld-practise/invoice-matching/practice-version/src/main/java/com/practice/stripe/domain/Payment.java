package com.practice.stripe.domain;

public record Payment(String id, long amount, String memo) {}
