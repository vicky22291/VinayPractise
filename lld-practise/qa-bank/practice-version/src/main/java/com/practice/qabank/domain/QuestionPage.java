package com.practice.qabank.domain;

import java.util.List;
import java.util.UUID;

// One page of the question list, newest first. nextCursor is the last item's id when more questions follow, and null on
// the last page; the client sends it back as after.
public record QuestionPage(List<Question> items, UUID nextCursor) {

    public QuestionPage {
        items = List.copyOf(items);
    }
}
