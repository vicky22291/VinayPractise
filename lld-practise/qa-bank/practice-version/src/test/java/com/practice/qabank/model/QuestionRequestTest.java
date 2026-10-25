package com.practice.qabank.model;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.util.Arrays;
import java.util.List;
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

class QuestionRequestTest {

    private static final ValidatorFactory FACTORY = Validation.buildDefaultValidatorFactory();
    private static final Validator VALIDATOR = FACTORY.getValidator();
    private static final String CONTENT = "How do I make a ConcurrentHashMap value update atomic?";

    @AfterAll
    static void closeFactory() {
        FACTORY.close();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidRequests")
    void rejectsInvalidValueOnTheRightField(String name, QuestionRequest request, String field) {
        Set<ConstraintViolation<QuestionRequest>> violations = VALIDATOR.validate(request);

        assertThat(violations).isNotEmpty()
                .allSatisfy(violation -> assertThat(rootField(violation)).isEqualTo(field));
    }

    static Stream<Arguments> invalidRequests() {
        return Stream.of(
                arguments("content missing", new QuestionRequest(null, null), "content"),
                arguments("content empty", new QuestionRequest("", null), "content"),
                arguments("content blank", new QuestionRequest("   ", null), "content"),
                arguments("content of 5001 chars", new QuestionRequest("x".repeat(5001), null), "content"),
                arguments("6 tags", new QuestionRequest(CONTENT, List.of("a", "b", "c", "d", "e", "f")), "tags"),
                arguments("empty tag", new QuestionRequest(CONTENT, List.of("")), "tags"),
                arguments("blank tag", new QuestionRequest(CONTENT, List.of("   ")), "tags"),
                arguments("null tag", new QuestionRequest(CONTENT, Arrays.asList("java", null)), "tags"),
                arguments("tag with a space", new QuestionRequest(CONTENT, List.of("spring boot")), "tags"),
                arguments("tag with a disallowed symbol", new QuestionRequest(CONTENT, List.of("java!")), "tags"),
                arguments("tag of 36 chars", new QuestionRequest(CONTENT, List.of("t".repeat(36))), "tags"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("validRequests")
    void acceptsBoundaryValue(String name, QuestionRequest request) {
        assertThat(VALIDATOR.validate(request)).isEmpty();
    }

    static Stream<Arguments> validRequests() {
        return Stream.of(
                arguments("content of 1 char", new QuestionRequest("x", null)),
                arguments("content of 5000 chars", new QuestionRequest("x".repeat(5000), null)),
                arguments("tags missing", new QuestionRequest(CONTENT, null)),
                arguments("no tags", new QuestionRequest(CONTENT, List.of())),
                arguments("5 tags", new QuestionRequest(CONTENT, List.of("a", "b", "c", "d", "e"))),
                arguments("tag of 1 char", new QuestionRequest(CONTENT, List.of("r"))),
                arguments("tag of 35 chars", new QuestionRequest(CONTENT, List.of("t".repeat(35)))),
                arguments("tags with allowed symbols",
                        new QuestionRequest(CONTENT, List.of("C#", "c++", ".NET", "objective-c", "Java21"))));
    }

    private static String rootField(ConstraintViolation<?> violation) {
        return violation.getPropertyPath().iterator().next().getName();
    }
}
