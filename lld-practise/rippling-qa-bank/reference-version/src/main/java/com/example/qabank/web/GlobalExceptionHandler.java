package com.example.qabank.web;

import com.example.qabank.exception.DuplicateVoteException;
import com.example.qabank.exception.QuestionNotFoundException;
import com.example.qabank.exception.SelfVoteException;
import com.example.qabank.web.auth.UnauthenticatedException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.lang.NonNull;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import java.util.Map;
import java.util.TreeMap;

/**
 * Maps domain exceptions to HTTP, so the service layer never imports an HTTP type.
 * Every error body is an RFC 9457 ProblemDetail. The parent class already covers malformed JSON,
 * type mismatches, method validation (limit out of range) and unknown routes.
 */
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(QuestionNotFoundException.class)
    ProblemDetail handleNotFound(QuestionNotFoundException e) {
        return problem(HttpStatus.NOT_FOUND, "Question not found", e);
    }

    @ExceptionHandler(DuplicateVoteException.class)
    ProblemDetail handleDuplicateVote(DuplicateVoteException e) {
        return problem(HttpStatus.CONFLICT, "Already upvoted", e);
    }

    @ExceptionHandler(SelfVoteException.class)
    ProblemDetail handleSelfVote(SelfVoteException e) {
        return problem(HttpStatus.FORBIDDEN, "Cannot upvote own question", e);
    }

    @ExceptionHandler(InvalidCursorException.class)
    ProblemDetail handleInvalidCursor(InvalidCursorException e) {
        return problem(HttpStatus.BAD_REQUEST, "Invalid cursor", e);
    }

    @ExceptionHandler(UnauthenticatedException.class)
    ProblemDetail handleUnauthenticated(UnauthenticatedException e) {
        return problem(HttpStatus.UNAUTHORIZED, "Unauthenticated", e);
    }

    @ExceptionHandler(Exception.class)
    ProblemDetail handleUnexpected(Exception e) {
        log.error("Unhandled exception", e);
        // Never echo internal messages or stack traces to the client.
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Unexpected error");
        detail.setTitle("Internal error");
        return detail;
    }

    /** Adds a field -> message map so clients can highlight the exact invalid inputs. */
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(@NonNull MethodArgumentNotValidException e,
                                                                  @NonNull HttpHeaders headers,
                                                                  @NonNull HttpStatusCode status,
                                                                  @NonNull WebRequest request) {
        ProblemDetail detail = e.getBody();
        Map<String, String> errors = new TreeMap<>();
        e.getBindingResult().getFieldErrors().forEach(err -> errors.putIfAbsent(err.getField(), err.getDefaultMessage()));
        detail.setProperty("errors", errors);
        return handleExceptionInternal(e, detail, headers, status, request);
    }

    private static ProblemDetail problem(HttpStatus status, String title, RuntimeException e) {
        ProblemDetail detail = ProblemDetail.forStatusAndDetail(status, e.getMessage());
        detail.setTitle(title);
        return detail;
    }
}
