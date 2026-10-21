package com.example.qabank.repository.inmemory;

import com.example.qabank.domain.PageCursor;
import com.example.qabank.domain.Question;
import com.example.qabank.repository.QuestionRepository;
import org.springframework.stereotype.Repository;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.ConcurrentNavigableMap;
import java.util.concurrent.ConcurrentSkipListMap;

@Repository
public class InMemoryQuestionRepository implements QuestionRepository {
    private static final Comparator<PageCursor> NEWEST_FIRST =
            Comparator.comparing(PageCursor::createdAt).thenComparing(PageCursor::id).reversed();

    private final ConcurrentMap<UUID, Question> byId = new ConcurrentHashMap<>();
    // Same role as a DB index on (created_at DESC, id DESC): O(log n) seek to a cursor.
    // Skip-list iteration is weakly consistent, so concurrent inserts never throw CME.
    private final ConcurrentNavigableMap<PageCursor, Question> byRecency = new ConcurrentSkipListMap<>(NEWEST_FIRST);

    @Override
    public Question save(Question question) {
        // byId first, so anything a reader can see in the listing is already fetchable by id.
        byId.put(question.id(), question);
        byRecency.put(PageCursor.of(question), question);
        return question;
    }

    @Override
    public Optional<Question> findById(UUID id) {
        return Optional.ofNullable(byId.get(id));
    }

    @Override
    public List<Question> findNewestFirst(PageCursor after, int limit) {
        ConcurrentNavigableMap<PageCursor, Question> view = after == null ? byRecency : byRecency.tailMap(after, false);
        return view.values().stream().limit(limit).toList();
    }
}
