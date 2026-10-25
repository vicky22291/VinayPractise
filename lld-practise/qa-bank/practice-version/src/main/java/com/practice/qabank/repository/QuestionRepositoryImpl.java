package com.practice.qabank.repository;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.UnaryOperator;

import org.springframework.stereotype.Repository;

import com.practice.qabank.domain.Question;

@Repository
public class QuestionRepositoryImpl implements QuestionRepository {

    private final ConcurrentHashMap<UUID, Question> store = new ConcurrentHashMap<>();

    @Override
    public Question save(Question question) {
        UUID id = Objects.requireNonNull(question.id(), "question id");
        // putIfAbsent instead of put: a duplicate id is a bug, so fail loudly rather than overwrite silently.
        if (store.putIfAbsent(id, question) != null) {
            throw new IllegalStateException("Question already exists: " + id);
        }
        return question;
    }

    @Override
    public Optional<Question> findById(UUID id) {
        return Optional.ofNullable(store.get(id));
    }

    // No lock: the values view never throws ConcurrentModificationException, and sees each entry once. An entry replaced
    // during the copy shows up as the old instance or the new one, never a mix, because questions are immutable.
    @Override
    public List<Question> findAll() {
        return List.copyOf(store.values());
    }

    @Override
    public Optional<Question> update(UUID id, UnaryOperator<Question> change) {
        // computeIfPresent runs read, change and write as one step per id, so concurrent changes to one question apply
        // one after another, each on the previous result. Throwing inside leaves the entry as it was.
        return Optional.ofNullable(store.computeIfPresent(id, (key, current) -> {
            Question changed = change.apply(current);
            // A null result would silently remove the question, and another id would file it under the wrong key.
            if (changed == null) {
                throw new IllegalStateException("Change to question " + id + " returned null");
            }
            if (!id.equals(changed.id())) {
                throw new IllegalStateException("Change to question " + id + " returned question " + changed.id());
            }
            return changed;
        }));
    }
}
