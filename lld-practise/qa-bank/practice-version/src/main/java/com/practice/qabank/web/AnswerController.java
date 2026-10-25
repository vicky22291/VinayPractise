package com.practice.qabank.web;

import static com.practice.qabank.constants.ApiConstants.IDEMPOTENCY_KEY_HEADER;
import static com.practice.qabank.constants.ApiConstants.MAX_HEADER_LENGTH;
import static com.practice.qabank.constants.ApiConstants.REPLAYED_HEADER;
import static com.practice.qabank.constants.ApiConstants.USER_ID_HEADER;

import java.net.URI;
import java.util.UUID;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
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
import org.springframework.web.bind.annotation.RestController;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.mapper.QuestionMapper;
import com.practice.qabank.model.AnswerRequest;
import com.practice.qabank.model.AnswerResponse;
import com.practice.qabank.service.QuestionService;

// Same header rules and validation style as QuestionController: no @Validated on the class, so header violations
// come from Spring MVC's built-in method validation. A non-UUID questionId fails conversion before this runs.
@RestController
@RequestMapping("/questions/{questionId}/answers")
public class AnswerController {

    private final QuestionService service;
    private final QuestionMapper mapper;

    public AnswerController(QuestionService service, QuestionMapper mapper) {
        this.service = service;
        this.mapper = mapper;
    }

    // The caller named by X-User-Id becomes the answer's author.
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<AnswerResponse> add(
            @PathVariable UUID questionId,
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String authorId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey,
            @Valid @RequestBody AnswerRequest body) {
        Answer draft = mapper.toAnswer(body, authorId);
        IdempotentResult<Answer> result = service.addAnswer(questionId, draft, idempotencyKey);
        AnswerResponse response = mapper.toResponse(result.value());

        // A replay gets the same status, Location and body as the original, plus the replay marker. The Location uses
        // the parsed questionId, so it's lower case whatever case the request used.
        ResponseEntity.BodyBuilder builder =
                ResponseEntity.created(URI.create("/questions/" + questionId + "/answers/" + response.id()));
        if (result.replayed()) {
            builder.header(REPLAYED_HEADER, "true");
        }
        return builder.body(response);
    }

    // Public read: X-User-Id isn't read or validated. A non-UUID id in either segment fails conversion before this
    // runs; any case parses to the same UUID, and the body always carries the id in lower case.
    @GetMapping("/{answerId}")
    public ResponseEntity<AnswerResponse> get(@PathVariable UUID questionId, @PathVariable UUID answerId) {
        return ResponseEntity.ok(mapper.toResponse(service.getAnswer(questionId, answerId)));
    }

    // Replaces the answer's content. The caller named by X-User-Id must be the answer's author; the service checks
    // that after the key and the 404s, so every 400 and 415 here comes first. A replay is still 200 with the stored
    // body, plus the replay marker.
    @PutMapping(path = "/{answerId}", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<AnswerResponse> update(
            @PathVariable UUID questionId,
            @PathVariable UUID answerId,
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String callerId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey,
            @Valid @RequestBody AnswerRequest body) {
        IdempotentResult<Answer> result =
                service.updateAnswer(questionId, answerId, mapper.toAnswer(body, callerId), idempotencyKey);

        ResponseEntity.BodyBuilder builder = ResponseEntity.ok();
        if (result.replayed()) {
            builder.header(REPLAYED_HEADER, "true");
        }
        return builder.body(mapper.toResponse(result.value()));
    }
}
