package com.example.qabank.web;

import com.example.qabank.domain.QuestionPage;
import com.example.qabank.domain.QuestionView;
import com.example.qabank.service.QuestionService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/questions")
public class QuestionController {
    // MVP caller identity. In production a JWT filter supplies the user id instead.
    static final String USER_HEADER = "X-User-Id";

    private final QuestionService service;

    public QuestionController(QuestionService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<QuestionResponse> create(@RequestHeader(USER_HEADER) UUID userId,
                                                   @Valid @RequestBody CreateQuestionRequest request) {
        QuestionView created = service.create(userId, request.title(), request.body());
        URI location = URI.create("/api/v1/questions/" + created.question().id());
        return ResponseEntity.created(location).body(QuestionResponse.from(created));
    }

    @GetMapping
    public PageResponse list(@RequestParam(defaultValue = "20") @Min(1) @Max(100) int limit,
                             @RequestParam(required = false) UUID cursor) {
        QuestionPage page = service.list(cursor, limit);
        return new PageResponse(page.items().stream().map(QuestionResponse::from).toList(), page.nextCursor());
    }

    @GetMapping("/{id}")
    public QuestionResponse get(@PathVariable UUID id) {
        return QuestionResponse.from(service.get(id));
    }

    @PostMapping("/{id}/upvotes")
    @ResponseStatus(HttpStatus.CREATED)
    public UpvoteResponse upvote(@PathVariable UUID id, @RequestHeader(USER_HEADER) UUID userId) {
        return new UpvoteResponse(id, service.upvote(id, userId));
    }
}
