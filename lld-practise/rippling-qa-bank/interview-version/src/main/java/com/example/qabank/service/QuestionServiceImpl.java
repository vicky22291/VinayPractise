package com.example.qabank.service;

import com.example.qabank.domain.Question;
import com.example.qabank.domain.QuestionPage;
import com.example.qabank.domain.QuestionView;
import com.example.qabank.exception.DuplicateVoteException;
import com.example.qabank.exception.InvalidCursorException;
import com.example.qabank.exception.QuestionNotFoundException;
import com.example.qabank.exception.SelfVoteException;
import com.example.qabank.repository.QuestionRepository;
import com.example.qabank.repository.VoteRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
public class QuestionServiceImpl implements QuestionService {
    private final QuestionRepository questions;
    private final VoteRepository votes;

    public QuestionServiceImpl(QuestionRepository questions, VoteRepository votes) {
        this.questions = questions;
        this.votes = votes;
    }

    @Override
    public QuestionView create(UUID authorId, String title, String body) {
        Question question = new Question(UUID.randomUUID(), authorId, title, body, Instant.now());
        questions.save(question);
        return new QuestionView(question, 0);
    }

    @Override
    public QuestionView get(UUID id) {
        return toView(findOrThrow(id));
    }

    @Override
    public QuestionPage list(UUID cursor, int limit) {
        Question after = cursor == null ? null
                : questions.findById(cursor).orElseThrow(() -> new InvalidCursorException(cursor));
        List<QuestionView> items = questions.findNewestFirst(after, limit).stream().map(this::toView).toList();
        UUID next = !items.isEmpty() && items.size() == limit ? items.get(limit - 1).question().id() : null;
        return new QuestionPage(items, next);
    }

    @Override
    public int upvote(UUID questionId, UUID userId) {
        Question question = findOrThrow(questionId);
        if (question.authorId().equals(userId)) {
            throw new SelfVoteException(questionId);
        }
        if (!votes.add(questionId, userId)) {
            throw new DuplicateVoteException(questionId);
        }
        return votes.count(questionId);
    }

    private Question findOrThrow(UUID id) {
        return questions.findById(id).orElseThrow(() -> new QuestionNotFoundException(id));
    }

    private QuestionView toView(Question question) {
        return new QuestionView(question, votes.count(question.id()));
    }
}
