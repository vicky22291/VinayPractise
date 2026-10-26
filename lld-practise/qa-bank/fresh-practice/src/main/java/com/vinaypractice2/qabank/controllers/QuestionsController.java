package com.vinaypractice2.qabank.controllers;

import com.vinaypractice1.qabank.common.mappers.QuestionMapper;
import com.vinaypractice1.qabank.model.CreateQuestionRequest;
import com.vinaypractice1.qabank.model.QuestionResponse;
import com.vinaypractice1.qabank.services.questions.QuestionsService;
import com.vinaypractice1.qabank.services.questions.model.Question;
import jakarta.annotation.Nonnull;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/api/v1/questions")
public class QuestionsController {
    private final QuestionsService questionsService;
    private final QuestionMapper questionMapper;

    @Autowired
    public QuestionsController(@Nonnull final QuestionsService questionsService
    , @Nonnull final QuestionMapper questionMapper) {
        this.questionsService = questionsService;
        this.questionMapper = questionMapper;
    }

    @PostMapping
    public ResponseEntity<QuestionResponse> create(
            @RequestBody @Valid CreateQuestionRequest question,
            @RequestHeader("X-User-Id") @NotBlank @Size(max=64) String authorId
    ) {
        final Question savedQuestion = this.questionsService.create(this.questionMapper.toQuestion(question, authorId));

        return ResponseEntity.created(URI.create("/api/v1/questions/" + savedQuestion.id()))
                .body(this.questionMapper.toQuestionResponse(savedQuestion));
    }

    @GetMapping
    public ResponseEntity<List<QuestionResponse>> list() {
        return ResponseEntity.ok().body(this.questionMapper.toListQuestionResponse(this.questionsService.list()));
    }
}
