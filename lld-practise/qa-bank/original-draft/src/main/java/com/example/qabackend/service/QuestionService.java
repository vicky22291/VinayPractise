package com.example.qabackend.service;

import com.example.qabackend.dao.QuestionDAO;
import com.example.qabackend.model.Question;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.NoSuchElementException;
import java.util.UUID;

@Service
public class QuestionService {

    private final QuestionDAO dao;

    public QuestionService(QuestionDAO dao) {
        this.dao = dao;
    }

    public Question createQuestion(String title, String description, String authorId) {
        if (title == null || title.isBlank()) {
            throw new IllegalArgumentException("Title required");
        }
        Question q = new Question(title, description, authorId);
        dao.save(q);
        return q;
    }

    public List<Question> listQuestions(int limit, int offset) {
        return dao.findAll(limit, offset);
    }

    public void upvote(UUID id, String userId) {
        Question q = dao.findById(id);
        if (q == null) throw new NoSuchElementException("Question not found");
        q.upvote(userId);
    }
}
