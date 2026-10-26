package com.vinaypractice1.qabank.services.questions;

import com.vinaypractice1.qabank.services.questions.model.Question;
import com.vinaypractice1.qabank.services.questions.repo.QuestionsRepository;
import jakarta.annotation.Nonnull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;

@Service
public class QuestionsServiceImpl   implements QuestionsService {
    private final QuestionsRepository questionsRepository;
    private final Clock clock;

    @Autowired
    public QuestionsServiceImpl(@Nonnull final QuestionsRepository questionsRepository, @Nonnull Clock clock) {
        this.questionsRepository = questionsRepository;
        this.clock = clock;
    }

    @Override
    public Question create(Question question) {
        return this.questionsRepository.create(question.withIdAndCreatedAt(UUID.randomUUID(), this.clock.instant()));
    }

    @Override
    public Question get(UUID id) {
        return this.questionsRepository.get(id);
    }

    @Override
    public List<Question> list() {
        return this.questionsRepository.getAll()
                .stream()
                .sorted(Comparator.comparing(Question::updatedAt).reversed())
                .toList();
    }
}
