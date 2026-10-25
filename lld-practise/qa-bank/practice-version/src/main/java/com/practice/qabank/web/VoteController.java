package com.practice.qabank.web;

import static com.practice.qabank.constants.ApiConstants.IDEMPOTENCY_KEY_HEADER;
import static com.practice.qabank.constants.ApiConstants.MAX_HEADER_LENGTH;
import static com.practice.qabank.constants.ApiConstants.REPLAYED_HEADER;
import static com.practice.qabank.constants.ApiConstants.USER_ID_HEADER;

import java.util.UUID;
import java.util.function.Function;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Vote;
import com.practice.qabank.domain.VoteResult;
import com.practice.qabank.mapper.VoteMapper;
import com.practice.qabank.model.DownvoteResponse;
import com.practice.qabank.model.UpvoteResponse;
import com.practice.qabank.service.QuestionService;

// Upvotes and downvotes. Same header rules and validation style as QuestionController. There's no body: no consumes
// and no @RequestBody, so a body or Content-Type, if sent, is ignored. A non-UUID id in either segment fails
// conversion before this runs.
@RestController
@RequestMapping("/questions/{questionId}")
public class VoteController {

    private final QuestionService service;
    private final VoteMapper mapper;

    public VoteController(QuestionService service, VoteMapper mapper) {
        this.service = service;
        this.mapper = mapper;
    }

    // The caller named by X-User-Id is the voter. The service checks the key, then 404, then 403, then 409.
    @PostMapping("/upvotes")
    public ResponseEntity<UpvoteResponse> upvoteQuestion(
            @PathVariable UUID questionId,
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String voterId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey) {
        return created(service.voteQuestion(questionId, voterId, idempotencyKey, Vote.UP), mapper::toUpvoteResponse);
    }

    @PostMapping("/answers/{answerId}/upvotes")
    public ResponseEntity<UpvoteResponse> upvoteAnswer(
            @PathVariable UUID questionId,
            @PathVariable UUID answerId,
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String voterId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey) {
        return created(service.voteAnswer(questionId, answerId, voterId, idempotencyKey, Vote.UP),
                mapper::toUpvoteResponse);
    }

    @PostMapping("/downvotes")
    public ResponseEntity<DownvoteResponse> downvoteQuestion(
            @PathVariable UUID questionId,
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String voterId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey) {
        return created(service.voteQuestion(questionId, voterId, idempotencyKey, Vote.DOWN),
                mapper::toDownvoteResponse);
    }

    @PostMapping("/answers/{answerId}/downvotes")
    public ResponseEntity<DownvoteResponse> downvoteAnswer(
            @PathVariable UUID questionId,
            @PathVariable UUID answerId,
            @RequestHeader(USER_ID_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String voterId,
            @RequestHeader(IDEMPOTENCY_KEY_HEADER) @NotBlank @Size(max = MAX_HEADER_LENGTH) String idempotencyKey) {
        return created(service.voteAnswer(questionId, answerId, voterId, idempotencyKey, Vote.DOWN),
                mapper::toDownvoteResponse);
    }

    // No Location: there's no GET for a single vote. A replay gets the same status and the stored count, plus the
    // replay marker.
    private static <T> ResponseEntity<T> created(IdempotentResult<VoteResult> result,
            Function<VoteResult, T> toResponse) {
        ResponseEntity.BodyBuilder builder = ResponseEntity.status(HttpStatus.CREATED);
        if (result.replayed()) {
            builder.header(REPLAYED_HEADER, "true");
        }
        return builder.body(toResponse.apply(result.value()));
    }
}
