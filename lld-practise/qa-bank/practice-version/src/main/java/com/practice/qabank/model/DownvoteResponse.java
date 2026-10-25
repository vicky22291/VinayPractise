package com.practice.qabank.model;

// The target's downvote count, including this vote. A replay carries the count stored with the original vote.
public record DownvoteResponse(int downvotes) {
}
