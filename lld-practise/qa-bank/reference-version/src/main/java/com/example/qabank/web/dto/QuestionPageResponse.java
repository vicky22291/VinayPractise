package com.example.qabank.web.dto;

import java.util.List;

public record QuestionPageResponse(List<QuestionSummaryResponse> items, String nextCursor) {
}
