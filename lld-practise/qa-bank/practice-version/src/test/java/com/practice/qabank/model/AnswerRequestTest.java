package com.practice.qabank.model;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.util.Set;
import java.util.stream.Stream;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

class AnswerRequestTest {

    private static final ValidatorFactory FACTORY = Validation.buildDefaultValidatorFactory();
    private static final Validator VALIDATOR = FACTORY.getValidator();

    @AfterAll
    static void closeFactory() {
        FACTORY.close();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void rejectsInvalidContent(String name, AnswerRequest request) {
        Set<ConstraintViolation<AnswerRequest>> violations = VALIDATOR.validate(request);

        assertThat(violations).isNotEmpty()
                .allSatisfy(violation -> assertThat(violation.getPropertyPath()).hasToString("content"));
    }

    static Stream<Arguments> invalidRequests() {
        return Stream.of(
                arguments("content missing", new AnswerRequest(null)),
                arguments("content empty", new AnswerRequest("")),
                arguments("content blank", new AnswerRequest("   ")),
                arguments("content of 5001 chars", new AnswerRequest("x".repeat(5001))));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("validRequests")
    void acceptsBoundaryValue(String name, AnswerRequest request) {
        assertThat(VALIDATOR.validate(request)).isEmpty();
    }

    static Stream<Arguments> validRequests() {
        return Stream.of(
                arguments("content of 1 char", new AnswerRequest("x")),
                arguments("content of 5000 chars", new AnswerRequest("x".repeat(5000))));
    }
}
