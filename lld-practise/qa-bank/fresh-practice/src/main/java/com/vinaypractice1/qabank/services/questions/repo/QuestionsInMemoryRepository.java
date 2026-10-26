package com.vinaypractice1.qabank.services.questions.repo;

import com.vinaypractice1.qabank.exceptions.EntityNotFoundException;
import com.vinaypractice1.qabank.services.questions.model.Question;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class QuestionsInMemoryRepository  implements QuestionsRepository {
    private final Map<UUID, Question> questions;

    public QuestionsInMemoryRepository() {
        this.questions = new ConcurrentHashMap<>();
    }

    @Override
    public Question create(Question question) {
        UUID id = question.id();
        Question oldQuestion = questions.putIfAbsent(id, question);
        if (Objects.nonNull(oldQuestion)) {
            throw new IllegalStateException("Question already exists");
        }
        return question;
    }

    @Override
    public Question get(UUID id) {
        return Optional.ofNullable(questions.get(id)).orElseThrow(() -> new EntityNotFoundException(String.format("Question with id: %s is not found", id)));
    }

    @Override
    public List<Question> getAll() {
        return questions.values().stream().toList();
    }
}
