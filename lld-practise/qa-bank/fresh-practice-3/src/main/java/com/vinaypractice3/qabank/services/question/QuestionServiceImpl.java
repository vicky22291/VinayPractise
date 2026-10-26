package com.vinaypractice3.qabank.services.question;

import com.vinaypractice3.qabank.commons.exceptions.EntityAlreadyExistsException;
import com.vinaypractice3.qabank.commons.exceptions.EntityNotFoundException;
import com.vinaypractice3.qabank.commons.exceptions.UnauthorizedException;
import com.vinaypractice3.qabank.services.question.model.Question;
import com.vinaypractice3.qabank.services.question.repository.QuestionsRepository;
import jakarta.annotation.Nonnull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

/**
 * Implementation of QuestionService.
 */
@Service
public class QuestionServiceImpl implements QuestionService {
    private final QuestionsRepository questionRepository;
    private final Clock clock;

    @Autowired
    public QuestionServiceImpl(@Nonnull final QuestionsRepository questionRepository,
                               @Nonnull final Clock clock) {
        this.questionRepository = questionRepository;
        this.clock = clock;
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Question create(@Nonnull final Question draft) throws EntityAlreadyExistsException {
        final Question questionToBeSaved = draft.withIdAndCreatedAt(UUID.randomUUID(), this.clock.instant());

        this.questionRepository.insert(questionToBeSaved);

        return questionToBeSaved;
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
        return this.questionRepository.getAll()
                .stream()
                .sorted(Comparator.comparing(Question::updatedAt).reversed())
                .toList();
    }

    @Override
    public Question upVote(UUID id, String userId) throws EntityNotFoundException, UnauthorizedException, EntityAlreadyExistsException {
        final Question question = this.questionRepository.get(id);
        if (userId.equals(question.authorId())) {
            throw new UnauthorizedException("Author is not allowed to vote.");
        } else if (question.upVotes().contains(userId)) {
            throw new EntityAlreadyExistsException("User has already voted.");
        }
        question.upVotes().add(userId);
        return question;
    }
}
