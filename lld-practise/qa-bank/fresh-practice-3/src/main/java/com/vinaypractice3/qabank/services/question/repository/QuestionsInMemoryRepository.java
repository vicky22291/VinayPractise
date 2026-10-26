package com.vinaypractice3.qabank.services.question.repository;

import com.vinaypractice3.qabank.commons.exceptions.EntityAlreadyExistsException;
import com.vinaypractice3.qabank.commons.exceptions.EntityNotFoundException;
import com.vinaypractice3.qabank.services.question.model.Question;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * In-memory repository of questions.
 */
@Component
public class QuestionsInMemoryRepository implements QuestionsRepository {
    private Map<UUID, Question> questions;

    public QuestionsInMemoryRepository() {
        questions = new ConcurrentHashMap<>();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public void insert(Question draft) throws EntityAlreadyExistsException {
        final Question old = this.questions.putIfAbsent(draft.id(), draft);
        if (Objects.nonNull(old)) {
            throw new EntityAlreadyExistsException("Question with id " + draft.id() + " already exists");
        }
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Question get(UUID id) throws EntityNotFoundException {
        return Optional.ofNullable(questions.get(id))
                .orElseThrow(() -> new EntityNotFoundException("Question with id " + id + " not found"));
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public List<Question> getAll() {
        return this.questions.values().stream().toList();
    }
}
