package com.example.qabank.web;

import java.util.UUID;

public record UpvoteResponse(UUID questionId, int upvotes) {
}
