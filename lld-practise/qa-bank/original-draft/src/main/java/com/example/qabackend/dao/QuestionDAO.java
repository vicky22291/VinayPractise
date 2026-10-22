package com.example.qabackend.dao;

import com.example.qabackend.model.Question;
import org.springframework.stereotype.Repository;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Repository
public class QuestionDAO {
    private final Map<UUID, Question> questionMap = new ConcurrentHashMap<>();

    public void save(Question question) {
        questionMap.put(question.getId(), question);
    }

    public Question findById(UUID id) {
        return questionMap.get(id);
    }

    public List<Question> findAll(int limit, int offset) {
        return questionMap.values().stream()
                .skip(offset)
                .limit(limit)
                .toList();
    }
}
