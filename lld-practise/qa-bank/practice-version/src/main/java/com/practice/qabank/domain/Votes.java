package com.practice.qabank.domain;

import java.util.HashSet;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

// Who voted on one question or answer, a set per direction. Question and Answer each hold one, so the never-both rule
// lives only here. Immutable, like its holder: with returns a copy. Counts are the set sizes, so they can't drift.
public record Votes(Set<String> upvoterIds, Set<String> downvoterIds) {

    public static final Votes NONE = new Votes(Set.of(), Set.of());

    // Checked here, so no Votes, whoever builds it, has a voter in both sets.
    public Votes {
        upvoterIds = upvoterIds == null ? Set.of() : Set.copyOf(upvoterIds);
        downvoterIds = downvoterIds == null ? Set.of() : Set.copyOf(downvoterIds);
        for (String voterId : upvoterIds) {
            if (downvoterIds.contains(voterId)) {
                throw new IllegalArgumentException("Voter " + voterId + " is in both sets");
            }
        }
    }

    // Exact, case-sensitive match on the voter, like the ownership checks.
    public Optional<Vote> heldBy(String voterId) {
        Objects.requireNonNull(voterId, "voterId");
        if (upvoterIds.contains(voterId)) {
            return Optional.of(Vote.UP);
        }
        if (downvoterIds.contains(voterId)) {
            return Optional.of(Vote.DOWN);
        }
        return Optional.empty();
    }

    public int count(Vote vote) {
        return switch (vote) {
            case UP -> upvoterIds.size();
            case DOWN -> downvoterIds.size();
        };
    }

    // Callers check heldBy first and turn a held vote into a 409, so a voter who already holds one is a bug here.
    public Votes with(String voterId, Vote vote) {
        heldBy(voterId).ifPresent(held -> {
            throw new IllegalStateException("Voter " + voterId + " already holds " + held);
        });
        return switch (vote) {
            case UP -> new Votes(plus(upvoterIds, voterId), downvoterIds);
            case DOWN -> new Votes(upvoterIds, plus(downvoterIds, voterId));
        };
    }

    private static Set<String> plus(Set<String> voterIds, String voterId) {
        Set<String> grown = new HashSet<>(voterIds);
        grown.add(voterId);
        return grown;
    }
}
