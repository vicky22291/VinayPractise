package com.practice.qabank.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;

class QuestionTest {

    private static final UUID ID = UUID.fromString("3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11");
    private static final Instant CREATED_AT = Instant.parse("2026-10-24T06:12:45.123Z");
    private static final Instant UPDATED_AT = Instant.parse("2026-10-24T06:15:00Z");
    private static final Instant NOW = Instant.parse("2026-10-24T06:20:03.456Z");
    private static final String CONTENT = "How do I make it atomic?";
    private static final List<String> TAGS = List.of("java", "concurrency");
    private static final Votes VOTES = new Votes(Set.of("user-3", "user-4"), Set.of("user-5"));

    @ParameterizedTest(name = "{0}")
    @MethodSource("tagNormalization")
    void normalizesTags(String name, List<String> tags, List<String> expected) {
        Question question = draft(tags);

        assertThat(question.tags()).containsExactlyElementsOf(expected);
    }

    static Stream<Arguments> tagNormalization() {
        return Stream.of(
                arguments("null becomes empty", null, List.of()),
                arguments("empty stays empty", List.of(), List.of()),
                arguments("lowercased", List.of("Java", "SPRING"), List.of("java", "spring")),
                arguments("deduplicated after lowercasing", List.of("Java", "java", "JAVA"), List.of("java")),
                arguments("first-seen order kept", List.of("b", "A", "c", "a", "B"), List.of("b", "a", "c")),
                arguments("symbols kept", List.of("C#", "c#", "C++", ".NET"), List.of("c#", "c++", ".net")));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("singleTags")
    void normalizeTagLowercasesOneTag(String name, String tag, String expected) {
        assertThat(Question.normalizeTag(tag)).isEqualTo(expected);
    }

    static Stream<Arguments> singleTags() {
        return Stream.of(
                arguments("Java", "Java", "java"),
                arguments("C#", "C#", "c#"),
                arguments(".NET", ".NET", ".net"),
                arguments("c++ unchanged", "c++", "c++"));
    }

    @Test
    void normalizeTagRejectsNull() {
        assertThatThrownBy(() -> Question.normalizeTag(null)).isInstanceOf(NullPointerException.class);
    }

    @Test
    void tagListIsImmutable() {
        Question question = draft(List.of("java"));

        assertThatThrownBy(() -> question.tags().add("spring")).isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void tagListDoesNotChangeWhenCallerListChanges() {
        List<String> tags = new ArrayList<>(Arrays.asList("java", "spring"));
        Question question = draft(tags);

        tags.add("kotlin");
        tags.set(0, "scala");

        assertThat(question.tags()).containsExactly("java", "spring");
    }

    @Test
    void nullAnswersBecomeEmpty() {
        assertThat(draft(TAGS).answers()).isEmpty();
    }

    @Test
    void nullVotesBecomeNone() {
        assertThat(draft(TAGS).votes()).isSameAs(Votes.NONE);
    }

    @Test
    void answerListIsImmutable() {
        Question question = stored(List.of(answer("user-7")));

        assertThatThrownBy(() -> question.answers().add(answer("user-8")))
                .isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void answerListDoesNotChangeWhenCallerListChanges() {
        Answer first = answer("user-7");
        List<Answer> answers = new ArrayList<>(List.of(first));
        Question question = stored(answers);

        answers.add(answer("user-8"));
        answers.set(0, answer("user-9"));

        assertThat(question.answers()).containsExactly(first);
    }

    @Test
    void withIdAndCreatedAtSetsServerFieldsOnly() {
        Question draft = draft(List.of("java"));

        Question question = draft.withIdAndCreatedAt(ID, CREATED_AT);

        assertThat(question.id()).isEqualTo(ID);
        assertThat(question.createdAt()).isEqualTo(CREATED_AT);
        assertThat(question.authorId()).isEqualTo("author-1");
        assertThat(question.content()).isEqualTo(CONTENT);
        assertThat(question.tags()).containsExactly("java");
        assertThat(question.updatedAt()).isNull();
        assertThat(question.answers()).isEmpty();
        assertThat(question.votes()).isSameAs(Votes.NONE);
        assertThat(draft.id()).isNull();
        assertThat(draft.createdAt()).isNull();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("realEdits")
    void withEditReturnsEditedCopy(String name, String content, List<String> tags, List<String> expectedTags) {
        Question original = stored(List.of());

        Question edited = original.withEdit(content, tags, NOW);

        assertThat(edited).isNotSameAs(original);
        assertThat(edited.content()).isEqualTo(content);
        assertThat(edited.tags()).containsExactlyElementsOf(expectedTags);
        assertThat(edited.updatedAt()).isEqualTo(NOW);
        assertThat(edited.id()).isEqualTo(ID);
        assertThat(edited.authorId()).isEqualTo("author-1");
        assertThat(edited.createdAt()).isEqualTo(CREATED_AT);
        assertThat(original.content()).isEqualTo(CONTENT);
        assertThat(original.updatedAt()).isNull();
    }

    static Stream<Arguments> realEdits() {
        return Stream.of(
                arguments("new content", CONTENT + "!", TAGS, TAGS),
                arguments("new tags", CONTENT, List.of("Kotlin", "coroutines"), List.of("kotlin", "coroutines")),
                arguments("reordered tags", CONTENT, List.of("concurrency", "java"), List.of("concurrency", "java")),
                arguments("tags cleared", CONTENT, null, List.of()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("noOpEdits")
    void withEditReturnsSameInstanceWhenNothingChanges(String name, List<String> tags) {
        Question original = stored(List.of());

        assertThat(original.withEdit(CONTENT, tags, NOW)).isSameAs(original);
    }

    static Stream<Arguments> noOpEdits() {
        return Stream.of(
                arguments("same content and tags", TAGS),
                arguments("tags differ only by case", List.of("JAVA", "Concurrency")),
                arguments("tags differ only by duplicates", List.of("java", "Java", "concurrency", "java")));
    }

    @Test
    void withEditKeepsAnswersAndVotes() {
        List<Answer> answers = List.of(answer("user-7"), answer("user-8"));
        Question original = new Question(ID, "author-1", CONTENT, TAGS, CREATED_AT, null, answers, VOTES);

        Question edited = original.withEdit(CONTENT + "!", TAGS, NOW);

        assertThat(edited.answers()).containsExactlyElementsOf(answers);
        assertThat(edited.votes()).isSameAs(VOTES);
    }

    @Test
    void withAnswerAppendsLastAndKeepsEverythingElse() {
        Answer first = answer("user-7");
        Answer second = answer("user-8");
        Question original = new Question(ID, "author-1", CONTENT, TAGS, CREATED_AT, UPDATED_AT, List.of(first), VOTES);

        Question added = original.withAnswer(second);

        assertThat(added.answers()).containsExactly(first, second);
        assertThat(added.id()).isEqualTo(ID);
        assertThat(added.authorId()).isEqualTo("author-1");
        assertThat(added.content()).isEqualTo(CONTENT);
        assertThat(added.tags()).isEqualTo(TAGS);
        assertThat(added.createdAt()).isEqualTo(CREATED_AT);
        assertThat(added.updatedAt()).isEqualTo(UPDATED_AT);
        assertThat(added.votes()).isSameAs(VOTES);
        assertThat(original.answers()).containsExactly(first);
    }

    @Test
    void answerByFindsThatUsersAnswer() {
        Answer mine = answer("user-8");
        Question question = stored(List.of(answer("user-7"), mine));

        assertThat(question.answerBy("user-8")).containsSame(mine);
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("otherAuthors")
    void answerByIsEmptyForOtherAuthors(String name, String authorId) {
        Question question = stored(List.of(answer("user-7")));

        assertThat(question.answerBy(authorId)).isEmpty();
    }

    static Stream<Arguments> otherAuthors() {
        return Stream.of(
                arguments("user who hasn't answered", "user-8"),
                arguments("same id in another case", "USER-7"));
    }

    @Test
    void answerFindsOneOfSeveral() {
        Answer target = answer("user-8");
        Question question = stored(List.of(answer("user-7"), target, answer("user-9")));

        assertThat(question.answer(target.id())).containsSame(target);
    }

    @Test
    void answerWithUnknownIdIsEmpty() {
        Question question = stored(List.of(answer("user-7")));

        assertThat(question.answer(UUID.randomUUID())).isEmpty();
    }

    @Test
    void withAnswerEditReplacesOnlyTheTargetInPlace() {
        Answer first = answer("user-7");
        Answer target = answer("user-8");
        Answer third = answer("user-9");
        Question original = new Question(ID, "author-1", CONTENT, TAGS, CREATED_AT, UPDATED_AT,
                List.of(first, target, third), VOTES);

        Question edited = original.withAnswerEdit(target.id(), "Edited answer", NOW);

        assertThat(edited).isNotSameAs(original);
        assertThat(edited.answers()).hasSize(3);
        assertThat(edited.answers().get(0)).isSameAs(first);
        assertThat(edited.answers().get(2)).isSameAs(third);
        Answer editedAnswer = edited.answers().get(1);
        assertThat(editedAnswer.id()).isEqualTo(target.id());
        assertThat(editedAnswer.content()).isEqualTo("Edited answer");
        assertThat(editedAnswer.updatedAt()).isEqualTo(NOW);
        assertThat(edited.content()).isEqualTo(CONTENT);
        assertThat(edited.tags()).isEqualTo(TAGS);
        assertThat(edited.updatedAt()).isEqualTo(UPDATED_AT);
        assertThat(edited.votes()).isSameAs(VOTES);
        assertThat(original.answers()).containsExactly(first, target, third);
    }

    @Test
    void withAnswerEditReturnsSameInstanceOnNoOp() {
        Answer target = answer("user-8");
        Question original = stored(List.of(answer("user-7"), target));

        assertThat(original.withAnswerEdit(target.id(), target.content(), NOW)).isSameAs(original);
    }

    @Test
    void withAnswerEditReturnsSameInstanceForUnknownAnswer() {
        Question original = stored(List.of(answer("user-7")));

        assertThat(original.withAnswerEdit(UUID.randomUUID(), "Edited answer", NOW)).isSameAs(original);
    }

    // A vote changes only the votes: updatedAt stays, as it does for withAnswer.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void withVoteAddsTheVoterAndKeepsEverythingElse(Vote vote) {
        List<Answer> answers = List.of(answer("user-7"));
        Question original = new Question(ID, "author-1", CONTENT, TAGS, CREATED_AT, UPDATED_AT, answers, VOTES);

        Question voted = original.withVote("user-8", vote);

        assertThat(voted.votes()).isEqualTo(VOTES.with("user-8", vote));
        assertThat(voted).usingRecursiveComparison().ignoringFields("votes").isEqualTo(original);
        assertThat(voted.answers()).containsExactlyElementsOf(answers);
        assertThat(original.votes()).isSameAs(VOTES);
    }

    // Neither updatedAt moves, and the question's own votes stay.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void withAnswerVoteVotesOnlyTheTargetInPlace(Vote vote) {
        Answer first = answer("user-7");
        Answer target = answer("user-8");
        Answer third = answer("user-9");
        Question original = new Question(ID, "author-1", CONTENT, TAGS, CREATED_AT, UPDATED_AT,
                List.of(first, target, third), VOTES);

        Question voted = original.withAnswerVote(target.id(), "user-10", vote);

        assertThat(voted.answers()).hasSize(3);
        assertThat(voted.answers().get(0)).isSameAs(first);
        assertThat(voted.answers().get(2)).isSameAs(third);
        assertThat(voted.answers().get(1)).isEqualTo(target.withVote("user-10", vote));
        assertThat(voted).usingRecursiveComparison().ignoringFields("answers").isEqualTo(original);
        assertThat(original.answers()).containsExactly(first, target, third);
    }

    @Test
    void withAnswerVoteReturnsSameInstanceForUnknownAnswer() {
        Question original = stored(List.of(answer("user-7")));

        assertThat(original.withAnswerVote(UUID.randomUUID(), "user-8", Vote.UP)).isSameAs(original);
    }

    private static Question draft(List<String> tags) {
        return new Question(null, "author-1", CONTENT, tags, null, null, null, null);
    }

    private static Question stored(List<Answer> answers) {
        return new Question(ID, "author-1", CONTENT, TAGS, CREATED_AT, null, answers, null);
    }

    private static Answer answer(String authorId) {
        return new Answer(UUID.randomUUID(), authorId, "Answer by " + authorId, CREATED_AT, null, null);
    }
}
