package com.example.qabank.web;

import com.example.qabank.domain.Page;
import com.example.qabank.domain.PageCursor;
import com.example.qabank.domain.QuestionView;
import com.example.qabank.service.QuestionService;
import com.example.qabank.web.auth.CurrentUser;
import com.example.qabank.web.dto.CreateQuestionRequest;
import com.example.qabank.web.dto.QuestionPageResponse;
import com.example.qabank.web.dto.QuestionResponse;
import com.example.qabank.web.dto.QuestionSummaryResponse;
import com.example.qabank.web.dto.UpvoteResponse;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;
import java.util.UUID;

/** HTTP mapping only: parse, delegate to the service, shape the response. No business rules here. */
@RestController
@RequestMapping("/api/v1/questions")
public class QuestionController {
    private final QuestionService questionService;
    private final CursorCodec cursorCodec;

    public QuestionController(QuestionService questionService, CursorCodec cursorCodec) {
        this.questionService = questionService;
        this.cursorCodec = cursorCodec;
    }

    @PostMapping
    public ResponseEntity<QuestionResponse> create(@CurrentUser UUID userId,
                                                   @Valid @RequestBody CreateQuestionRequest request) {
        QuestionView created = questionService.create(userId, request.title(), request.body());
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
                .path("/{id}").buildAndExpand(created.question().id()).toUri();
        return ResponseEntity.created(location).body(QuestionResponse.from(created));
    }

    @GetMapping
    public QuestionPageResponse list(
            @RequestParam(defaultValue = "20") @Min(1) @Max(QuestionService.MAX_PAGE_SIZE) int limit,
            @RequestParam(required = false) String cursor) {
        PageCursor after = cursor == null ? null : cursorCodec.decode(cursor);
        Page<QuestionView> page = questionService.list(after, limit);
        String next = page.hasNext() ? cursorCodec.encode(page.nextCursor()) : null;
        return new QuestionPageResponse(page.items().stream().map(QuestionSummaryResponse::from).toList(), next);
    }

    @GetMapping("/{questionId}")
    public QuestionResponse get(@PathVariable UUID questionId) {
        return QuestionResponse.from(questionService.get(questionId));
    }

    @PostMapping("/{questionId}/upvotes")
    @ResponseStatus(HttpStatus.CREATED)
    public UpvoteResponse upvote(@PathVariable UUID questionId, @CurrentUser UUID userId) {
        return new UpvoteResponse(questionId, questionService.upvote(questionId, userId));
    }
}
