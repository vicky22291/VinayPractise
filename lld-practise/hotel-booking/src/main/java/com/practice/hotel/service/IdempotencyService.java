package com.practice.hotel.service;

import java.util.function.Supplier;

import com.practice.hotel.domain.OperationType;

public interface IdempotencyService {

    // Runs action at most once per (operation, idempotency key) and returns the id of the resource it produced.
    String execute(OperationType operation, RequestContext context, Supplier<String> action);
}
