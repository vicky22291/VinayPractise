package com.vinaypractice1.qabank.services.questions.repo;

import com.vinaypractice1.qabank.services.questions.model.Question;

import java.util.List;
import java.util.UUID;

public interface QuestionsRepository {

    Question create(Question question);

    Question get(UUID id);

    List<Question> getAll();
}
