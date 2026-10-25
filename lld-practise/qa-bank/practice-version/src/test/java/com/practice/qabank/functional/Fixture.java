package com.practice.qabank.functional;

import static com.practice.qabank.functional.RequestSpec.USER_ID;
import static org.assertj.core.api.Assertions.assertThat;

// The vote FTs' test data. answerAuthor wrote both answers. The other question is by a third user.
record Fixture(String questionAuthor, String questionId, String answerAuthor, String answerId,
        String otherQuestionId, String otherAnswerId) {

    private static final String QUESTIONS = "/questions";

    // A question by a fresh author, answered by a second fresh user, who also answers another question by a third.
    // Created only through the API.
    static Fixture create(ApiClient api) {
        String questionAuthor = RequestSpec.freshUser();
        String answerAuthor = RequestSpec.freshUser();
        String questionId = createQuestion(api, questionAuthor);
        String otherQuestionId = createQuestion(api, RequestSpec.freshUser());
        String answerId = answer(api, questionId, answerAuthor);
        String otherAnswerId = answer(api, otherQuestionId, answerAuthor);
        return new Fixture(questionAuthor, questionId, answerAuthor, answerId, otherQuestionId, otherAnswerId);
    }

    private static String createQuestion(ApiClient api, String authorId) {
        ApiResponse response = api.post(QUESTIONS, RequestSpec.validCreate().withHeader(USER_ID, authorId));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return (String) response.json("$.id");
    }

    private static String answer(ApiClient api, String questionId, String authorId) {
        ApiResponse response = api.post(QUESTIONS + "/" + questionId + "/answers",
                RequestSpec.validAnswer().withHeader(USER_ID, authorId));
        assertThat(response.status()).as(response.body()).isEqualTo(201);
        return (String) response.json("$.id");
    }
}
