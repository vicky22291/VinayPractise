package com.practice.qabank.functional.journey;

// How many times each API is called within a story (UserJourneys.md, Profiles). The thread takes N answers, V voters,
// k answer votes per voter, S siblings each side of Q and list limit L. The busy day takes the mix multiplier m, R
// rounds and P users, and its warm-up asks 3m questions with 2 answers each.
enum Profile {
    SMALL(3, 5, 2, 2, 2, 1, 4, 12),
    MEDIUM(12, 40, 4, 4, 3, 2, 8, 24),
    LARGE(40, 100, 6, 8, 5, 4, 15, 48);

    private final int answers;
    private final int voters;
    private final int answerVotes;
    private final int siblings;
    private final int limit;
    private final int scale;
    private final int rounds;
    private final int users;

    Profile(int answers, int voters, int answerVotes, int siblings, int limit, int scale, int rounds, int users) {
        this.answers = answers;
        this.voters = voters;
        this.answerVotes = answerVotes;
        this.siblings = siblings;
        this.limit = limit;
        this.scale = scale;
        this.rounds = rounds;
        this.users = users;
    }

    // N
    int answers() {
        return answers;
    }

    // V
    int voters() {
        return voters;
    }

    // k
    int answerVotes() {
        return answerVotes;
    }

    // S
    int siblings() {
        return siblings;
    }

    // L
    int limit() {
        return limit;
    }

    // m: every Mix count is multiplied by it.
    int scale() {
        return scale;
    }

    // R
    int rounds() {
        return rounds;
    }

    // P
    int users() {
        return users;
    }
}
