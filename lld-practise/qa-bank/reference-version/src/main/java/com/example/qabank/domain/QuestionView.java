package com.example.qabank.domain;

/** Read model: a question plus its derived upvote count. */
public record QuestionView(Question question, int upvotes) {
}
