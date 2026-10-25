package com.practice.qabank.functional;

import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.params.provider.Arguments.arguments;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.Callable;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

// Black-box tests for GET /questions against a running app (see qabank.baseUrl). Every FT class shares that app, so the
// full list holds other tests' questions too: exact assertions run under a tag only that test uses, and assertions on
// the untagged list are relative. The expected order comes from the create responses: createdAt descending, then id
// descending. Test data is created only through the API.
@Tag("api")
class ListQuestionsFT {

    private static final String QUESTIONS = "/questions";
    private static final String REPLAYED = "Idempotent-Replayed";
    private static final int PARALLEL_CREATES = 50;
    private static final int WALKERS = 5;

    private static final String LIMIT_TOO_SMALL = "limit: must be greater than or equal to 1";
    private static final String LIMIT_TOO_LARGE = "limit: must be less than or equal to 100";
    private static final String LIMIT_NOT_INTEGER = "limit must be an integer";
    private static final String TAG_RULE = "tag: must match \"[A-Za-z0-9+#.-]{1,35}\"";

    // pagesWithoutGapsOrDuplicates walks 7 questions: every page is full except the last, and an exactly full last page
    // ends the walk.
    private static final Map<Integer, List<Integer>> PAGE_SIZES = Map.of(
            1, List.of(1, 1, 1, 1, 1, 1, 1),
            3, List.of(3, 3, 1),
            7, List.of(7),
            100, List.of(7));

    private static final Set<String> SUMMARY_FIELDS = Set.of(
            "id", "authorId", "content", "tags", "createdAt", "updatedAt", "upvotes", "downvotes", "answerCount");

    // Compared as the server compares them: createdAt as an Instant, then id as a UUID, both descending.
    private static final Comparator<Map<String, Object>> NEWEST_FIRST = Comparator
            .comparing((Map<String, Object> question) -> Instant.parse((String) question.get("createdAt")))
            .thenComparing(question -> UUID.fromString((String) question.get("id")))
            .reversed();

    private final ApiClient api = new ApiClient();

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidQueries")
    void rejectsInvalidQuery(String name, String query, String message) {
        ApiResponse response = list(query);

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo(message);
    }

    // Sent exactly as written. In a query, + means a space, so tag=c++ arrives as "c  ".
    static Stream<Arguments> invalidQueries() {
        return Stream.of(
                arguments("limit=0", "limit=0", LIMIT_TOO_SMALL),
                arguments("limit=-1", "limit=-1", LIMIT_TOO_SMALL),
                arguments("limit=101", "limit=101", LIMIT_TOO_LARGE),
                arguments("limit=abc", "limit=abc", LIMIT_NOT_INTEGER),
                arguments("limit=1.5", "limit=1.5", LIMIT_NOT_INTEGER),
                arguments("limit=99999999999, above int", "limit=99999999999", LIMIT_NOT_INTEGER),
                arguments("tag= (empty)", "tag=", TAG_RULE),
                arguments("tag=spring%20boot", "tag=spring%20boot", TAG_RULE),
                arguments("tag=c++, where + is a space", "tag=c++", TAG_RULE),
                arguments("tag of 36 chars", "tag=" + "t".repeat(36), TAG_RULE),
                arguments("limit=0&tag=a%20b, both reported", "limit=0&tag=a%20b", LIMIT_TOO_SMALL + "; " + TAG_RULE),
                arguments("after=not-a-uuid&limit=0, conversion first", "after=not-a-uuid&limit=0",
                        "after must be a UUID"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("com.practice.qabank.functional.GetQuestionFT#malformedIds")
    void rejectsMalformedAfter(String name, String id) {
        ApiResponse response = list("after=" + id);

        assertThat(response.status()).as(response.body()).isEqualTo(400);
        assertThat(response.json("$.error")).isEqualTo("VALIDATION_FAILED");
        assertThat(response.json("$.message")).isEqualTo("after must be a UUID");
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("tagForms")
    void matchesTagForm(String name, String stored, String sent) {
        ApiResponse created = create(stored, "java");

        ApiResponse response = list("tag=" + sent);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.items[*].id")).isEqualTo(List.of(id(created)));
        assertThat(response.json("$.items[0].tags")).isEqualTo(List.of(stored.toLowerCase(Locale.ROOT), "java"));
        assertThat(response.json("$.nextCursor")).isNull();
    }

    // A fresh unique tag per row, sent upper-cased. # and + are URL-encoded, as a client must send them.
    static Stream<Arguments> tagForms() {
        String plain = uniqueTag();
        String sharp = uniqueTag();
        String plus = uniqueTag();
        String dot = uniqueTag();
        String longest = uniqueTag();
        longest = longest + "x".repeat(35 - longest.length());
        return Stream.of(
                arguments("upper case", plain, upper(plain)),
                arguments("C# as C%23", sharp + "c#", upper(sharp) + "C%23"),
                arguments("C++ as C%2B%2B", plus + "c++", upper(plus) + "C%2B%2B"),
                arguments(".NET", dot + ".net", upper(dot) + ".NET"),
                arguments("35 chars, the longest tag", longest, upper(longest)));
    }

    @ParameterizedTest(name = "limit {0}")
    @MethodSource("limits")
    void pagesWithoutGapsOrDuplicates(int limit) {
        String tag = uniqueTag();
        List<String> expected = ids(newestFirst(createMany(7, tag)));

        List<List<Map<String, Object>>> pages = pages("tag=" + tag, limit);

        assertThat(itemIds(pages.stream().flatMap(List::stream).toList())).isEqualTo(expected);
        assertThat(pages.stream().map(List::size).toList()).isEqualTo(PAGE_SIZES.get(limit));
    }

    static Stream<Arguments> limits() {
        return Stream.of(arguments(1), arguments(3), arguments(7), arguments(100));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("limitForms")
    void defaultsLimitTo20(String name, String query) {
        String tag = uniqueTag();
        List<String> expected = ids(newestFirst(createMany(21, tag)));
        String base = "tag=" + tag + query;

        ApiResponse first = list(base);
        ApiResponse second = list(base + "&after=" + first.json("$.nextCursor"));

        assertThat(first.status()).as(first.body()).isEqualTo(200);
        assertThat(first.json("$.items[*].id")).isEqualTo(expected.subList(0, 20));
        assertThat(first.json("$.nextCursor")).isEqualTo(expected.get(19));
        assertThat(second.status()).as(second.body()).isEqualTo(200);
        assertThat(second.json("$.items[*].id")).isEqualTo(expected.subList(20, 21));
        assertThat(second.json("$.nextCursor")).isNull();
    }

    static Stream<Arguments> limitForms() {
        return Stream.of(
                arguments("no limit", ""),
                arguments("limit= (empty)", "&limit="));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("com.practice.qabank.functional.GetQuestionFT#userHeaders")
    void ignoresUserHeader(String name, String userId) {
        String tag = uniqueTag();
        ApiResponse created = create(tag);
        Map<String, String> headers = userId == null ? Map.of() : Map.of(USER_ID, userId);

        ApiResponse response = api.get(QUESTIONS + "?tag=" + tag, headers);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.items[*].id")).isEqualTo(List.of(id(created)));
        assertThat(response.json("$")).isEqualTo(list("tag=" + tag).json("$"));
    }

    @Test
    void listsNewestFirst() {
        String tag = uniqueTag();
        List<ApiResponse> created = newestFirst(createMany(3, tag));

        ApiResponse response = list("tag=" + tag);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        List<Map<String, Object>> items = items(response);
        assertThat(itemIds(items)).isEqualTo(ids(created));
        for (int i = 0; i < items.size(); i++) {
            assertThat(items.get(i).keySet()).containsExactlyInAnyOrderElementsOf(SUMMARY_FIELDS);
            assertThat(items.get(i)).isEqualTo(summaryOf(created.get(i)));
            assertThat(items.get(i)).containsEntry("answerCount", 0);
        }
        assertThat(response.json("$.nextCursor")).isNull();
        assertThat(response.header("Location")).isEmpty();
        assertThat(response.header(REPLAYED)).isEmpty();
    }

    @Test
    void emptyForUnknownTag() {
        ApiResponse response = list("tag=" + uniqueTag());

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        Map<String, Object> empty = new HashMap<>();
        empty.put("items", List.of());
        empty.put("nextCursor", null);
        assertThat(response.json("$")).isEqualTo(empty);
    }

    @Test
    void tagMatchesWholeTag() {
        String tag = uniqueTag();
        ApiResponse exact = create(tag);
        create(tag + "x");

        ApiResponse response = list("tag=" + tag);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.items[*].id")).isEqualTo(List.of(id(exact)));
    }

    // Counts are read when the list is built, and answerCount and content come from the stored question.
    @Test
    void itemsCarryLiveCounts() {
        String tag = uniqueTag();
        ApiResponse q1 = create(tag);
        ApiResponse q2 = create(tag);
        answer(q1);
        answer(q1);
        vote(q1, "upvotes");
        vote(q1, "upvotes");
        vote(q1, "downvotes");
        vote(q2, "downvotes");
        String editedContent = edit(q2, tag);

        ApiResponse response = list("tag=" + tag);

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        List<Map<String, Object>> items = items(response);
        assertThat(itemIds(items)).isEqualTo(ids(newestFirst(List.of(q1, q2))));
        Map<String, Map<String, Object>> byId =
                items.stream().collect(Collectors.toMap(ListQuestionsFT::itemId, Function.identity()));
        Map<String, Object> first = byId.get(id(q1));
        Map<String, Object> second = byId.get(id(q2));
        assertThat(second).containsEntry("upvotes", 0).containsEntry("downvotes", 1).containsEntry("answerCount", 0)
                .containsEntry("content", editedContent);
        assertThat(second.get("updatedAt")).isNotNull();
        assertThat(first).containsEntry("upvotes", 2).containsEntry("downvotes", 1).containsEntry("answerCount", 2);
        assertThat(first).isEqualTo(summaryOf(getQuestion(q1)));
        assertThat(second).isEqualTo(summaryOf(getQuestion(q2)));
    }

    @Test
    void unknownAfterIsNotFound() {
        String id = UUID.randomUUID().toString();

        ApiResponse response = list("after=" + id);

        assertThat(response.status()).as(response.body()).isEqualTo(404);
        assertThat(response.json("$.error")).isEqualTo("QUESTION_NOT_FOUND");
        assertThat((String) response.json("$.message")).contains(id);
    }

    // The cursor only places the page: X doesn't carry the tag, and the page holds what sorts after it, in practice Q1.
    @Test
    void afterNeedNotMatchTag() {
        String tag = uniqueTag();
        ApiResponse q1 = create(tag);
        ApiResponse x = create(uniqueTag());
        ApiResponse q2 = create(tag);
        List<ApiResponse> order = newestFirst(List.of(q1, x, q2));
        List<String> expected = ids(order.subList(order.indexOf(x) + 1, order.size()));

        ApiResponse response = list("tag=" + tag + "&after=" + id(x));

        assertThat(response.status()).as(response.body()).isEqualTo(200);
        assertThat(response.json("$.items[*].id")).isEqualTo(expected);
        assertThat(response.json("$.nextCursor")).isNull();
    }

    @Test
    void acceptsUpperCaseAfter() {
        String tag = uniqueTag();
        List<ApiResponse> created = newestFirst(createMany(3, tag));
        String after = id(created.get(0));

        ApiResponse lower = list("tag=" + tag + "&after=" + after);
        ApiResponse upper = list("tag=" + tag + "&after=" + after.toUpperCase(Locale.ROOT));

        assertThat(lower.status()).as(lower.body()).isEqualTo(200);
        assertThat(lower.json("$.items[*].id")).isEqualTo(ids(created.subList(1, 3)));
        assertThat(upper.status()).as(upper.body()).isEqualTo(200);
        assertThat(upper.json("$")).isEqualTo(lower.json("$"));
    }

    // The untagged list holds every other test's questions too, so only the order and these three are checked.
    @Test
    void walksWholeList() {
        List<ApiResponse> created = createMany(3, "java", "concurrency");

        List<Map<String, Object>> all = walk("", 100);

        assertNewestFirst(all);
        assertThat(itemIds(all)).containsSubsequence(ids(newestFirst(created)));
    }

    // Offset paging would have repeated Q5 and Q4 on page 2, after Q6 and Q7 were created.
    @Test
    void changesBetweenPagesDoNotShiftPages() {
        String tag = uniqueTag();
        List<ApiResponse> questions = newestFirst(createMany(5, tag));
        String query = "tag=" + tag + "&limit=2";
        ApiResponse page1 = list(query);
        assertThat(page1.status()).as(page1.body()).isEqualTo(200);
        assertThat(page1.json("$.items[*].id")).isEqualTo(ids(questions.subList(0, 2)));
        assertThat(page1.json("$.nextCursor")).isEqualTo(id(questions.get(1)));

        List<ApiResponse> newer = createMany(2, tag);
        String editedContent = edit(questions.get(2), tag);
        vote(questions.get(3), "upvotes");
        answer(questions.get(4));
        ApiResponse page2 = list(query + "&after=" + page1.json("$.nextCursor"));
        ApiResponse page3 = list(query + "&after=" + page2.json("$.nextCursor"));

        assertThat(page2.status()).as(page2.body()).isEqualTo(200);
        assertThat(page2.json("$.items[*].id")).isEqualTo(ids(questions.subList(2, 4)));
        assertThat(page2.json("$.items[0].content")).isEqualTo(editedContent);
        assertThat(page2.json("$.items[1].upvotes")).isEqualTo(1);
        assertThat(page2.json("$.nextCursor")).isEqualTo(id(questions.get(3)));
        assertThat(page3.status()).as(page3.body()).isEqualTo(200);
        assertThat(page3.json("$.items[*].id")).isEqualTo(ids(questions.subList(4, 5)));
        assertThat(page3.json("$.items[0].answerCount")).isEqualTo(1);
        assertThat(page3.json("$.nextCursor")).isNull();
        List<ApiResponse> all = new ArrayList<>(questions);
        all.addAll(newer);
        assertThat(itemIds(walk("tag=" + tag, 2))).isEqualTo(ids(newestFirst(all)));
    }

    // Each walk may or may not see each new question, but never one twice, and never misses an earlier one.
    @Test
    void parallelCreatesWhilePaging() throws Exception {
        String tag = uniqueTag();
        List<ApiResponse> earlier = newestFirst(createMany(20, tag));
        List<ApiResponse> all = new ArrayList<>(earlier);
        ExecutorService pool = Executors.newFixedThreadPool(PARALLEL_CREATES + WALKERS);
        CountDownLatch ready = new CountDownLatch(PARALLEL_CREATES + WALKERS);
        CountDownLatch start = new CountDownLatch(1);
        try {
            List<Future<ApiResponse>> creates = new ArrayList<>();
            for (int i = 0; i < PARALLEL_CREATES; i++) {
                creates.add(pool.submit(afterStart(ready, start, () -> create(tag))));
            }
            List<Future<List<Map<String, Object>>>> walks = new ArrayList<>();
            for (int i = 0; i < WALKERS; i++) {
                walks.add(pool.submit(afterStart(ready, start, () -> walk("tag=" + tag, 3))));
            }
            assertThat(ready.await(10, TimeUnit.SECONDS)).isTrue();
            start.countDown();

            for (Future<ApiResponse> create : creates) {
                all.add(create.get(60, TimeUnit.SECONDS));
            }
            for (Future<List<Map<String, Object>>> walk : walks) {
                List<Map<String, Object>> walked = walk.get(60, TimeUnit.SECONDS);
                assertNewestFirst(walked);
                assertThat(itemIds(walked)).containsSubsequence(ids(earlier));
                assertThat(itemIds(walked)).isSubsetOf(ids(all));
            }
        } finally {
            pool.shutdownNow();
        }

        assertThat(itemIds(walk("tag=" + tag, 100))).isEqualTo(ids(newestFirst(all)));
    }

    // Posts fresh content with these tags as a fresh user, and asserts 201.
    private ApiResponse create(String... tags) {
        String content = "Listed question " + UUID.randomUUID();
        ApiResponse response = api.post(QUESTIONS, RequestSpec.validCreate().withBody(body(content, tags)));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return response;
    }

    private List<ApiResponse> createMany(int count, String... tags) {
        List<ApiResponse> created = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            created.add(create(tags));
        }
        return created;
    }

    // GET /questions?<query> with no headers.
    private ApiResponse list(String query) {
        return api.get(query.isEmpty() ? QUESTIONS : QUESTIONS + "?" + query, Map.of());
    }

    private List<Map<String, Object>> walk(String query, int limit) {
        return pages(query, limit).stream().flatMap(List::stream).toList();
    }

    // Follows nextCursor as after until it's null. Each page is 200 with at most limit items, and its nextCursor is
    // its last id or null. A page with a nextCursor is full. A cursor seen twice fails rather than looping forever.
    private List<List<Map<String, Object>>> pages(String query, int limit) {
        List<List<Map<String, Object>>> pages = new ArrayList<>();
        Set<String> cursors = new HashSet<>();
        String after = null;
        do {
            String pageQuery = Stream.of(query, "limit=" + limit, after == null ? "" : "after=" + after)
                    .filter(part -> !part.isEmpty())
                    .collect(Collectors.joining("&"));
            ApiResponse response = list(pageQuery);
            assertThat(response.status()).as(response.body()).isEqualTo(200);
            List<Map<String, Object>> items = items(response);
            after = (String) response.json("$.nextCursor");
            if (after == null) {
                assertThat(items).hasSizeLessThanOrEqualTo(limit);
            } else {
                assertThat(items).hasSize(limit);
                assertThat(after).isEqualTo(itemId(items.get(limit - 1)));
                assertThat(cursors.add(after)).as("cursor %s seen twice", after).isTrue();
            }
            pages.add(items);
        } while (after != null);
        return pages;
    }

    // (createdAt, id) strictly decreases, which also rules out duplicates.
    private static void assertNewestFirst(List<Map<String, Object>> items) {
        for (int i = 1; i < items.size(); i++) {
            assertThat(NEWEST_FIRST.compare(items.get(i - 1), items.get(i)))
                    .as("%s before %s", itemId(items.get(i - 1)), itemId(items.get(i)))
                    .isNegative();
        }
    }

    // The order the list must show these questions in. In practice, the reverse of creation order.
    private static List<ApiResponse> newestFirst(List<ApiResponse> created) {
        return created.stream().sorted(Comparator.comparing(ListQuestionsFT::fields, NEWEST_FIRST)).toList();
    }

    // ft- and 24 random hex chars: a tag no other test or run uses.
    private static String uniqueTag() {
        return "ft-" + UUID.randomUUID().toString().replace("-", "").substring(0, 24);
    }

    // A create or GET question body as a list item: answerCount in place of answers.
    private static Map<String, Object> summaryOf(ApiResponse question) {
        Map<String, Object> summary = new LinkedHashMap<>(fields(question));
        List<?> answers = (List<?>) summary.remove("answers");
        summary.put("answerCount", answers.size());
        return summary;
    }

    // Returns the new content. The tags are replaced by just tag, so the question keeps it.
    private String edit(ApiResponse question, String tag) {
        String content = "Edited question " + UUID.randomUUID();
        RequestSpec request = RequestSpec.validUpdate((String) question.json("$.authorId")).withBody(body(content, tag));
        ApiResponse response = api.put(path(question), request);
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return content;
    }

    private void answer(ApiResponse question) {
        ApiResponse response = api.post(path(question) + "/answers", RequestSpec.validAnswer());
        assertThat(response.status()).as(response.body()).isEqualTo(201);
    }

    // votes is "upvotes" or "downvotes". Each vote is by a fresh user.
    private void vote(ApiResponse question, String votes) {
        ApiResponse response =
                api.post(path(question) + "/" + votes, RequestSpec.validVote(RequestSpec.freshUser()));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
    }

    private ApiResponse getQuestion(ApiResponse question) {
        ApiResponse response = api.get(path(question), Map.of());
        assertThat(response.status()).as(response.body()).isEqualTo(200);
        return response;
    }

    // Every task waits on the start latch, so all of them are released together and really overlap.
    private static <T> Callable<T> afterStart(CountDownLatch ready, CountDownLatch start, Callable<T> task) {
        return () -> {
            ready.countDown();
            start.await();
            return task.call();
        };
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> items(ApiResponse page) {
        return (List<Map<String, Object>>) page.json("$.items");
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> fields(ApiResponse question) {
        return (Map<String, Object>) question.json("$");
    }

    private static String id(ApiResponse question) {
        return (String) question.json("$.id");
    }

    private static String itemId(Map<String, Object> item) {
        return (String) item.get("id");
    }

    private static List<String> ids(List<ApiResponse> questions) {
        return questions.stream().map(ListQuestionsFT::id).toList();
    }

    private static List<String> itemIds(List<Map<String, Object>> items) {
        return items.stream().map(ListQuestionsFT::itemId).toList();
    }

    private static String path(ApiResponse question) {
        return QUESTIONS + "/" + id(question);
    }

    private static String upper(String tag) {
        return tag.toUpperCase(Locale.ROOT);
    }

    private static String body(String content, String... tags) {
        String tagList = Stream.of(tags).map(tag -> "\"" + tag + "\"").collect(Collectors.joining(", "));
        return "{\"content\": \"" + content + "\", \"tags\": [" + tagList + "]}";
    }
}
