package com.practice.qabank.repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.function.UnaryOperator;

import com.practice.qabank.domain.Question;

public interface QuestionRepository {

    /**
     * Stores a new question and returns the same instance.
     *
     * @throws IllegalStateException if a question with the same id is already stored
     */
    Question save(Question question);

    Optional<Question> findById(UUID id);

    /**
     * Returns every stored question once, as an unmodifiable snapshot in no particular order. It holds every question
     * stored before the call started, and maybe some stored during it. Ordering and filtering are the caller's job.
     */
    List<Question> findAll();

    /**
     * Replaces the stored question with {@code change} applied to it, as one atomic step per id, and returns the
     * result. Returns empty, without calling {@code change}, when no question has that id. Every change to a stored
     * question goes through here: question edits, answer adds and answer edits.
     * <p>
     * {@code change} must build from the question it's given, be short, and not write to this repository. If it
     * throws, the stored question stays as it was.
     *
     * @throws IllegalStateException if {@code change} returns {@code null} or a question with another id
     */
    Optional<Question> update(UUID id, UnaryOperator<Question> change);
}
