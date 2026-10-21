package com.example.qabank.service;

import com.example.qabank.domain.Page;
import com.example.qabank.domain.QuestionView;
import com.example.qabank.exception.DuplicateVoteException;
import com.example.qabank.exception.QuestionNotFoundException;
import com.example.qabank.exception.SelfVoteException;
import com.example.qabank.repository.inmemory.InMemoryQuestionRepository;
import com.example.qabank.repository.inmemory.InMemoryVoteRepository;
import com.example.qabank.support.MutableClock;
import com.example.qabank.support.SequentialIdGenerator;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

// Uses the real in-memory repositories instead of mocks: they are cheap, deterministic,
// and catch wiring mistakes a mock would hide.
class DefaultQuestionServiceTest {
    private static final Instant T0 = Instant.parse("2026-01-01T00:00:00Z");
    private static final UUID AUTHOR = UUID.fromString("aaaaaaaa-0000-0000-0000-000000000001");
    private static final UUID VOTER = UUID.fromString("bbbbbbbb-0000-0000-0000-000000000002");

    private final MutableClock clock = new MutableClock(T0);
    private final QuestionService service = new DefaultQuestionService(
            new InMemoryQuestionRepository(), new InMemoryVoteRepository(), clock, new SequentialIdGenerator());

    @Test
    void createAssignsIdAndTimestampAndStartsAtZeroVotes() {
        QuestionView created = service.create(AUTHOR, "How do I parse JSON in Java?", "Details");

        assertThat(created.question().id()).isEqualTo(new UUID(0, 1));
        assertThat(created.question().createdAt()).isEqualTo(T0);
        assertThat(created.upvotes()).isZero();
        assertThat(service.get(created.question().id())).isEqualTo(created);
    }

    @Test
    void listReturnsNewestFirst() {
        UUID first = createAndTick("First question title here");
        UUID second = createAndTick("Second question title here");
        UUID third = createAndTick("Third question title here");

        Page<QuestionView> page = service.list(null, 10);

        assertThat(page.items()).extracting(v -> v.question().id()).containsExactly(third, second, first);
        assertThat(page.hasNext()).isFalse();
    }

    @Test
    void listPagesWithCursorAndSignalsLastPage() {
        UUID first = createAndTick("First question title here");
        UUID second = createAndTick("Second question title here");
        UUID third = createAndTick("Third question title here");

        Page<QuestionView> page1 = service.list(null, 2);
        Page<QuestionView> page2 = service.list(page1.nextCursor(), 2);

        assertThat(page1.items()).extracting(v -> v.question().id()).containsExactly(third, second);
        assertThat(page2.items()).extracting(v -> v.question().id()).containsExactly(first);
        assertThat(page2.hasNext()).isFalse();
    }

    @Test
    void questionsWithIdenticalTimestampsAreAllListed() {
        UUID a = service.create(AUTHOR, "Same instant question A", "b").question().id();
        UUID b = service.create(AUTHOR, "Same instant question B", "b").question().id();

        assertThat(service.list(null, 10).items()).extracting(v -> v.question().id()).containsExactlyInAnyOrder(a, b);
    }

    @Test
    void upvoteIncrementsCount() {
        UUID id = createAndTick("A question worth voting on");

        assertThat(service.upvote(id, VOTER)).isEqualTo(1);
        assertThat(service.upvote(id, UUID.randomUUID())).isEqualTo(2);
        assertThat(service.get(id).upvotes()).isEqualTo(2);
    }

    @Test
    void duplicateVoteIsRejectedAndNotCounted() {
        UUID id = createAndTick("A question worth voting on");
        service.upvote(id, VOTER);

        assertThatThrownBy(() -> service.upvote(id, VOTER)).isInstanceOf(DuplicateVoteException.class);
        assertThat(service.get(id).upvotes()).isEqualTo(1);
    }

    @Test
    void authorCannotUpvoteOwnQuestion() {
        UUID id = createAndTick("A question worth voting on");

        assertThatThrownBy(() -> service.upvote(id, AUTHOR)).isInstanceOf(SelfVoteException.class);
        assertThat(service.get(id).upvotes()).isZero();
    }

    @Test
    void unknownQuestionIsNotFound() {
        UUID unknown = UUID.randomUUID();

        assertThatThrownBy(() -> service.upvote(unknown, VOTER)).isInstanceOf(QuestionNotFoundException.class);
        assertThatThrownBy(() -> service.get(unknown)).isInstanceOf(QuestionNotFoundException.class);
    }

    @Test
    void limitOutsideBoundsIsRejected() {
        assertThatThrownBy(() -> service.list(null, 0)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.list(null, QuestionService.MAX_PAGE_SIZE + 1))
                .isInstanceOf(IllegalArgumentException.class);
    }

    private UUID createAndTick(String title) {
        UUID id = service.create(AUTHOR, title, "body").question().id();
        clock.advance(Duration.ofSeconds(1));
        return id;
    }
}
