package com.practice.qabank.mapper;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.tuple;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.mapstruct.factory.Mappers;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.Question;
import com.practice.qabank.domain.QuestionPage;
import com.practice.qabank.domain.Votes;
import com.practice.qabank.model.AnswerRequest;
import com.practice.qabank.model.AnswerResponse;
import com.practice.qabank.model.QuestionPageResponse;
import com.practice.qabank.model.QuestionRequest;
import com.practice.qabank.model.QuestionResponse;
import com.practice.qabank.model.QuestionSummaryResponse;

class QuestionMapperTest {

    private static final Instant CREATED_AT = Instant.parse("2026-10-24T06:12:45.123Z");
    private static final Instant UPDATED_AT = Instant.parse("2026-10-24T06:20:03.456Z");

    private final QuestionMapper mapper = Mappers.getMapper(QuestionMapper.class);

    @Test
    void toQuestionCopiesBodyAndAuthorAndLeavesServerFieldsEmpty() {
        QuestionRequest body = new QuestionRequest("How?", List.of("java", "spring"));

        Question question = mapper.toQuestion(body, "author-1");

        assertThat(question.authorId()).isEqualTo("author-1");
        assertThat(question.content()).isEqualTo("How?");
        assertThat(question.tags()).containsExactly("java", "spring");
        assertThat(question.id()).isNull();
        assertThat(question.createdAt()).isNull();
        assertThat(question.updatedAt()).isNull();
        assertThat(question.answers()).isEmpty();
        assertThat(question.votes()).isSameAs(Votes.NONE);
    }

    @Test
    void toQuestionWithoutTagsGivesEmptyTags() {
        Question question = mapper.toQuestion(new QuestionRequest("How?", null), "author-1");

        assertThat(question.tags()).isEmpty();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("updatedAtValues")
    void toResponseCopiesEveryField(String name, Instant updatedAt) {
        Question question =
                new Question(UUID.randomUUID(), "author-1", "How?", List.of("java"), CREATED_AT, updatedAt, null, null);

        QuestionResponse response = mapper.toResponse(question);

        assertThat(response.id()).isEqualTo(question.id());
        assertThat(response.authorId()).isEqualTo(question.authorId());
        assertThat(response.content()).isEqualTo(question.content());
        assertThat(response.tags()).isEqualTo(question.tags());
        assertThat(response.createdAt()).isEqualTo(question.createdAt());
        assertThat(response.updatedAt()).isEqualTo(updatedAt);
        assertThat(response.upvotes()).isZero();
        assertThat(response.downvotes()).isZero();
        assertThat(response.answers()).isEmpty();
    }

    static Stream<Arguments> updatedAtValues() {
        return Stream.of(
                arguments("never updated", null),
                arguments("updated", UPDATED_AT));
    }

    @Test
    void toResponseMapsAnswersInOrder() {
        Answer first = new Answer(UUID.randomUUID(), "user-7", "First", CREATED_AT, null, null);
        Answer second = new Answer(UUID.randomUUID(), "user-8", "Second", UPDATED_AT, null, null);
        Question question = new Question(
                UUID.randomUUID(), "author-1", "How?", List.of(), CREATED_AT, null, List.of(first, second), null);

        QuestionResponse response = mapper.toResponse(question);

        assertThat(response.answers()).containsExactly(
                new AnswerResponse(first.id(), "user-7", "First", CREATED_AT, null, 0, 0),
                new AnswerResponse(second.id(), "user-8", "Second", UPDATED_AT, null, 0, 0));
    }

    // Each target shows its own counts, in the stored order, and every count differs, so a swap fails. The third
    // answer has no votes, so it shows 0 and 0.
    @Test
    void toResponseCountsTheQuestionsAndEachAnswersVotes() {
        Answer first = new Answer(UUID.randomUUID(), "user-7", "First", CREATED_AT, null, votes(3, 4));
        Answer second = new Answer(UUID.randomUUID(), "user-8", "Second", UPDATED_AT, null, votes(1, 2));
        Answer third = new Answer(UUID.randomUUID(), "user-9", "Third", UPDATED_AT, null, null);
        Question question = new Question(UUID.randomUUID(), "author-1", "How?", List.of(), CREATED_AT, null,
                List.of(first, second, third), votes(5, 6));

        QuestionResponse response = mapper.toResponse(question);

        assertThat(response.upvotes()).isEqualTo(5);
        assertThat(response.downvotes()).isEqualTo(6);
        assertThat(response.answers())
                .extracting(AnswerResponse::id, AnswerResponse::upvotes, AnswerResponse::downvotes)
                .containsExactly(tuple(first.id(), 3, 4), tuple(second.id(), 1, 2), tuple(third.id(), 0, 0));
    }

    // The counts differ, so a swap fails. answerCount is the number of answers; the answers themselves aren't mapped.
    @ParameterizedTest(name = "{0}")
    @MethodSource("answerLists")
    void toSummaryCopiesFieldsAndCountsVotesAndAnswers(String name, List<Answer> answers, int answerCount) {
        Question question = new Question(UUID.randomUUID(), "author-1", "How?", List.of("java", "spring"), CREATED_AT,
                UPDATED_AT, answers, votes(5, 6));

        QuestionSummaryResponse summary = mapper.toSummary(question);

        assertThat(summary).isEqualTo(new QuestionSummaryResponse(question.id(), "author-1", "How?",
                List.of("java", "spring"), CREATED_AT, UPDATED_AT, 5, 6, answerCount));
    }

    static Stream<Arguments> answerLists() {
        return Stream.of(
                arguments("no answers", null, 0),
                arguments("two answers", List.of(
                        new Answer(UUID.randomUUID(), "user-7", "First", CREATED_AT, null, null),
                        new Answer(UUID.randomUUID(), "user-8", "Second", UPDATED_AT, null, null)), 2));
    }

    // The third question has no votes, so it shows 0 and 0.
    @ParameterizedTest(name = "{0}")
    @MethodSource("nextCursors")
    void toPageResponseKeepsOrderAndEachItemsCountsAndCopiesNextCursor(String name, UUID nextCursor) {
        Question first = new Question(UUID.randomUUID(), "author-1", "First?", List.of(), CREATED_AT, null, null,
                votes(3, 4));
        Question second = new Question(UUID.randomUUID(), "author-2", "Second?", List.of(), CREATED_AT, null, null,
                votes(1, 2));
        Question third = new Question(UUID.randomUUID(), "author-3", "Third?", List.of(), CREATED_AT, null, null, null);

        QuestionPageResponse response =
                mapper.toPageResponse(new QuestionPage(List.of(first, second, third), nextCursor));

        assertThat(response.items())
                .extracting(QuestionSummaryResponse::id, QuestionSummaryResponse::upvotes,
                        QuestionSummaryResponse::downvotes)
                .containsExactly(tuple(first.id(), 3, 4), tuple(second.id(), 1, 2), tuple(third.id(), 0, 0));
        assertThat(response.nextCursor()).isEqualTo(nextCursor);
    }

    static Stream<Arguments> nextCursors() {
        return Stream.of(
                arguments("last page", null),
                arguments("more follow", UUID.fromString("3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11")));
    }

    @Test
    void toAnswerCopiesBodyAndAuthorAndLeavesServerFieldsNull() {
        Answer answer = mapper.toAnswer(new AnswerRequest("Use compute()."), "user-7");

        assertThat(answer.authorId()).isEqualTo("user-7");
        assertThat(answer.content()).isEqualTo("Use compute().");
        assertThat(answer.id()).isNull();
        assertThat(answer.createdAt()).isNull();
        assertThat(answer.updatedAt()).isNull();
        assertThat(answer.votes()).isSameAs(Votes.NONE);
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("updatedAtValues")
    void toAnswerResponseCopiesEveryField(String name, Instant updatedAt) {
        Answer answer = new Answer(UUID.randomUUID(), "user-7", "Use compute().", CREATED_AT, updatedAt, null);

        AnswerResponse response = mapper.toResponse(answer);

        assertThat(response).isEqualTo(
                new AnswerResponse(answer.id(), "user-7", "Use compute().", CREATED_AT, updatedAt, 0, 0));
    }

    @Test
    void toAnswerResponseCountsItsVotes() {
        Answer answer = new Answer(UUID.randomUUID(), "user-7", "Use compute().", CREATED_AT, null, votes(4, 9));

        AnswerResponse response = mapper.toResponse(answer);

        assertThat(response.upvotes()).isEqualTo(4);
        assertThat(response.downvotes()).isEqualTo(9);
    }

    // up distinct upvoters and down distinct downvoters.
    private static Votes votes(int up, int down) {
        return new Votes(voters("up-", up), voters("down-", down));
    }

    private static Set<String> voters(String prefix, int count) {
        return IntStream.range(0, count).mapToObj(i -> prefix + i).collect(Collectors.toSet());
    }
}
