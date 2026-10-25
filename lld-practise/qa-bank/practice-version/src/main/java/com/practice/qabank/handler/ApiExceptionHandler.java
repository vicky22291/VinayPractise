package com.practice.qabank.handler;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.validation.ObjectError;
import org.springframework.validation.method.ParameterErrors;
import org.springframework.validation.method.ParameterValidationResult;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import com.practice.qabank.exception.AlreadyVotedException;
import com.practice.qabank.exception.AnswerAlreadyExistsException;
import com.practice.qabank.exception.AnswerNotFoundException;
import com.practice.qabank.exception.CannotVoteOwnException;
import com.practice.qabank.exception.NotAnswerOwnerException;
import com.practice.qabank.exception.NotFoundException;
import com.practice.qabank.exception.NotOwnerException;
import com.practice.qabank.exception.NotQuestionOwnerException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.model.ErrorResponse;

// Turns every error into { "error": CODE, "message": detail }. Messages never carry stack traces or internals.
@RestControllerAdvice
public class ApiExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

    @ExceptionHandler(MissingRequestHeaderException.class)
    public ResponseEntity<ErrorResponse> handleMissingHeader(MissingRequestHeaderException e) {
        return error(HttpStatus.BAD_REQUEST, "MISSING_HEADER", "Required header '" + e.getHeaderName() + "' is missing");
    }

    // Constraint violations on the @Valid request body.
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleInvalidBody(MethodArgumentNotValidException e) {
        List<String> problems = new ArrayList<>();
        e.getBindingResult().getAllErrors().forEach(error -> problems.add(describe(error)));
        return validationFailed(problems);
    }

    // Constraint violations on header parameters, raised by Spring MVC's built-in method validation. Body violations
    // can also arrive here (as ParameterErrors), so both shapes are handled.
    @ExceptionHandler(HandlerMethodValidationException.class)
    public ResponseEntity<ErrorResponse> handleInvalidParameters(HandlerMethodValidationException e) {
        List<String> problems = new ArrayList<>();
        for (ParameterValidationResult result : e.getParameterValidationResults()) {
            if (result instanceof ParameterErrors errors) {
                errors.getAllErrors().forEach(error -> problems.add(describe(error)));
            } else {
                String name = parameterName(result.getMethodParameter());
                result.getResolvableErrors().forEach(error -> problems.add(name + ": " + error.getDefaultMessage()));
            }
        }
        return validationFailed(problems);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ErrorResponse> handleUnreadableBody(HttpMessageNotReadableException e) {
        return error(HttpStatus.BAD_REQUEST, "MALFORMED_REQUEST",
                "Request body is missing or is not valid JSON of the expected shape");
    }

    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    public ResponseEntity<ErrorResponse> handleUnsupportedMediaType(HttpMediaTypeNotSupportedException e) {
        return ResponseEntity.status(HttpStatus.UNSUPPORTED_MEDIA_TYPE)
                .headers(e.getHeaders())
                .body(new ErrorResponse("UNSUPPORTED_MEDIA_TYPE", "Content-Type must be application/json"));
    }

    // A path segment or query parameter that doesn't convert, such as a non-UUID id or a non-numeric limit. Names the
    // parameter but never echoes the raw input. Without this handler the catch-all below would turn it into a 500.
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ErrorResponse> handleTypeMismatch(MethodArgumentTypeMismatchException e) {
        return error(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED",
                e.getName() + " must be " + typePhrase(e.getRequiredType()));
    }

    // The switch is exhaustive over the sealed subtypes, so a new one without a code fails the build.
    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(NotFoundException e) {
        String code = switch (e) {
            case QuestionNotFoundException questionNotFound -> "QUESTION_NOT_FOUND";
            case AnswerNotFoundException answerNotFound -> "ANSWER_NOT_FOUND";
        };
        return error(HttpStatus.NOT_FOUND, code, e.getMessage());
    }

    @ExceptionHandler(NotOwnerException.class)
    public ResponseEntity<ErrorResponse> handleNotOwner(NotOwnerException e) {
        String code = switch (e) {
            case NotQuestionOwnerException notQuestionOwner -> "NOT_QUESTION_OWNER";
            case NotAnswerOwnerException notAnswerOwner -> "NOT_ANSWER_OWNER";
        };
        return error(HttpStatus.FORBIDDEN, code, e.getMessage());
    }

    // 403, like NOT_QUESTION_OWNER: a rule about who the caller is, so a retry can never succeed. The code names the
    // vote tried.
    @ExceptionHandler(CannotVoteOwnException.class)
    public ResponseEntity<ErrorResponse> handleCannotVoteOwn(CannotVoteOwnException e) {
        String code = switch (e.vote()) {
            case UP -> "CANNOT_UPVOTE_OWN";
            case DOWN -> "CANNOT_DOWNVOTE_OWN";
        };
        return error(HttpStatus.FORBIDDEN, code, e.getMessage());
    }

    @ExceptionHandler(AnswerAlreadyExistsException.class)
    public ResponseEntity<ErrorResponse> handleAnswerAlreadyExists(AnswerAlreadyExistsException e) {
        return error(HttpStatus.CONFLICT, "ANSWER_ALREADY_EXISTS", e.getMessage());
    }

    // The code names the vote the caller holds, not the one tried, so a downvote after an upvote is ALREADY_UPVOTED.
    @ExceptionHandler(AlreadyVotedException.class)
    public ResponseEntity<ErrorResponse> handleAlreadyVoted(AlreadyVotedException e) {
        String code = switch (e.held()) {
            case UP -> "ALREADY_UPVOTED";
            case DOWN -> "ALREADY_DOWNVOTED";
        };
        return error(HttpStatus.CONFLICT, code, e.getMessage());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handle(Exception e) {
        // Spring's own client errors (404 unknown path, 405 wrong method, 406, ...) carry their status. Keep it, so
        // only genuinely unexpected failures become a 500.
        if (e instanceof org.springframework.web.ErrorResponse springError
                && springError.getStatusCode().is4xxClientError()) {
            return clientError(springError);
        }
        log.error("Unexpected error", e);
        return error(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "An unexpected error occurred");
    }

    private static ResponseEntity<ErrorResponse> clientError(org.springframework.web.ErrorResponse springError) {
        HttpStatusCode status = springError.getStatusCode();
        HttpStatus known = HttpStatus.resolve(status.value());
        String code = known != null ? known.name() : "HTTP_" + status.value();
        String reason = known != null ? known.getReasonPhrase() : code;
        String message = Objects.requireNonNullElse(springError.getBody().getDetail(), reason);
        HttpHeaders headers = springError.getHeaders();
        return ResponseEntity.status(status).headers(headers).body(new ErrorResponse(code, message));
    }

    private static ResponseEntity<ErrorResponse> validationFailed(List<String> problems) {
        return error(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", String.join("; ", problems.stream().sorted().toList()));
    }

    private static ResponseEntity<ErrorResponse> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status).body(new ErrorResponse(code, message));
    }

    // "a UUID", but "an integer" for int and Integer rather than "a int".
    private static String typePhrase(Class<?> type) {
        if (type == null) {
            return "a valid value";
        }
        if (type == int.class || type == Integer.class) {
            return "an integer";
        }
        return "a " + type.getSimpleName();
    }

    private static String describe(ObjectError error) {
        String target = error instanceof FieldError fieldError ? fieldError.getField() : error.getObjectName();
        return target + ": " + error.getDefaultMessage();
    }

    // Report a header by its HTTP name (X-User-Id), not the Java parameter name.
    private static String parameterName(MethodParameter parameter) {
        RequestHeader header = parameter.getParameterAnnotation(RequestHeader.class);
        if (header != null) {
            String name = header.name().isEmpty() ? header.value() : header.name();
            if (!name.isEmpty()) {
                return name;
            }
        }
        return Objects.requireNonNullElse(parameter.getParameterName(), "argument " + parameter.getParameterIndex());
    }
}
