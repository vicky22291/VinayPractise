package com.practice.qabank.domain;

import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.function.UnaryOperator;

// Immutable, including both lists and the votes, so one instance is safe to share across threads and across both
// stores. Every change returns a copy; a no-op returns this instance. The question's votes and each answer's live
// here, so every vote is a change to the question.
public record Question(
        UUID id,
        String authorId,
        String content,
        List<String> tags,
        Instant createdAt,
        Instant updatedAt,
        List<Answer> answers,
        Votes votes) {

    // Normalizing here means every Question follows the tag rule, whoever builds it (mapper, service, tests).
    public Question {
        tags = normalizeTags(tags);
        answers = answers == null ? List.of() : List.copyOf(answers);
        votes = votes == null ? Votes.NONE : votes;
    }

    public Question withIdAndCreatedAt(UUID id, Instant createdAt) {
        return new Question(Objects.requireNonNull(id, "id"), authorId, content, tags,
                Objects.requireNonNull(createdAt, "createdAt"), updatedAt, answers, votes);
    }

    // The copy is built first so tags are compared after normalization. updatedAt moves only on a real change.
    public Question withEdit(String content, List<String> tags, Instant now) {
        Question edited = new Question(id, authorId, content, tags, createdAt, now, answers, votes);
        if (Objects.equals(edited.content, this.content) && edited.tags.equals(this.tags)) {
            return this;
        }
        return edited;
    }

    // Exact, case-sensitive match on the author, like the ownership checks.
    public Optional<Answer> answerBy(String authorId) {
        return answers.stream().filter(answer -> Objects.equals(answer.authorId(), authorId)).findFirst();
    }

    public Optional<Answer> answer(UUID answerId) {
        return answers.stream().filter(answer -> Objects.equals(answer.id(), answerId)).findFirst();
    }

    // Appends last, so answers stay in the order they were added. The question's own updatedAt doesn't move: it tracks
    // edits to the question, not activity on it.
    public Question withAnswer(Answer answer) {
        List<Answer> appended = new ArrayList<>(answers);
        appended.add(Objects.requireNonNull(answer, "answer"));
        return new Question(id, authorId, content, tags, createdAt, updatedAt, appended, votes);
    }

    // Returns this on a no-op or when there's no such answer.
    public Question withAnswerEdit(UUID answerId, String content, Instant now) {
        return withAnswerChanged(answerId, answer -> answer.withEdit(content, now));
    }

    // A vote isn't an edit, so updatedAt doesn't move, as for withAnswer.
    public Question withVote(String voterId, Vote vote) {
        return new Question(id, authorId, content, tags, createdAt, updatedAt, answers, votes.with(voterId, vote));
    }

    // Neither the question's updatedAt nor the answer's moves. Returns this when there's no such answer.
    public Question withAnswerVote(UUID answerId, String voterId, Vote vote) {
        return withAnswerChanged(answerId, answer -> answer.withVote(voterId, vote));
    }

    // Replaces only the target answer, in its position. Returns this when change is a no-op or there's no such answer.
    private Question withAnswerChanged(UUID answerId, UnaryOperator<Answer> change) {
        for (int i = 0; i < answers.size(); i++) {
            Answer current = answers.get(i);
            if (!Objects.equals(current.id(), answerId)) {
                continue;
            }
            Answer changed = change.apply(current);
            if (changed == current) {
                return this;
            }
            List<Answer> replaced = new ArrayList<>(answers);
            replaced.set(i, changed);
            return new Question(id, authorId, content, tags, createdAt, updatedAt, replaced, votes);
        }
        return this;
    }

    // One tag as it's stored. The list's tag filter uses it too, so stored tags and the filter share one rule.
    public static String normalizeTag(String tag) {
        return Objects.requireNonNull(tag, "tag").toLowerCase(Locale.ROOT);
    }

    // Lowercase, drop duplicates keeping first-seen order, and copy so later changes to the caller's list can't leak in.
    private static List<String> normalizeTags(List<String> tags) {
        if (tags == null) {
            return List.of();
        }
        Set<String> unique = new LinkedHashSet<>();
        for (String tag : tags) {
            unique.add(normalizeTag(tag));
        }
        return List.copyOf(unique);
    }
}
