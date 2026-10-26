package com.vinaypractice3.qabank.controllers;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.vinaypractice3.qabank.commons.constants.QuestionsConstants;
import com.vinaypractice3.qabank.domain.CreateQuestionRequest;
import com.vinaypractice3.qabank.domain.QuestionResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import org.springframework.test.web.servlet.assertj.MvcTestResult;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.InstanceOfAssertFactories.map;

// Slice test: @WebMvcTest loads only this controller's web layer, so it starts faster than
// @SpringBootTest. If the controller gets a service, add it as a @MockitoBean field.
// MockMvcTester converts the JSON body back into an object, so we assert on data, not JSON paths.
@SpringBootTest
@AutoConfigureMockMvc
class QuestionsControllerTest {
    private static final String TITLE = "How to run tests?";
    private static final String DESCRIPTION = "How to run junit tests?";
    private static final String USER_ID = "USERID1";

    @Autowired
    private MockMvcTester mvc;

    @Autowired
    private ObjectMapper objectMapper;

    private MvcTestResult create(CreateQuestionRequest request) throws Exception {
        return this.mvc.post().uri(QuestionsConstants.BASE_QUESTIONS_PATH)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
                .header(QuestionsConstants.USER_HEADER, USER_ID)
                .exchange();
    }

    @Test
    void testFullLength() throws Exception {
        final CreateQuestionRequest createQuestionRequest = new CreateQuestionRequest(TITLE, DESCRIPTION);

        final MvcTestResult result = create(createQuestionRequest);
        final QuestionResponse created = this.objectMapper.readValue(result.getResponse().getContentAsString(), QuestionResponse.class);

        assertThat(result.getResponse().getStatus()).isEqualTo(HttpStatus.CREATED.value());
        assertThat(result.getResponse().getHeader("Location")).isEqualTo(QuestionsConstants.BASE_QUESTIONS_PATH + "/" + created.id());
        assertThat(created.authorId()).isEqualTo(USER_ID);

        final MvcTestResult getQuestionResult = mvc.get().uri(QuestionsConstants.BASE_QUESTIONS_PATH + "/" + created.id())
                .contentType(MediaType.APPLICATION_JSON)
                .exchange();
        final QuestionResponse questionResponse = this.objectMapper.readValue(getQuestionResult.getResponse().getContentAsString(), QuestionResponse.class);

        assertThat(getQuestionResult.getResponse().getStatus()).isEqualTo(HttpStatus.OK.value());
        assertThat(questionResponse.authorId()).isEqualTo(USER_ID);
        assertThat(questionResponse.id()).isEqualTo(created.id());
        assertThat(questionResponse.description()).isEqualTo(DESCRIPTION);
        assertThat(questionResponse.title()).isEqualTo(TITLE);

        final MvcTestResult getAllResult = mvc.get().uri(QuestionsConstants.BASE_QUESTIONS_PATH).contentType(MediaType.APPLICATION_JSON).exchange();
        final List<QuestionResponse> questionsList = this.objectMapper.readValue(getAllResult.getResponse().getContentAsString(), List.class);

        assertThat(getAllResult.getResponse().getStatus()).isEqualTo(HttpStatus.OK.value());
        assertThat(questionsList.size()).isEqualTo(1);

        final MvcTestResult upVoteResult = mvc.put().uri(QuestionsConstants.BASE_QUESTIONS_PATH + "/" + created.id() + "/upVote")
                .contentType(MediaType.APPLICATION_JSON)
                .header(QuestionsConstants.USER_HEADER, "ANOTHER_USER")
                .exchange();
        final QuestionResponse upVote = this.objectMapper.readValue(upVoteResult.getResponse().getContentAsString(), QuestionResponse.class);

        assertThat(upVoteResult.getResponse().getStatus()).isEqualTo(HttpStatus.OK.value());
        assertThat(upVote.upVotes()).isEqualTo(1);
    }
}
