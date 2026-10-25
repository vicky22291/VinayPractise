package com.practice.qabank.service;

import java.time.Clock;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

import org.springframework.stereotype.Service;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.IdempotencyKey;
import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Operation;
import com.practice.qabank.domain.Question;
import com.practice.qabank.domain.QuestionPage;
import com.practice.qabank.domain.Vote;
import com.practice.qabank.domain.VoteResult;
import com.practice.qabank.exception.AlreadyVotedException;
import com.practice.qabank.exception.AnswerAlreadyExistsException;
import com.practice.qabank.exception.AnswerNotFoundException;
import com.practice.qabank.exception.CannotVoteOwnException;
import com.practice.qabank.exception.NotAnswerOwnerException;
import com.practice.qabank.exception.NotQuestionOwnerException;
import com.practice.qabank.exception.QuestionNotFoundException;
import com.practice.qabank.repository.IdempotencyRepository;
import com.practice.qabank.repository.QuestionRepository;

// Answers and votes live inside their question, so this service owns them too, and every answer or vote change goes
// through QuestionRepository.update. Upvotes and downvotes share every step, so the direction is a parameter.
@Service
public class QuestionService {

    // The list order: newest createdAt first, ties by id descending, so it's total. One comparator both sorts a page and
    // places its cursor, so the two can't disagree. createdAt and id never change, so neither does a question's place.
    private static final Comparator<Question> NEWEST_FIRST =
            Comparator.comparing(Question::createdAt).thenComparing(Question::id).reversed();

    private final QuestionRepository questions;
    private final IdempotencyRepository idempotency;
    private final Clock clock;

    public QuestionService(QuestionRepository questions, IdempotencyRepository idempotency, Clock clock) {
        this.questions = questions;
        this.idempotency = idempotency;
        this.clock = clock;
    }

    public IdempotentResult<Question> create(Question draft, String idempotencyKey) {
        Question candidate = draft.withIdAndCreatedAt(UUID.randomUUID(), clock.instant());
        // The author is the caller, so the author id scopes the key. Create has no target yet. The save runs inside
        // getOrCreate, so a question is stored before any replay can return it, and a failed save leaves the key
        // unrecorded.
        IdempotencyKey key = new IdempotencyKey(draft.authorId(), Operation.CREATE_QUESTION, null, idempotencyKey);
        return idempotency.getOrCreate(key, Question.class, () -> questions.save(candidate));
    }

    // Reads are public and never touch the idempotency store, so a replay can't change what GET returns.
    public Question get(UUID id) {
        return questions.findById(id).orElseThrow(() -> new QuestionNotFoundException(id));
    }

    // Newest first, with page size limit, optionally narrowed to one tag. after is exclusive and needn't carry the tag.
    // The cursor is looked up first, so an unknown after throws before any list read. One extra item is fetched to tell
    // whether a next page exists, so a client never has to fetch an empty last page.
    public QuestionPage list(String tag, UUID after, int limit) {
        if (limit < 1) {
            throw new IllegalArgumentException("limit must be at least 1, was " + limit);
        }
        Question cursor = after == null ? null : get(after);
        String wanted = tag == null ? null : Question.normalizeTag(tag);
        List<Question> matches = questions.findAll().stream()
                .filter(question -> wanted == null || question.tags().contains(wanted))
                .filter(question -> cursor == null || NEWEST_FIRST.compare(question, cursor) > 0)
                .sorted(NEWEST_FIRST)
                .limit(limit + 1L)
                .toList();
        if (matches.size() > limit) {
            List<Question> items = matches.subList(0, limit);
            return new QuestionPage(items, items.get(limit - 1).id());
        }
        return new QuestionPage(matches, null);
    }

    // draft.authorId() is the caller. The key is checked first, so a replay skips the 404 and 403 checks; it can only
    // exist after this caller's successful edit of this question. A rejection throws inside getOrCreate and records
    // nothing.
    public IdempotentResult<Question> update(UUID id, Question draft, String idempotencyKey) {
        IdempotencyKey key = new IdempotencyKey(draft.authorId(), Operation.UPDATE_QUESTION, id, idempotencyKey);
        return idempotency.getOrCreate(key, Question.class, () -> {
            Question current = get(id);
            // Safe outside the atomic change only because authorId never changes after create.
            if (!Objects.equals(current.authorId(), draft.authorId())) {
                throw new NotQuestionOwnerException(id);
            }
            // Built from q, never from current, which may be stale. The clock is read inside so updatedAt follows the
            // order the edits were applied in. Empty means the question was removed in between.
            return questions.update(id, q -> q.withEdit(draft.content(), draft.tags(), clock.instant()))
                    .orElseThrow(() -> new QuestionNotFoundException(id));
        });
    }

    public IdempotentResult<Answer> addAnswer(UUID questionId, Answer draft, String idempotencyKey) {
        Answer candidate = draft.withIdAndCreatedAt(UUID.randomUUID(), clock.instant());
        // The author is the caller, so the author id scopes the key, and the question is the target. The append runs
        // inside getOrCreate, so a seen key replays before any 404 or 409, and a 404 or 409 leaves the key unrecorded.
        IdempotencyKey key = new IdempotencyKey(draft.authorId(), Operation.ADD_ANSWER, questionId, idempotencyKey);
        return idempotency.getOrCreate(key, Answer.class, () -> appendAnswer(questionId, candidate));
    }

    // The one-answer check runs inside the atomic update, so two adds by one user under different keys can't both
    // pass. Throwing there leaves the stored question as it was.
    private Answer appendAnswer(UUID questionId, Answer candidate) {
        questions.update(questionId, question -> {
            question.answerBy(candidate.authorId()).ifPresent(existing -> {
                throw new AnswerAlreadyExistsException(questionId, existing.id());
            });
            return question.withAnswer(candidate);
        }).orElseThrow(() -> new QuestionNotFoundException(questionId));
        return candidate;
    }

    // Reads are public and never touch the idempotency store. The answer is looked up in one snapshot of its own
    // question only, so another question's answer id is not found. updateAnswer and voteAnswer find answers through
    // this too, so the rule lives only here.
    public Answer getAnswer(UUID questionId, UUID answerId) {
        return get(questionId)
                .answer(answerId)
                .orElseThrow(() -> new AnswerNotFoundException(questionId, answerId));
    }

    // draft.authorId() is the caller. Answer ids are globally unique, so the key needs no question id, and a retry
    // under a wrong questionId still replays. The key is checked first, so a replay skips the 404 and 403 checks; it
    // can only exist after this caller's successful edit of this answer. A rejection throws inside getOrCreate and
    // records nothing.
    public IdempotentResult<Answer> updateAnswer(UUID questionId, UUID answerId, Answer draft, String idempotencyKey) {
        IdempotencyKey key = new IdempotencyKey(draft.authorId(), Operation.UPDATE_ANSWER, answerId, idempotencyKey);
        return idempotency.getOrCreate(key, Answer.class, () -> {
            Answer answer = getAnswer(questionId, answerId);
            // Safe outside the atomic change only because an answer's authorId never changes. The question's author
            // fails here too: only the answer's own author may edit it.
            if (!Objects.equals(answer.authorId(), draft.authorId())) {
                throw new NotAnswerOwnerException(questionId, answerId);
            }
            // Built from q, never from getAnswer's snapshot, so answers added or edited in between are kept. The clock
            // is read inside so updatedAt follows the order the edits were applied in. Both throws below are
            // defensive: there's no delete API.
            Question updated = questions
                    .update(questionId, q -> q.withAnswerEdit(answerId, draft.content(), clock.instant()))
                    .orElseThrow(() -> new QuestionNotFoundException(questionId));
            return updated.answer(answerId).orElseThrow(() -> new AnswerNotFoundException(questionId, answerId));
        });
    }

    // The voter scopes the key and the question is the target; the Vote picks the key's operation. Every check runs
    // inside getOrCreate, so a seen key replays its stored count before any 404, 403 or 409, and a rejection records
    // nothing.
    public IdempotentResult<VoteResult> voteQuestion(UUID questionId, String voterId, String idempotencyKey,
            Vote vote) {
        IdempotencyKey key = new IdempotencyKey(voterId, vote.questionOperation(), questionId, idempotencyKey);
        return idempotency.getOrCreate(key, VoteResult.class, () -> {
            // Safe outside the atomic change only because authorId never changes and there's no delete API.
            if (Objects.equals(get(questionId).authorId(), voterId)) {
                throw CannotVoteOwnException.question(vote, questionId);
            }
            // The once-per-user check runs inside the atomic change, in both directions: of two racing votes by one
            // user, up or down, only one is stored, and the other gets it back. Throwing there leaves the question as
            // it was. Empty means the question was removed in between.
            Question voted = questions.update(questionId, q -> {
                q.votes().heldBy(voterId).ifPresent(held -> {
                    throw AlreadyVotedException.question(held, questionId);
                });
                return q.withVote(voterId, vote);
            }).orElseThrow(() -> new QuestionNotFoundException(questionId));
            // Read from the question this vote produced, so it counts this vote and every one applied before it.
            return new VoteResult(voted.votes().count(vote));
        });
    }

    // Answer ids are globally unique, so the key needs no question id, as for UPDATE_ANSWER, and a retry under a wrong
    // questionId still replays. The answer is found only under its own question, and only its own author is blocked:
    // the question's author may vote on it.
    public IdempotentResult<VoteResult> voteAnswer(UUID questionId, UUID answerId, String voterId,
            String idempotencyKey, Vote vote) {
        IdempotencyKey key = new IdempotencyKey(voterId, vote.answerOperation(), answerId, idempotencyKey);
        return idempotency.getOrCreate(key, VoteResult.class, () -> {
            // Safe outside the atomic change for the same reasons as on a question.
            if (Objects.equals(getAnswer(questionId, answerId).authorId(), voterId)) {
                throw CannotVoteOwnException.answer(vote, answerId);
            }
            // Built from q, so answers added or edited and votes cast in between are kept. Both throws after the
            // change are defensive: there's no delete API.
            Question voted = questions.update(questionId, q -> {
                q.answer(answerId).flatMap(answer -> answer.votes().heldBy(voterId)).ifPresent(held -> {
                    throw AlreadyVotedException.answer(held, answerId);
                });
                return q.withAnswerVote(answerId, voterId, vote);
            }).orElseThrow(() -> new QuestionNotFoundException(questionId));
            Answer answer = voted.answer(answerId).orElseThrow(() -> new AnswerNotFoundException(questionId, answerId));
            return new VoteResult(answer.votes().count(vote));
        });
    }
}
