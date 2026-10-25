package com.practice.qabank.web;

import static com.practice.qabank.constants.ApiConstants.DEFAULT_LIMIT;
import static com.practice.qabank.constants.ApiConstants.IDEMPOTENCY_KEY_HEADER;
import static com.practice.qabank.constants.ApiConstants.MAX_HEADER_LENGTH;
import static com.practice.qabank.constants.ApiConstants.MAX_LIMIT;
import static com.practice.qabank.constants.ApiConstants.REPLAYED_HEADER;
import static com.practice.qabank.constants.ApiConstants.TAG_PATTERN;
import static com.practice.qabank.constants.ApiConstants.USER_ID_HEADER;

import java.net.URI;
import java.util.UUID;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Question;
import com.practice.qabank.mapper.QuestionMapper;
import com.practice.qabank.model.QuestionPageResponse;
import com.practice.qabank.model.QuestionRequest;
import com.practice.qabank.model.QuestionResponse;
import com.practice.qabank.service.QuestionService;

// No @Validated on the class on purpose: the header and query parameter constraints below use Spring MVC's built-in
// method validation, which reports violations as HandlerMethodValidationException (handled in ApiExceptionHandler).
@RestController
@RequestMapping("/questions")
public class QuestionController {

    private final QuestionService service;
    private final QuestionMapper mapper;

    public QuestionController(QuestionService service, QuestionMapper mapper) {
        this.service = service;
        this.mapper = mapper;
    }

    // The caller named by X-User-Id becomes the question's author.
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<QuestionResponse> create(
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String authorId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey,
            @Valid @RequestBody QuestionRequest body) {
        Question draft = mapper.toQuestion(body, authorId);
        IdempotentResult<Question> result = service.create(draft, idempotencyKey);
        QuestionResponse response = mapper.toResponse(result.value());

        // A replay gets the same status, Location and body as the original, plus the replay marker.
        ResponseEntity.BodyBuilder builder = ResponseEntity.created(URI.create("/questions/" + response.id()));
        if (result.replayed()) {
            builder.header(REPLAYED_HEADER, "true");
        }
        return builder.body(response);
    }

    // Public read: X-User-Id isn't read or validated. after and limit are converted first (a failure is a 400 from
    // ApiExceptionHandler), then the constraints are checked. An empty after= or limit= counts as absent, but an empty
    // tag= breaks the tag rule. tag is passed as sent; the service lowercases it like stored tags.
    @GetMapping
    public ResponseEntity<QuestionPageResponse> list(
            @RequestParam(required = false) @Pattern(regexp = TAG_PATTERN) String tag,
            @RequestParam(required = false) UUID after,
            @RequestParam(defaultValue = DEFAULT_LIMIT) @Min(1) @Max(MAX_LIMIT) int limit) {
        return ResponseEntity.ok(mapper.toPageResponse(service.list(tag, after, limit)));
    }

    // Public read: X-User-Id isn't read or validated. A non-UUID id fails conversion before this runs and becomes a
    // 400 in ApiExceptionHandler; any case parses to the same UUID, and the body always carries it in lower case.
    @GetMapping("/{id}")
    public ResponseEntity<QuestionResponse> get(@PathVariable UUID id) {
        return ResponseEntity.ok(mapper.toResponse(service.get(id)));
    }

    // Replaces content and tags. The caller named by X-User-Id must be the author; the service checks that after the
    // key, so every 400 and 415 here comes first. A replay is still 200 with the stored body, plus the replay marker.
    @PutMapping(path = "/{id}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<QuestionResponse> update(
            @PathVariable UUID id,
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String callerId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey,
            @Valid @RequestBody QuestionRequest body) {
        IdempotentResult<Question> result = service.update(id, mapper.toQuestion(body, callerId), idempotencyKey);

        ResponseEntity.BodyBuilder builder = ResponseEntity.ok();
        if (result.replayed()) {
            builder.header(REPLAYED_HEADER, "true");
        }
        return builder.body(mapper.toResponse(result.value()));
    }
}
