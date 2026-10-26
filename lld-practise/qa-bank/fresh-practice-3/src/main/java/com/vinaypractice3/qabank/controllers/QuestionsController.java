package com.vinaypractice3.qabank.controllers;

import com.vinaypractice3.qabank.commons.constants.QuestionsConstants;
import com.vinaypractice3.qabank.commons.exceptions.EntityAlreadyExistsException;
import com.vinaypractice3.qabank.commons.exceptions.EntityNotFoundException;
import com.vinaypractice3.qabank.commons.exceptions.UnauthorizedException;
import com.vinaypractice3.qabank.commons.mappers.QuestionMapper;
import com.vinaypractice3.qabank.domain.CreateQuestionRequest;
import com.vinaypractice3.qabank.domain.QuestionResponse;
import com.vinaypractice3.qabank.services.question.QuestionService;
import com.vinaypractice3.qabank.services.question.model.Question;
import jakarta.annotation.Nonnull;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Size;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping(QuestionsConstants.BASE_QUESTIONS_PATH)
public class QuestionsController {
    private final QuestionService questionService;
    private final QuestionMapper questionMapper;

    @Autowired
    public QuestionsController(@Nonnull final QuestionService questionService,
                               @Nonnull final QuestionMapper questionMapper) {
        this.questionService = questionService;
        this.questionMapper = questionMapper;
    }

    @PostMapping
    public ResponseEntity<QuestionResponse> createQuestion(@RequestBody @Valid CreateQuestionRequest createQuestionRequest,
                                                           @RequestHeader(QuestionsConstants.USER_HEADER) @Size(max = QuestionsConstants.MAX_HEADER_LENGTH) String userId) throws EntityAlreadyExistsException {
        final Question draft = this.questionMapper.toQuestion(createQuestionRequest, userId);

        final Question savedQuestion = this.questionService.create(draft);

        final QuestionResponse response = this.questionMapper.toQuestionResponse(savedQuestion);

        return ResponseEntity.created(URI.create(QuestionsConstants.BASE_QUESTIONS_PATH + "/" + response.id()))
                .body(response);
    }

    @GetMapping("/{questionId}")
    public ResponseEntity<QuestionResponse> getQuestion(@PathVariable("questionId") UUID questionId) throws EntityNotFoundException {
        final Question question = this.questionService.get(questionId);

        this.questionMapper.toQuestionResponse(question);

        return ResponseEntity.ok(this.questionMapper.toQuestionResponse(question));
    }

    @PutMapping("/{questionId}/upVote")
    public ResponseEntity<QuestionResponse> upVoteQuestion(@PathVariable("questionId") UUID questionId,
                                                           @RequestHeader(QuestionsConstants.USER_HEADER) @Size(max = QuestionsConstants.MAX_HEADER_LENGTH) String userId) throws EntityNotFoundException, EntityAlreadyExistsException, UnauthorizedException {
        final Question question = this.questionService.upVote(questionId, userId);

        this.questionMapper.toQuestionResponse(question);

        return ResponseEntity.ok(this.questionMapper.toQuestionResponse(question));
    }

    @GetMapping
    public ResponseEntity<List<QuestionResponse>> getAllQuestions() {
        final List<Question> questionList = this.questionService.list();

        final List<QuestionResponse> responseList = this.questionMapper.toListQuestionResponses(questionList);

        return ResponseEntity.ok(responseList);
    }
}
