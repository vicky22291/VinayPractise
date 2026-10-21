package com.example.qabank.web;

import java.util.List;
import java.util.UUID;

public record PageResponse(List<QuestionResponse> items, UUID nextCursor) {
}
