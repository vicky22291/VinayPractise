package com.practice.hotel.error;

import java.util.stream.Collectors;

import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.exc.MismatchedInputException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.validation.ObjectError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleInvalidBody(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getAllErrors().stream()
                .map(GlobalExceptionHandler::describe)
                .sorted()
                .collect(Collectors.joining("; "));
        return error(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", message);
    }

    // A constraint on a controller method parameter, such as search's @NotBlank city.
    @ExceptionHandler(HandlerMethodValidationException.class)
    public ResponseEntity<ErrorResponse> handleInvalidParameter(HandlerMethodValidationException e) {
        String message = e.getParameterValidationResults().stream()
                .flatMap(result -> result.getResolvableErrors().stream()
                        .map(error -> result.getMethodParameter().getParameterName() + " " + error.getDefaultMessage()))
                .sorted()
                .collect(Collectors.joining("; "));
        return error(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", message);
    }

    // A query parameter that can't be parsed, such as checkIn=2026-13-01. Without this, Spring answers 400 with no code.
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ErrorResponse> handleUnparsableParameter(MethodArgumentTypeMismatchException e) {
        return error(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", e.getName() + " has an invalid value");
    }

    // Valid JSON with a value of the wrong type, such as "ten" or 2.9 for a count, names the field. Anything else, such
    // as broken JSON or a missing body, is malformed.
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ErrorResponse> handleUnreadableBody(HttpMessageNotReadableException e) {
        if (e.getCause() instanceof MismatchedInputException mismatch) {
            return error(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", fieldPath(mismatch) + " has an invalid value");
        }
        return error(HttpStatus.BAD_REQUEST, "MALFORMED_REQUEST", "Request body is missing or not valid JSON");
    }

    @ExceptionHandler(MissingRequestHeaderException.class)
    public ResponseEntity<ErrorResponse> handleMissingHeader(MissingRequestHeaderException e) {
        return switch (e.getHeaderName()) {
            case "X-Admin-Id", "X-Guest-Id" -> error(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", e.getMessage());
            case "Idempotency-Key" -> error(HttpStatus.BAD_REQUEST, "IDEMPOTENCY_KEY_INVALID", e.getMessage());
            default -> error(HttpStatus.BAD_REQUEST, "VALIDATION_FAILED", e.getMessage());
        };
    }

    @ExceptionHandler(UnauthorizedException.class)
    public ResponseEntity<ErrorResponse> handleUnauthorized(UnauthorizedException e) {
        return error(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", e.getMessage());
    }

    @ExceptionHandler(InvalidIdempotencyKeyException.class)
    public ResponseEntity<ErrorResponse> handleInvalidIdempotencyKey(InvalidIdempotencyKeyException e) {
        return error(HttpStatus.BAD_REQUEST, "IDEMPOTENCY_KEY_INVALID", e.getMessage());
    }

    @ExceptionHandler(DuplicateRoomTypeException.class)
    public ResponseEntity<ErrorResponse> handleDuplicateRoomType(DuplicateRoomTypeException e) {
        return error(HttpStatus.BAD_REQUEST, "DUPLICATE_ROOM_TYPE", e.getMessage());
    }

    @ExceptionHandler(HotelNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleHotelNotFound(HotelNotFoundException e) {
        return error(HttpStatus.NOT_FOUND, "HOTEL_NOT_FOUND", e.getMessage());
    }

    @ExceptionHandler(NotHotelOwnerException.class)
    public ResponseEntity<ErrorResponse> handleNotHotelOwner(NotHotelOwnerException e) {
        return error(HttpStatus.FORBIDDEN, "NOT_HOTEL_OWNER", e.getMessage());
    }

    @ExceptionHandler(RoomTypeNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleRoomTypeNotFound(RoomTypeNotFoundException e) {
        return error(HttpStatus.NOT_FOUND, "ROOM_TYPE_NOT_FOUND", e.getMessage());
    }

    @ExceptionHandler(InvalidStayException.class)
    public ResponseEntity<ErrorResponse> handleInvalidStay(InvalidStayException e) {
        return error(HttpStatus.BAD_REQUEST, "INVALID_STAY", e.getMessage());
    }

    @ExceptionHandler(RoomsNotAvailableException.class)
    public ResponseEntity<ErrorResponse> handleRoomsNotAvailable(RoomsNotAvailableException e) {
        return error(HttpStatus.CONFLICT, "ROOMS_NOT_AVAILABLE", e.getMessage());
    }

    @ExceptionHandler(RoomCountBelowReservedException.class)
    public ResponseEntity<ErrorResponse> handleRoomCountBelowReserved(RoomCountBelowReservedException e) {
        return error(HttpStatus.CONFLICT, "ROOM_COUNT_BELOW_RESERVED", e.getMessage());
    }

    @ExceptionHandler(IdempotencyInProgressException.class)
    public ResponseEntity<ErrorResponse> handleIdempotencyInProgress(IdempotencyInProgressException e) {
        return error(HttpStatus.CONFLICT, "IDEMPOTENCY_IN_PROGRESS", e.getMessage());
    }

    @ExceptionHandler(IdempotencyKeyReusedException.class)
    public ResponseEntity<ErrorResponse> handleIdempotencyKeyReused(IdempotencyKeyReusedException e) {
        return error(HttpStatus.UNPROCESSABLE_ENTITY, "IDEMPOTENCY_KEY_REUSED", e.getMessage());
    }

    private static String describe(ObjectError error) {
        return error instanceof FieldError field
                ? field.getField() + " " + field.getDefaultMessage()
                : error.getDefaultMessage();
    }

    // Formats a Jackson path the way Bean Validation names fields, such as roomTypes[0].count.
    private static String fieldPath(JsonMappingException e) {
        StringBuilder path = new StringBuilder();
        for (JsonMappingException.Reference reference : e.getPath()) {
            if (reference.getFieldName() == null) {
                path.append('[').append(reference.getIndex()).append(']');
            } else {
                path.append(path.isEmpty() ? "" : ".").append(reference.getFieldName());
            }
        }
        return path.isEmpty() ? "body" : path.toString();
    }

    private static ResponseEntity<ErrorResponse> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status).body(new ErrorResponse(code, message));
    }
}
