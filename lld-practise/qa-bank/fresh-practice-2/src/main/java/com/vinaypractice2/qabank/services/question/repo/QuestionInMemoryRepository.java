package com.vinaypractice2.qabank.services.question.repo;

import com.vinaypractice2.qabank.common.exceptions.EntityAlreadyExistsException;
import com.vinaypractice2.qabank.common.exceptions.EntityNotFoundException;
import com.vinaypractice2.qabank.services.question.model.Question;
import jakarta.annotation.Nonnull;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Repository of questions where the questions are stored In-Memory
 */
@Component
public class QuestionInMemoryRepository implements QuestionRepository {
    private final Map<UUID, Question> questions;

    public QuestionInMemoryRepository() {
        this.questions = new ConcurrentHashMap<>();
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Question insert(@Nonnull final Question question) throws EntityAlreadyExistsException {
        final Question oldQuestion = this.questions.putIfAbsent(question.id(), question);
        if (Objects.nonNull(oldQuestion)) {
            throw new EntityAlreadyExistsException("A question with the same id already exists: " + question.id());
        }
        return question;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Question get(@Nonnull final UUID id) throws EntityNotFoundException {
        return Optional.ofNullable(this.questions.get(id)).orElseThrow(() -> new EntityNotFoundException("No question with id: " + id));
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public List<Question> list() {
        return this.questions.values().stream().toList();
    }
}
