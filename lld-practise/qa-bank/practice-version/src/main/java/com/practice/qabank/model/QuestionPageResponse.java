package com.practice.qabank.model;

import java.util.List;
import java.util.UUID;

// The body of GET /questions. nextCursor is always present: the last item's id when more questions follow, else null.
public record QuestionPageResponse(List<QuestionSummaryResponse> items, UUID nextCursor) {
}
