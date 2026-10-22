package com.example.qabank.service;

import com.example.qabank.domain.Page;
import com.example.qabank.domain.PageCursor;
import com.example.qabank.domain.Question;
import com.example.qabank.domain.QuestionView;
import com.example.qabank.domain.Vote;
import com.example.qabank.exception.DuplicateVoteException;
import com.example.qabank.exception.QuestionNotFoundException;
import com.example.qabank.exception.SelfVoteException;
import com.example.qabank.repository.QuestionRepository;
import com.example.qabank.repository.VoteRepository;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.util.List;
import java.util.UUID;

@Service
public class DefaultQuestionService implements QuestionService {
    private final QuestionRepository questions;
    private final VoteRepository votes;
    private final Clock clock;
    private final IdGenerator ids;

    public DefaultQuestionService(QuestionRepository questions, VoteRepository votes, Clock clock, IdGenerator ids) {
        this.questions = questions;
        this.votes = votes;
        this.clock = clock;
        this.ids = ids;
    }

    @Override
    public QuestionView create(UUID authorId, String title, String body) {
        Question question = questions.save(new Question(ids.next(), authorId, title, body, clock.instant()));
        return new QuestionView(question, 0);
    }

    @Override
    public QuestionView get(UUID questionId) {
        return toView(findOrThrow(questionId));
    }

    @Override
    public Page<QuestionView> list(PageCursor after, int limit) {
        if (limit < 1 || limit > MAX_PAGE_SIZE) {
            throw new IllegalArgumentException("limit must be between 1 and " + MAX_PAGE_SIZE);
        }
        // Ask for one extra row: it tells us whether a next page exists without a count query.
        List<Question> rows = questions.findNewestFirst(after, limit + 1);
        boolean hasMore = rows.size() > limit;
        List<Question> page = hasMore ? rows.subList(0, limit) : rows;
        PageCursor next = hasMore ? PageCursor.of(page.getLast()) : null;
        return new Page<>(page.stream().map(this::toView).toList(), next);
    }

    @Override
    public int upvote(UUID questionId, UUID voterId) {
        Question question = findOrThrow(questionId);
        if (question.isAuthoredBy(voterId)) {
            throw new SelfVoteException(questionId);
        }
        if (!votes.addIfAbsent(new Vote(questionId, voterId, clock.instant()))) {
            throw new DuplicateVoteException(questionId, voterId);
        }
        return votes.countByQuestionId(questionId);
    }

    private Question findOrThrow(UUID questionId) {
        return questions.findById(questionId).orElseThrow(() -> new QuestionNotFoundException(questionId));
    }

    private QuestionView toView(Question question) {
        return new QuestionView(question, votes.countByQuestionId(question.id()));
    }
}
