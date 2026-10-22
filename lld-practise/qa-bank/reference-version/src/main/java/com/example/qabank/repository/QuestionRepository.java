package com.example.qabank.repository;

import com.example.qabank.domain.PageCursor;
import com.example.qabank.domain.Question;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface QuestionRepository {
    Question save(Question question);

    Optional<Question> findById(UUID id);

    /** Up to {@code limit} questions, newest first, strictly after {@code after} (null = from the top). */
    List<Question> findNewestFirst(PageCursor after, int limit);
}
