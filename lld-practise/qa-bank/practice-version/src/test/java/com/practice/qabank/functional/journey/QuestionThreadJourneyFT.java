package com.practice.qabank.functional.journey;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;

import com.practice.qabank.functional.ApiClient;
import com.practice.qabank.functional.ApiResponse;

// The question thread journey (UserJourneys.md) against a running app (see qabank.baseUrl). Q is asked between
// siblings, answered and voted on by many users, then its author revises and retags it. Each checkpoint compares GET
// question, every GET answer and the tag lists with the ledger, so every view agrees exactly on every target, and the
// retag moves Q between tag lists without moving its place in T. Calls are sequential, so every check is exact. Fresh
// users and tags at each Profile's scale.
@Tag("journey")
class QuestionThreadJourneyFT {

    // Answerers 0 to 2 edit their answers in step 5.
    private static final int ANSWER_EDITS = 3;

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @EnumSource(Profile.class)
    @Timeout(60)
    void threadGrowsThenIsRevised(Profile profile) {
        String t = TestUser.freshTag();
        String u = TestUser.freshTag();
        String w = TestUser.freshTag();
        int n = profile.answers();
        int k = profile.answerVotes();
        Ledger ledger = new Ledger();
        TestUser asker = TestUser.fresh(api);

        // 1. S siblings [T], then Q [T, U], then S more siblings [T], so Q sits at index S of the T list.
        Map<String, Object> asked = null;
        for (int i = 0; i < 2 * profile.siblings() + 1; i++) {
            Map<String, Object> created = i == profile.siblings()
                    ? accepted(asker.ask(content("Thread question"), t, u), 201)
                    : accepted(TestUser.fresh(api).ask(content("Sibling question"), t), 201);
            ledger.recordQuestion(created);
            if (i == profile.siblings()) {
                asked = created;
            }
        }
        String questionId = (String) asked.get("id");

        // 2. N answerers, one at a time.
        List<TestUser> answerers = new ArrayList<>();
        List<String> answerIds = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            TestUser answerer = TestUser.fresh(api);
            Map<String, Object> added = accepted(answerer.answer(questionId, content("Answer")), 201);
            ledger.recordAnswer(questionId, added, 0);
            answerers.add(answerer);
            answerIds.add((String) added.get("id"));
        }

        // 3. Voter i votes on Q and on answers i to i+k-1, the asker on answers 0 to k-1, and answerer i on answer i+1.
        int votes = 0;
        for (int i = 0; i < profile.voters(); i++) {
            TestUser voter = TestUser.fresh(api);
            vote(ledger, voter, questionId, null, votes++);
            for (int j = i; j < i + k; j++) {
                vote(ledger, voter, questionId, answerIds.get(j % n), votes++);
            }
        }
        for (int j = 0; j < k; j++) {
            vote(ledger, asker, questionId, answerIds.get(j), votes++);
        }
        for (int i = 0; i < n; i++) {
            vote(ledger, answerers.get(i), questionId, answerIds.get((i + 1) % n), votes++);
        }

        // 4. Checkpoint 1: U holds Q alone.
        Checkpoint first = checkpoint(profile, ledger, asker, questionId, answerIds, t);
        assertThat(ledger.expectedList(u)).extracting(item -> item.get("id")).containsExactly(questionId);
        assertThat(onlyPage(asker, u, profile)).as("tag=U").isEqualTo(page(ledger.expectedList(u)));

        // 5. The asker swaps U for W, then answerers 0 to 2 edit. Every body keeps the counts and Q keeps its answers.
        Map<String, Object> revised = accepted(asker.editQuestion(questionId, content("Revised question"), t, w), 200);
        ledger.recordEdit(revised);
        assertThat(revised).as("PUT question").isEqualTo(ledger.expectedQuestion(questionId));
        for (int i = 0; i < ANSWER_EDITS; i++) {
            String answerId = answerIds.get(i);
            Map<String, Object> edited =
                    accepted(answerers.get(i).editAnswer(questionId, answerId, content("Revised answer")), 200);
            ledger.recordEdit(edited);
            assertThat(edited).as("PUT answer %d", i).isEqualTo(ledger.expectedAnswer(answerId));
        }

        // 6. Checkpoint 2: nothing counted moved, Q kept its place in T and its createdAt, and only Q's own PUT moved
        // its updatedAt. Q left U and is alone in W.
        Checkpoint second = checkpoint(profile, ledger, asker, questionId, answerIds, t);
        assertThat(second.counts()).as("counts at checkpoint 2").isEqualTo(first.counts());
        assertThat(second.question().get("createdAt")).isEqualTo(asked.get("createdAt"));
        assertThat(second.question().get("updatedAt")).isNotNull().isEqualTo(revised.get("updatedAt"));
        assertThat(onlyPage(asker, u, profile)).as("tag=U").isEqualTo(page(List.of()));
        assertThat(ledger.expectedList(w)).extracting(item -> item.get("id")).containsExactly(questionId);
        assertThat(onlyPage(asker, w, profile)).as("tag=W").isEqualTo(page(ledger.expectedList(w)));
    }

    // Every 4th vote is a downvote. Calls are sequential, so the body's count is exactly the ledger's once the vote is
    // recorded.
    private static void vote(Ledger ledger, TestUser voter, String questionId, String answerId, int index) {
        Direction direction = index % 4 == 3 ? Direction.DOWN : Direction.UP;
        Map<String, Object> body = accepted(voter.vote(direction, questionId, answerId), 201);
        String target = answerId == null ? questionId : answerId;
        ledger.recordVote(target, voter.id(), direction);
        assertThat(body).as("vote %d, %s on %s", index, direction, target)
                .isEqualTo(Map.of(direction.countField(), ledger.count(target, direction)));
    }

    // GET Q, GET each answer, and walk tag=T with limit L, each against the ledger. Q is at index S of T.
    @SuppressWarnings("unchecked")
    private static Checkpoint checkpoint(Profile profile, Ledger ledger, TestUser reader, String questionId,
            List<String> answerIds, String t) {
        Map<String, Object> question = accepted(reader.getQuestion(questionId), 200);
        assertThat(question).as("GET question").isEqualTo(ledger.expectedQuestion(questionId));
        List<Map<String, Object>> entries = (List<Map<String, Object>>) question.get("answers");
        for (int i = 0; i < answerIds.size(); i++) {
            String answerId = answerIds.get(i);
            Map<String, Object> answer = accepted(reader.getAnswer(questionId, answerId), 200);
            assertThat(answer).as("GET answer %d", i).isEqualTo(entries.get(i))
                    .isEqualTo(ledger.expectedAnswer(answerId));
        }
        List<Map<String, Object>> items = TestUser.items(reader.walk(t, profile.limit()), profile.limit());
        assertThat(items).as("tag=T").isEqualTo(ledger.expectedList(t));
        assertThat(items).extracting(item -> item.get("id")).element(profile.siblings()).isEqualTo(questionId);
        return new Checkpoint(question, items);
    }

    // A list that must fit on one page, as that page's body.
    private static Object onlyPage(TestUser reader, String tag, Profile profile) {
        List<ApiResponse> pages = reader.walk(tag, profile.limit());
        assertThat(pages).as("tag=%s", tag).hasSize(1);
        assertThat(pages.get(0).status()).as(pages.get(0).body()).isEqualTo(200);
        return pages.get(0).json("$");
    }

    private static Map<String, Object> page(List<Map<String, Object>> items) {
        Map<String, Object> page = new HashMap<>();
        page.put("items", items);
        page.put("nextCursor", null);
        return page;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> accepted(ApiResponse response, int status) {
        assertThat(response.status()).as(response.body()).isEqualTo(status);
        return (Map<String, Object>) response.json("$");
    }

    private static String content(String prefix) {
        return prefix + " " + UUID.randomUUID();
    }

    // What a checkpoint read: GET Q's body and the T list's items.
    private record Checkpoint(Map<String, Object> question, List<Map<String, Object>> items) {

        // Every count by id: Q's and each answer's from GET Q, and each T item's with its answerCount.
        @SuppressWarnings("unchecked")
        Map<String, List<Object>> counts() {
            Map<String, List<Object>> counts = new LinkedHashMap<>();
            List<Map<String, Object>> targets = new ArrayList<>(List.of(question));
            targets.addAll((List<Map<String, Object>>) question.get("answers"));
            for (Map<String, Object> target : targets) {
                counts.put("GET " + target.get("id"), List.of(target.get("upvotes"), target.get("downvotes")));
            }
            for (Map<String, Object> item : items) {
                counts.put("list " + item.get("id"),
                        List.of(item.get("upvotes"), item.get("downvotes"), item.get("answerCount")));
            }
            return counts;
        }
    }
}
