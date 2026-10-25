package com.practice.qabank.web;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.aMapWithSize;
import static org.hamcrest.Matchers.contains;
import static org.hamcrest.Matchers.empty;
import static org.hamcrest.Matchers.hasKey;
import static org.hamcrest.Matchers.nullValue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.junit.jupiter.params.provider.Arguments.arguments;
import static org.mockito.Mockito.verify;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.IdempotentResult;
import com.practice.qabank.domain.Question;
import com.practice.qabank.domain.QuestionPage;
import com.practice.qabank.domain.Vote;
import com.practice.qabank.mapper.QuestionMapperImpl;
import com.practice.qabank.service.QuestionService;

@WebMvcTest(QuestionController.class)
@Import(QuestionMapperImpl.class)
class QuestionControllerTest {

    private static final UUID ID = UUID.fromString("3f1c9a52-8a7e-4f0b-9d0e-2b6c1f6a7e11");
    private static final UUID OTHER_ID = UUID.fromString("c81f5e30-6a2d-4b7c-8e19-0d3f4a5b6c72");
    private static final Instant CREATED_AT = Instant.parse("2026-10-24T06:12:45.123Z");
    private static final Question STORED = new Question(
            ID, "user-42", "How do I make it atomic?", List.of("java", "concurrency"), CREATED_AT, null, null, null);
    private static final Question EDITED = new Question(ID, "user-42", "How do I make it atomic without locks?",
            List.of("java", "atomic"), CREATED_AT, Instant.parse("2026-10-24T06:20:03.456Z"), null, null);

    @Autowired
    MockMvc mvc;

    @MockitoBean
    QuestionService service;

    @Test
    void createReturns201WithLocationAndBody() throws Exception {
        given(service.create(any(), anyString())).willReturn(new IdempotentResult<>(STORED, false));

        mvc.perform(validCreate())
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/questions/" + ID))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$.id").value(ID.toString()))
                .andExpect(jsonPath("$.authorId").value("user-42"))
                .andExpect(jsonPath("$.content").value("How do I make it atomic?"))
                .andExpect(jsonPath("$.tags", contains("java", "concurrency")))
                .andExpect(jsonPath("$.createdAt").value("2026-10-24T06:12:45.123Z"))
                .andExpect(jsonPath("$.updatedAt").value(nullValue()))
                .andExpect(jsonPath("$.upvotes").value(0))
                .andExpect(jsonPath("$.downvotes").value(0))
                .andExpect(jsonPath("$.answers", empty()));
    }

    @Test
    void replayReturns201WithOriginalAndReplayHeader() throws Exception {
        given(service.create(any(), anyString())).willReturn(new IdempotentResult<>(STORED, true));

        mvc.perform(validCreate())
                .andExpect(status().isCreated())
                .andExpect(header().string("Location", "/questions/" + ID))
                .andExpect(header().string("Idempotent-Replayed", "true"))
                .andExpect(jsonPath("$.id").value(ID.toString()));
    }

    // The counts are the returned question's own, so a replay shows them as they were stored.
    @ParameterizedTest(name = "{0}")
    @MethodSource("replayFlags")
    void createShowsTheReturnedQuestionsCounts(String name, boolean replayed) throws Exception {
        given(service.create(any(), anyString())).willReturn(new IdempotentResult<>(voted(STORED, 2, 3), replayed));

        mvc.perform(validCreate())
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.upvotes").value(2))
                .andExpect(jsonPath("$.downvotes").value(3));
    }

    static Stream<Arguments> replayFlags() {
        return Stream.of(
                arguments("first response", false),
                arguments("replay", true));
    }

    @Test
    void passesDraftFromBodyAndUserHeaderPlusKeyToService() throws Exception {
        given(service.create(any(), anyString())).willReturn(new IdempotentResult<>(STORED, false));

        mvc.perform(validCreate()).andExpect(status().isCreated());

        ArgumentCaptor<Question> draft = ArgumentCaptor.forClass(Question.class);
        ArgumentCaptor<String> key = ArgumentCaptor.forClass(String.class);
        verify(service).create(draft.capture(), key.capture());
        assertThat(key.getValue()).isEqualTo("key-1");
        assertThat(draft.getValue().authorId()).isEqualTo("user-42");
        assertThat(draft.getValue().content()).isEqualTo("How do I make it atomic?");
        assertThat(draft.getValue().tags()).containsExactly("java", "concurrency");
        assertThat(draft.getValue().id()).isNull();
        assertThat(draft.getValue().createdAt()).isNull();
        assertThat(draft.getValue().updatedAt()).isNull();
        assertThat(draft.getValue().answers()).isEmpty();
    }

    // Each item shows its own counts, and how many answers it has instead of the answers.
    @Test
    void listReturns200WithItemsAndNextCursor() throws Exception {
        Answer first = new Answer(UUID.fromString("9b2e4d71-0c3a-4f5e-8b6d-1a7c2e9f4b30"), "user-7", "First",
                Instant.parse("2026-10-24T06:20:02.481Z"), null, null);
        Answer second = new Answer(UUID.fromString("1c4f7a20-5d8e-4b3a-9f61-7e2d0c8b5a94"), "user-8", "Second",
                Instant.parse("2026-10-24T06:21:00Z"), null, null);
        Question older = new Question(OTHER_ID, "user-9", "When does values() see a put?", List.of("java"),
                Instant.parse("2026-10-24T06:00:00Z"), null, List.of(first, second), null);
        given(service.list(any(), any(), anyInt()))
                .willReturn(new QuestionPage(List.of(voted(EDITED, 2, 3), voted(older, 4, 0)), null));

        mvc.perform(get("/questions"))
                .andExpect(status().isOk())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$", aMapWithSize(2)))
                .andExpect(jsonPath("$", hasKey("nextCursor")))
                .andExpect(jsonPath("$.nextCursor").value(nullValue()))
                .andExpect(jsonPath("$.items.length()").value(2))
                .andExpect(jsonPath("$.items[0]", aMapWithSize(9)))
                .andExpect(jsonPath("$.items[0].id").value(ID.toString()))
                .andExpect(jsonPath("$.items[0].authorId").value("user-42"))
                .andExpect(jsonPath("$.items[0].content").value("How do I make it atomic without locks?"))
                .andExpect(jsonPath("$.items[0].tags", contains("java", "atomic")))
                .andExpect(jsonPath("$.items[0].createdAt").value("2026-10-24T06:12:45.123Z"))
                .andExpect(jsonPath("$.items[0].updatedAt").value("2026-10-24T06:20:03.456Z"))
                .andExpect(jsonPath("$.items[0].upvotes").value(2))
                .andExpect(jsonPath("$.items[0].downvotes").value(3))
                .andExpect(jsonPath("$.items[0].answerCount").value(0))
                .andExpect(jsonPath("$.items[1]", aMapWithSize(9)))
                .andExpect(jsonPath("$.items[1].id").value(OTHER_ID.toString()))
                .andExpect(jsonPath("$.items[1].updatedAt").value(nullValue()))
                .andExpect(jsonPath("$.items[1].upvotes").value(4))
                .andExpect(jsonPath("$.items[1].downvotes").value(0))
                .andExpect(jsonPath("$.items[1].answerCount").value(2));
    }

    @Test
    void listShowsTheNextCursor() throws Exception {
        given(service.list(any(), any(), anyInt())).willReturn(new QuestionPage(List.of(STORED), ID));

        mvc.perform(get("/questions?limit=1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items[*].id", contains(ID.toString())))
                .andExpect(jsonPath("$.nextCursor").value(ID.toString()));
    }

    @Test
    void listWorksWithoutUserHeader() throws Exception {
        given(service.list(any(), any(), anyInt())).willReturn(new QuestionPage(List.of(), null));

        mvc.perform(get("/questions"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items", empty()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("listQueries")
    void listPassesQueryParametersToService(String name, String query, String tag, UUID after, int limit)
            throws Exception {
        given(service.list(any(), any(), anyInt())).willReturn(new QuestionPage(List.of(), null));

        mvc.perform(get("/questions" + query)).andExpect(status().isOk());

        verify(service).list(tag, after, limit);
    }

    // The service, not the controller, lowercases the tag.
    static Stream<Arguments> listQueries() {
        return Stream.of(
                arguments("no parameters", "", null, null, 20),
                arguments("limit= counts as absent", "?limit=", null, null, 20),
                arguments("after= counts as absent", "?after=", null, null, 20),
                arguments("tag=Java passes as sent", "?tag=Java", "Java", null, 20),
                arguments("upper-case after", "?after=" + ID.toString().toUpperCase(Locale.ROOT), null, ID, 20),
                arguments("limit=1", "?limit=1", null, null, 1),
                arguments("limit=100", "?limit=100", null, null, 100));
    }

    @Test
    void getReturns200WithEveryFieldAndNoLocation() throws Exception {
        Instant updatedAt = Instant.parse("2026-10-24T06:20:03.456Z");
        Question edited = new Question(ID, "user-42", "How do I make it atomic?", List.of("java", "concurrency"),
                CREATED_AT, updatedAt, null, null);
        given(service.get(ID)).willReturn(edited);

        mvc.perform(get("/questions/" + ID))
                .andExpect(status().isOk())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$.id").value(ID.toString()))
                .andExpect(jsonPath("$.authorId").value("user-42"))
                .andExpect(jsonPath("$.content").value("How do I make it atomic?"))
                .andExpect(jsonPath("$.tags", contains("java", "concurrency")))
                .andExpect(jsonPath("$.createdAt").value("2026-10-24T06:12:45.123Z"))
                .andExpect(jsonPath("$.updatedAt").value("2026-10-24T06:20:03.456Z"))
                .andExpect(jsonPath("$.upvotes").value(0))
                .andExpect(jsonPath("$.downvotes").value(0))
                .andExpect(jsonPath("$.answers", empty()));
    }

    @Test
    void getReturnsAnswersInStoredOrder() throws Exception {
        Answer first = new Answer(UUID.fromString("9b2e4d71-0c3a-4f5e-8b6d-1a7c2e9f4b30"), "user-7", "First",
                Instant.parse("2026-10-24T06:20:02.481Z"), null, null);
        Answer second = new Answer(UUID.fromString("1c4f7a20-5d8e-4b3a-9f61-7e2d0c8b5a94"), "user-8", "Second",
                Instant.parse("2026-10-24T06:21:00Z"), Instant.parse("2026-10-24T06:25:00Z"), null);
        given(service.get(ID)).willReturn(STORED.withAnswer(first).withAnswer(second));

        mvc.perform(get("/questions/" + ID))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answers.length()").value(2))
                .andExpect(jsonPath("$.answers[0].id").value(first.id().toString()))
                .andExpect(jsonPath("$.answers[0].authorId").value("user-7"))
                .andExpect(jsonPath("$.answers[0].content").value("First"))
                .andExpect(jsonPath("$.answers[0].createdAt").value("2026-10-24T06:20:02.481Z"))
                .andExpect(jsonPath("$.answers[0].updatedAt").value(nullValue()))
                .andExpect(jsonPath("$.answers[1].id").value(second.id().toString()))
                .andExpect(jsonPath("$.answers[1].authorId").value("user-8"))
                .andExpect(jsonPath("$.answers[1].content").value("Second"))
                .andExpect(jsonPath("$.answers[1].createdAt").value("2026-10-24T06:21:00Z"))
                .andExpect(jsonPath("$.answers[1].updatedAt").value("2026-10-24T06:25:00Z"));
    }

    @Test
    void getShowsTheQuestionsAndEachAnswersCounts() throws Exception {
        Answer first = new Answer(UUID.fromString("9b2e4d71-0c3a-4f5e-8b6d-1a7c2e9f4b30"), "user-7", "First",
                Instant.parse("2026-10-24T06:20:02.481Z"), null, null);
        Answer second = new Answer(UUID.fromString("1c4f7a20-5d8e-4b3a-9f61-7e2d0c8b5a94"), "user-8", "Second",
                Instant.parse("2026-10-24T06:21:00Z"), null, null);
        given(service.get(ID)).willReturn(voted(STORED, 5, 6).withAnswer(voted(first, 3, 4)).withAnswer(second));

        mvc.perform(get("/questions/" + ID))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.upvotes").value(5))
                .andExpect(jsonPath("$.downvotes").value(6))
                .andExpect(jsonPath("$.answers[0].upvotes").value(3))
                .andExpect(jsonPath("$.answers[0].downvotes").value(4))
                .andExpect(jsonPath("$.answers[1].upvotes").value(0))
                .andExpect(jsonPath("$.answers[1].downvotes").value(0));
    }

    @Test
    void getWorksWithoutUserHeader() throws Exception {
        given(service.get(ID)).willReturn(STORED);

        mvc.perform(get("/questions/" + ID))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(ID.toString()));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("idForms")
    void getPassesTheParsedIdToService(String name, String id) throws Exception {
        given(service.get(ID)).willReturn(STORED);

        mvc.perform(get("/questions/" + id))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(ID.toString()));

        verify(service).get(ID);
    }

    static Stream<Arguments> idForms() {
        return Stream.of(
                arguments("lower case", ID.toString()),
                arguments("upper case", ID.toString().toUpperCase(Locale.ROOT)));
    }

    @Test
    void updateReturns200WithBodyAndNoLocation() throws Exception {
        given(service.update(any(), any(), anyString())).willReturn(new IdempotentResult<>(EDITED, false));

        mvc.perform(validUpdate())
                .andExpect(status().isOk())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().doesNotExist("Idempotent-Replayed"))
                .andExpect(jsonPath("$.id").value(ID.toString()))
                .andExpect(jsonPath("$.authorId").value("user-42"))
                .andExpect(jsonPath("$.content").value("How do I make it atomic without locks?"))
                .andExpect(jsonPath("$.tags", contains("java", "atomic")))
                .andExpect(jsonPath("$.createdAt").value("2026-10-24T06:12:45.123Z"))
                .andExpect(jsonPath("$.updatedAt").value("2026-10-24T06:20:03.456Z"))
                .andExpect(jsonPath("$.upvotes").value(0))
                .andExpect(jsonPath("$.downvotes").value(0))
                .andExpect(jsonPath("$.answers", empty()));
    }

    @Test
    void updateReplayReturns200WithStoredBodyAndReplayHeader() throws Exception {
        given(service.update(any(), any(), anyString())).willReturn(new IdempotentResult<>(EDITED, true));

        mvc.perform(validUpdate())
                .andExpect(status().isOk())
                .andExpect(header().doesNotExist("Location"))
                .andExpect(header().string("Idempotent-Replayed", "true"))
                .andExpect(jsonPath("$.content").value("How do I make it atomic without locks?"));
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("replayFlags")
    void updateShowsTheReturnedQuestionsCounts(String name, boolean replayed) throws Exception {
        given(service.update(any(), any(), anyString()))
                .willReturn(new IdempotentResult<>(voted(EDITED, 2, 3), replayed));

        mvc.perform(validUpdate())
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.upvotes").value(2))
                .andExpect(jsonPath("$.downvotes").value(3));
    }

    @Test
    void updatePassesPathIdAndDraftFromBodyAndUserHeaderPlusKeyToService() throws Exception {
        given(service.update(any(), any(), anyString())).willReturn(new IdempotentResult<>(EDITED, false));

        mvc.perform(validUpdate()).andExpect(status().isOk());

        ArgumentCaptor<UUID> id = ArgumentCaptor.forClass(UUID.class);
        ArgumentCaptor<Question> draft = ArgumentCaptor.forClass(Question.class);
        ArgumentCaptor<String> key = ArgumentCaptor.forClass(String.class);
        verify(service).update(id.capture(), draft.capture(), key.capture());
        assertThat(id.getValue()).isEqualTo(ID);
        assertThat(key.getValue()).isEqualTo("key-2");
        assertThat(draft.getValue().authorId()).isEqualTo("user-42");
        assertThat(draft.getValue().content()).isEqualTo("How do I make it atomic without locks?");
        assertThat(draft.getValue().tags()).containsExactly("java", "atomic");
        assertThat(draft.getValue().id()).isNull();
        assertThat(draft.getValue().createdAt()).isNull();
        assertThat(draft.getValue().updatedAt()).isNull();
        assertThat(draft.getValue().answers()).isEmpty();
    }

    // question with up upvotes and down downvotes, each from its own voter.
    private static Question voted(Question question, int up, int down) {
        Question voted = question;
        for (int i = 0; i < up; i++) {
            voted = voted.withVote("up-" + i, Vote.UP);
        }
        for (int i = 0; i < down; i++) {
            voted = voted.withVote("down-" + i, Vote.DOWN);
        }
        return voted;
    }

    private static Answer voted(Answer answer, int up, int down) {
        Answer voted = answer;
        for (int i = 0; i < up; i++) {
            voted = voted.withVote("up-" + i, Vote.UP);
        }
        for (int i = 0; i < down; i++) {
            voted = voted.withVote("down-" + i, Vote.DOWN);
        }
        return voted;
    }

    private static MockHttpServletRequestBuilder validCreate() {
        return post("/questions")
                .header("X-User-Id", "user-42")
                .header("Idempotency-Key", "key-1")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"content\": \"How do I make it atomic?\", \"tags\": [\"Java\", \"concurrency\"]}");
    }

    private static MockHttpServletRequestBuilder validUpdate() {
        return put("/questions/" + ID)
                .header("X-User-Id", "user-42")
                .header("Idempotency-Key", "key-2")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"content\": \"How do I make it atomic without locks?\", "
                        + "\"tags\": [\"Java\", \"java\", \"Atomic\"]}");
    }
}
