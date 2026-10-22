package com.example.qabank.service;

import com.example.qabank.domain.QuestionPage;
import com.example.qabank.domain.QuestionView;

import java.util.UUID;

public interface QuestionService {
    QuestionView create(UUID authorId, String title, String body);

    QuestionView get(UUID id);

    QuestionPage list(UUID cursor, int limit);

    /** @return the question's upvote count after this vote. */
    int upvote(UUID questionId, UUID userId);
}
