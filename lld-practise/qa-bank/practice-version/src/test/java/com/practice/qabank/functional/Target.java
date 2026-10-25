package com.practice.qabank.functional;

// What a vote endpoint votes on. Vote FTs that take a Target run once per endpoint.
enum Target {
    QUESTION,
    ANSWER;

    // A question or answer path. The votes paths are this plus /upvotes or /downvotes.
    String targetPath(Fixture f) {
        return switch (this) {
            case QUESTION -> "/questions/" + f.questionId();
            case ANSWER -> "/questions/" + f.questionId() + "/answers/" + f.answerId();
        };
    }

    String authorId(Fixture f) {
        return switch (this) {
            case QUESTION -> f.questionAuthor();
            case ANSWER -> f.answerAuthor();
        };
    }
}
