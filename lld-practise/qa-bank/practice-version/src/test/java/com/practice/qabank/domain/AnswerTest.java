package com.practice.qabank.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;

class AnswerTest {

    private static final UUID ID = UUID.fromString("9b2e4d71-0c3a-4f5e-8b6d-1a7c2e9f4b30");
    private static final Instant CREATED_AT = Instant.parse("2026-10-24T06:20:02.481Z");
    private static final Instant NOW = Instant.parse("2026-10-24T06:31:10.204Z");
    private static final String CONTENT = "Use compute() or merge().";
    private static final Votes VOTES = new Votes(Set.of("user-3"), Set.of("user-4"));

    @Test
    void withIdAndCreatedAtSetsServerFieldsOnly() {
        Answer draft = new Answer(null, "user-7", CONTENT, null, null, null);

        Answer answer = draft.withIdAndCreatedAt(ID, CREATED_AT);

        assertThat(answer.id()).isEqualTo(ID);
        assertThat(answer.createdAt()).isEqualTo(CREATED_AT);
        assertThat(answer.authorId()).isEqualTo("user-7");
        assertThat(answer.content()).isEqualTo(CONTENT);
        assertThat(answer.updatedAt()).isNull();
        assertThat(answer.votes()).isSameAs(Votes.NONE);
        assertThat(draft.id()).isNull();
        assertThat(draft.createdAt()).isNull();
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("realEdits")
    void withEditReturnsEditedCopy(String name, String content) {
        Answer original = new Answer(ID, "user-7", CONTENT, CREATED_AT, null, VOTES);

        Answer edited = original.withEdit(content, NOW);

        assertThat(edited).isNotSameAs(original);
        assertThat(edited.content()).isEqualTo(content);
        assertThat(edited.updatedAt()).isEqualTo(NOW);
        assertThat(edited.id()).isEqualTo(ID);
        assertThat(edited.authorId()).isEqualTo("user-7");
        assertThat(edited.createdAt()).isEqualTo(CREATED_AT);
        assertThat(edited.votes()).isSameAs(VOTES);
        assertThat(original.content()).isEqualTo(CONTENT);
        assertThat(original.updatedAt()).isNull();
    }

    static Stream<Arguments> realEdits() {
        return Stream.of(
                arguments("new content", "Use compute(), merge() or putIfAbsent()."),
                arguments("trailing space added (not trimmed)", CONTENT + " "));
    }

    @Test
    void withEditReturnsSameInstanceForSameContent() {
        Answer original = new Answer(ID, "user-7", CONTENT, CREATED_AT, null, null);

        assertThat(original.withEdit(CONTENT, NOW)).isSameAs(original);
    }

    // A vote isn't an edit: updatedAt stays null.
    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void withVoteAddsTheVoterAndKeepsEverythingElse(Vote vote) {
        Answer original = new Answer(ID, "user-7", CONTENT, CREATED_AT, null, VOTES);

        Answer voted = original.withVote("user-8", vote);

        assertThat(voted).isEqualTo(new Answer(ID, "user-7", CONTENT, CREATED_AT, null, VOTES.with("user-8", vote)));
        assertThat(original.votes()).isSameAs(VOTES);
    }
}
