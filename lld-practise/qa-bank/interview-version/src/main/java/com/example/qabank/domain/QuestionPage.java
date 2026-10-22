package com.example.qabank.domain;

import java.util.List;
import java.util.UUID;

public record QuestionPage(List<QuestionView> items, UUID nextCursor) {
}
