package com.example.qabank.repository;

import com.example.qabank.domain.Question;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface QuestionRepository {
    void save(Question question);

    Optional<Question> findById(UUID id);

    /** Newest first, strictly after {@code after} (null means from the start). */
    List<Question> findNewestFirst(Question after, int limit);
}
