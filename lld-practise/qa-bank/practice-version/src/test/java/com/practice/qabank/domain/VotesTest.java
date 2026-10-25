package com.practice.qabank.domain;

import static com.practice.qabank.domain.Vote.DOWN;
import static com.practice.qabank.domain.Vote.UP;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;

class VotesTest {

    // user-7 and user-8 upvoted, user-9 downvoted.
    private static final Votes VOTES = new Votes(Set.of("user-7", "user-8"), Set.of("user-9"));

    @Test
    void nullSetsBecomeEmpty() {
        assertThat(new Votes(null, null)).isEqualTo(Votes.NONE);
        assertThat(Votes.NONE.count(UP)).isZero();
        assertThat(Votes.NONE.count(DOWN)).isZero();
    }

    @Test
    void setsAreImmutableCopies() {
        Set<String> upvoterIds = new HashSet<>(Set.of("user-7"));
        Votes votes = new Votes(upvoterIds, Set.of());

        upvoterIds.add("user-8");

        assertThat(votes.upvoterIds()).containsExactly("user-7");
        assertThatThrownBy(() -> votes.upvoterIds().add("user-9")).isInstanceOf(UnsupportedOperationException.class);
        assertThatThrownBy(() -> votes.downvoterIds().add("user-9")).isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void voterInBothSetsIsRejected() {
        assertThatThrownBy(() -> new Votes(Set.of("user-7", "user-8"), Set.of("user-8")))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Voter user-8 is in both sets");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("voters")
    void heldByNamesTheVotersSet(String voterId, Optional<Vote> held) {
        assertThat(VOTES.heldBy(voterId)).isEqualTo(held);
    }

    static Stream<Arguments> voters() {
        return Stream.of(
                arguments("user-7", Optional.of(UP)),
                arguments("user-9", Optional.of(DOWN)),
                arguments("user-10", Optional.empty()),
                arguments("USER-7", Optional.empty()));
    }

    @Test
    void countIsTheSizeOfEachSet() {
        assertThat(VOTES.count(UP)).isEqualTo(2);
        assertThat(VOTES.count(DOWN)).isEqualTo(1);
    }

    @ParameterizedTest(name = "{0}")
    @EnumSource(Vote.class)
    void withAddsTheVoterToThatSetOnly(Vote vote) {
        Votes voted = VOTES.with("user-10", vote);

        assertThat(voted.heldBy("user-10")).contains(vote);
        assertThat(voted.count(vote)).isEqualTo(VOTES.count(vote) + 1);
        assertThat(voted.count(opposite(vote))).isEqualTo(VOTES.count(opposite(vote)));
        assertThat(VOTES.heldBy("user-10")).isEmpty();
    }

    // Either direction: a held vote is never added to or switched.
    @ParameterizedTest(name = "holds {0}, tries {1}")
    @MethodSource("heldAndTried")
    void withThrowsWhenTheVoterAlreadyHoldsAVote(Vote held, Vote tried) {
        Votes votes = Votes.NONE.with("user-7", held);

        assertThatThrownBy(() -> votes.with("user-7", tried))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("Voter user-7 already holds " + held);
    }

    static Stream<Arguments> heldAndTried() {
        return Stream.of(Vote.values())
                .flatMap(held -> Stream.of(Vote.values()).map(tried -> arguments(held, tried)));
    }

    private static Vote opposite(Vote vote) {
        return vote == UP ? DOWN : UP;
    }
}
