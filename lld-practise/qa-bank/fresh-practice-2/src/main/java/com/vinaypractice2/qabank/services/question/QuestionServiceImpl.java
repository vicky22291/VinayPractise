package com.vinaypractice2.qabank.services.question;

import com.vinaypractice2.qabank.common.exceptions.EntityAlreadyExistsException;
import com.vinaypractice2.qabank.common.exceptions.EntityNotFoundException;
import com.vinaypractice2.qabank.services.question.model.Question;
import com.vinaypractice2.qabank.services.question.repo.QuestionRepository;
import jakarta.annotation.Nonnull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * Implementation of Question Service which has all the business logic
 */
@Service
public class QuestionServiceImpl implements QuestionService {
    private final QuestionRepository questionRepository;
    private final Clock clock;

    @Autowired
    public QuestionServiceImpl(@Nonnull final QuestionRepository questionRepository,
                               @Nonnull final Clock clock) {
        this.questionRepository = questionRepository;
        this.clock = clock;
    }
    /**
     * {@inheritDoc}
     */
    @Override
    public Question create(@Nonnull final Question draft) throws EntityAlreadyExistsException {
        final Question questionToBeSaved = draft.withIdAndCreatedAt(UUID.randomUUID(), clock.instant());
        return this.questionRepository.insert(questionToBeSaved);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Question get(@Nonnull final UUID id) throws EntityNotFoundException {
        return this.questionRepository.get(id);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public List<Question> list() {
        return this.questionRepository.list()
                .stream()
                .sorted(Comparator.comparing(Question::updatedAt).reversed())
                .toList();
    }
}
