package com.practice.qabank.functional.journey;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.practice.qabank.functional.journey.TestUser.Sent;

// The expected model: what the server should hold. It's built only from 2xx response bodies, never from what a test
// meant to send, and never from replays. Questions and answers are kept in the order they were recorded, with the
// latest body of each and each answer's round. Counts come from the recorded votes, one per voter per target, so they
// can't drift from them. The expected* methods merge the latest bodies with those counts and answers. Used from the
// test thread only.
final class Ledger {

    // The list order, as the server compares it: createdAt as an Instant, then id as a UUID, both descending.
    static final Comparator<Map<String, Object>> NEWEST_FIRST = Comparator
            .comparing((Map<String, Object> question) -> Instant.parse((String) question.get("createdAt")))
            .thenComparing(question -> UUID.fromString((String) question.get("id")))
            .reversed();

    // Question id to its latest body, without counts and answers.
    private final Map<String, Map<String, Object>> questions = new LinkedHashMap<>();
    // Answer id to its latest body, without counts. Insertion order across every question.
    private final Map<String, Map<String, Object>> answers = new LinkedHashMap<>();
    private final Map<String, List<String>> answersOf = new HashMap<>();
    private final Map<String, String> questionOf = new HashMap<>();
    private final Map<String, Integer> roundOf = new HashMap<>();
    // Target id to each voter's vote, in the order they were recorded.
    private final Map<String, Map<String, Direction>> votes = new HashMap<>();
    // Accepted writes that a busy day may retry, in the order they were recorded.
    private final List<Sent> writes = new ArrayList<>();

    // A create body.
    void recordQuestion(Map<String, Object> body) {
        String id = (String) body.get("id");
        questions.put(id, own(body));
        answersOf.put(id, new ArrayList<>());
    }

    // An add body, appended to its question's answers. round is when it was added: CONCURRENT only orders by round.
    void recordAnswer(String questionId, Map<String, Object> body, int round) {
        String id = (String) body.get("id");
        answers.put(id, own(body));
        answersOf.get(questionId).add(id);
        questionOf.put(id, questionId);
        roundOf.put(id, round);
    }

    // Throws on a second accepted vote by one voter on one target: the server must have rejected one of them.
    void recordVote(String targetId, String voterId, Direction direction) {
        Direction held = votes.computeIfAbsent(targetId, id -> new LinkedHashMap<>()).putIfAbsent(voterId, direction);
        if (held != null) {
            throw new IllegalStateException("The server accepted a " + direction + " vote by " + voterId + " on "
                    + targetId + ", who already holds a " + held + " vote there");
        }
    }

    // A PUT question or PUT answer body. Only the target's own fields are taken: its counts and answers stay the
    // ledger's, since a PUT question body's answers may predate answers added or edited at the same time.
    void recordEdit(Map<String, Object> body) {
        String id = (String) body.get("id");
        if (questions.containsKey(id)) {
            questions.put(id, own(body));
        } else if (answers.containsKey(id)) {
            answers.put(id, own(body));
        } else {
            throw new IllegalStateException("Edit of " + id + ", which the ledger doesn't hold");
        }
    }

    // A write the server accepted, so a busy day can retry it later. Replays and double-clicks are never recorded.
    void recordWrite(Sent sent) {
        writes.add(sent);
    }

    int count(String targetId, Direction direction) {
        return (int) votes.getOrDefault(targetId, Map.of()).values().stream()
                .filter(held -> held == direction)
                .count();
    }

    // As GET question should show it: the latest body, the ledger's counts, and its answers in recorded order.
    Map<String, Object> expectedQuestion(String questionId) {
        Map<String, Object> expected = withCounts(questions.get(questionId), questionId);
        expected.put("answers", answersOf.get(questionId).stream().map(this::expectedAnswer).toList());
        return expected;
    }

    Map<String, Object> expectedAnswer(String answerId) {
        return withCounts(answers.get(answerId), answerId);
    }

    // Every question that holds tag now, as list items, newest first.
    List<Map<String, Object>> expectedList(String tag) {
        return questions.keySet().stream()
                .filter(id -> tagsOf(id).contains(tag))
                .map(this::summary)
                .sorted(NEWEST_FIRST)
                .toList();
    }

    // What's wrong with ids as a question's answers, if anything: they must be the ledger's answers, each once, with
    // earlier rounds first. Within a round any order is fine, since CONCURRENT adds land in apply order.
    List<String> checkAnswerOrder(String questionId, List<String> ids) {
        List<String> expected = answersOf.get(questionId);
        List<String> violations = new ArrayList<>();
        if (ids.size() != expected.size() || !new HashSet<>(ids).equals(new HashSet<>(expected))) {
            violations.add("question " + questionId + " has answers " + ids + ", expected " + expected
                    + " in any order within a round");
            return violations;
        }
        for (int i = 1; i < ids.size(); i++) {
            int before = roundOf.get(ids.get(i - 1));
            int after = roundOf.get(ids.get(i));
            if (before > after) {
                violations.add("answer " + ids.get(i - 1) + " of round " + before + " comes before answer "
                        + ids.get(i) + " of round " + after);
            }
        }
        return violations;
    }

    // The rest is what MixPlanner reads to pick by position, and what the busy day walks and reads back.

    List<String> questionIds() {
        return List.copyOf(questions.keySet());
    }

    List<String> answerIds() {
        return List.copyOf(answers.keySet());
    }

    String questionOf(String answerId) {
        return questionOf.get(answerId);
    }

    String authorOf(String targetId) {
        Map<String, Object> body = questions.containsKey(targetId) ? questions.get(targetId) : answers.get(targetId);
        return (String) body.get("authorId");
    }

    @SuppressWarnings("unchecked")
    List<String> tagsOf(String questionId) {
        return (List<String>) questions.get(questionId).get("tags");
    }

    boolean hasAnswered(String questionId, String userId) {
        return answersOf.get(questionId).stream().anyMatch(id -> userId.equals(authorOf(id)));
    }

    // The vote userId holds on targetId, or null.
    Direction voteOf(String targetId, String userId) {
        return votes.getOrDefault(targetId, Map.of()).get(userId);
    }

    List<Sent> writes() {
        return List.copyOf(writes);
    }

    private Map<String, Object> summary(String questionId) {
        Map<String, Object> summary = withCounts(questions.get(questionId), questionId);
        summary.put("answerCount", answersOf.get(questionId).size());
        return summary;
    }

    private Map<String, Object> withCounts(Map<String, Object> body, String targetId) {
        Map<String, Object> copy = new LinkedHashMap<>(body);
        for (Direction direction : Direction.values()) {
            copy.put(direction.countField(), count(targetId, direction));
        }
        return copy;
    }

    // A body without what the ledger derives itself.
    private static Map<String, Object> own(Map<String, Object> body) {
        Map<String, Object> copy = new LinkedHashMap<>(body);
        for (Direction direction : Direction.values()) {
            copy.remove(direction.countField());
        }
        copy.remove("answers");
        return copy;
    }
}
