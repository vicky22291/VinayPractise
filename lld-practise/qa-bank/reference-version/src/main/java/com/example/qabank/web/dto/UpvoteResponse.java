package com.example.qabank.web.dto;

import java.util.UUID;

public record UpvoteResponse(UUID questionId, int upvotes) {
}
