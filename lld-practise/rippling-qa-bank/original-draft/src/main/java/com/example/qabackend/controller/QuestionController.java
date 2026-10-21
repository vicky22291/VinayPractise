package com.example.qabackend.controller;

import com.example.qabackend.dto.CreateQuestionReq;
import com.example.qabackend.dto.VoteReq;
import com.example.qabackend.model.Question;
import com.example.qabackend.service.QuestionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.NoSuchElementException;
import java.util.UUID;

@RestController
@RequestMapping("/questions")
public class QuestionController {

    private final QuestionService service;

    public QuestionController(QuestionService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<?> create(@RequestBody CreateQuestionReq req) {
        try {
            Question q = service.createQuestion(req.title(), req.description(), req.authorId());
            return ResponseEntity.status(HttpStatus.CREATED).body(q);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }

    @GetMapping
    public ResponseEntity<List<Question>> list(
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(defaultValue = "0") int offset) {
        return ResponseEntity.ok(service.listQuestions(limit, offset));
    }

    @PostMapping("/{id}/upvote")
    public ResponseEntity<?> upvote(@PathVariable UUID id, @RequestBody VoteReq req) {
        try {
            service.upvote(id, req.userId());
            return ResponseEntity.ok().build();
        } catch (NoSuchElementException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
