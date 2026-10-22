package com.example.qabank.service;

import com.example.qabank.domain.Page;
import com.example.qabank.domain.PageCursor;
import com.example.qabank.domain.QuestionView;

import java.util.UUID;

public interface QuestionService {
    int MAX_PAGE_SIZE = 100;

    QuestionView create(UUID authorId, String title, String body);

    QuestionView get(UUID questionId);

    /** Newest first. {@code after} is null for the first page. */
    Page<QuestionView> list(PageCursor after, int limit);

    /** @return the upvote count right after this vote was recorded. */
    int upvote(UUID questionId, UUID voterId);
}
