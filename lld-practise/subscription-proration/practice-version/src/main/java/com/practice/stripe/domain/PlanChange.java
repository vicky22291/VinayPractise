package com.practice.stripe.domain;

import java.time.Instant;

public record PlanChange(Instant at, Plan plan) {}
