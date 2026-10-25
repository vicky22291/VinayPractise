package com.practice.qabank.model;

// The target's count, including this vote. A replay carries the count stored with the original vote.
public record UpvoteResponse(int upvotes) {
}
