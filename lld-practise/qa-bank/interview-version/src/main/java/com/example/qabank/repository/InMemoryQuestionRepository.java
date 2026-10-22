package com.example.qabank.repository;

import com.example.qabank.domain.Question;
import org.springframework.stereotype.Repository;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.NavigableSet;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentSkipListSet;

@Repository
public class InMemoryQuestionRepository implements QuestionRepository {
    // id breaks ties so two questions created in the same instant are both kept.
    private static final Comparator<Question> NEWEST_FIRST =
            Comparator.comparing(Question::createdAt).thenComparing(Question::id).reversed();

    private final Map<UUID, Question> byId = new ConcurrentHashMap<>();
    // Sorted, thread-safe index: O(log n) seek to the cursor, iteration never throws CME.
    private final NavigableSet<Question> byRecency = new ConcurrentSkipListSet<>(NEWEST_FIRST);

    @Override
    public void save(Question question) {
        byId.put(question.id(), question);
        byRecency.add(question);
    }

    @Override
    public Optional<Question> findById(UUID id) {
        return Optional.ofNullable(byId.get(id));
    }

    @Override
    public List<Question> findNewestFirst(Question after, int limit) {
        NavigableSet<Question> view = after == null ? byRecency : byRecency.tailSet(after, false);
        return view.stream().limit(limit).toList();
    }
}
