package com.vinaypractice2.qabank.controllers;

import com.vinaypractice2.qabank.common.exceptions.EntityAlreadyExistsException;
import com.vinaypractice2.qabank.common.exceptions.EntityNotFoundException;
import com.vinaypractice2.qabank.common.mappers.QuestionMapper;
import com.vinaypractice2.qabank.domain.CreateQuestionRequest;
import com.vinaypractice2.qabank.domain.QuestionResponse;
import com.vinaypractice2.qabank.services.question.QuestionService;
import com.vinaypractice2.qabank.services.question.model.Question;
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
@RequestMapping("/api/v1/questions")
public class QuestionsController {
    private final QuestionService questionService;
    private final QuestionMapper questionMapper;

    @Autowired
    public QuestionsController(@Nonnull final QuestionService questionService,
                               @Nonnull final QuestionMapper questionMapper) {
        this.questionService = questionService;
        this.questionMapper = questionMapper;
    }

    /**
     * Creates a question based on the title, description and user.
     * @param createQuestionRequest - Create request with Title and description.
     * @param userId - ID of the author
     * @return the saved question.
     * @throws EntityAlreadyExistsException, thrown when a question already exists.
     */
    @PostMapping
    public ResponseEntity<QuestionResponse> create(
            @RequestBody @Valid CreateQuestionRequest createQuestionRequest,
            @RequestHeader(value = "X-User-Id") @Size(max = 64) String userId) throws EntityAlreadyExistsException {

        // Mapping to internal object
        final Question draft = this.questionMapper.toQuestion(createQuestionRequest, userId);

        // Actual Insertion
        final Question savedQuestion = this.questionService.create(draft);

        // Mapping saved question to response
        final QuestionResponse questionResponse = this.questionMapper.toQuestionResponse(savedQuestion);

        // Actual Response.
        return ResponseEntity.created(URI.create("/api/v1/questions/" + questionResponse.id())).body(questionResponse);
    }

    /**
     * Returns the question that is requested.
     * @param questionId - id of the question
     * @return Question
     * @throws EntityNotFoundException - thrown when not found.
     */
    @GetMapping("/{questionId}")
    public ResponseEntity<QuestionResponse> get(@PathVariable UUID questionId) throws EntityNotFoundException {

        // Getting the question based on id.
        final Question question = this.questionService.get(questionId);

        // Mapping saved question to response
        final QuestionResponse questionResponse = this.questionMapper.toQuestionResponse(question);

        // Actual Response.
        return ResponseEntity.ok(questionResponse);
    }

    /**
     * Returns the list of questions.
     * @return list of questions
     */
    @GetMapping
    public ResponseEntity<List<QuestionResponse>> getAll() {
        final List<Question> questionList = this.questionService.list();

        final List<QuestionResponse> responseList = this.questionMapper.toListQuestions(questionList);

        return ResponseEntity.ok(responseList);
    }
}
