package com.example.qabackend.model;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public class Question {
    private UUID id;
    private String title;
    private String description;
    private String authorId;
    private int voteCount;
    private Set<String> voters;
    private Instant createdAt;

    public Question(String title, String description, String authorId) {
        this.id = UUID.randomUUID();
        this.title = title;
        this.description = description;
        this.authorId = authorId;
        this.voteCount = 0;
        this.voters = ConcurrentHashMap.newKeySet();
        this.createdAt = Instant.now();
    }

    public synchronized void upvote(String userId) {
        if (authorId.equals(userId)) {
            throw new IllegalArgumentException("Author cannot vote");
        }
        if (voters.contains(userId)) {
            throw new IllegalArgumentException("Duplicate vote");
        }
        voters.add(userId);
        voteCount++;
    }

    public UUID getId() { return id; }
    public String getTitle() { return title; }
    public String getDescription() { return description; }
    public String getAuthorId() { return authorId; }
    public int getVoteCount() { return voteCount; }
    public Instant getCreatedAt() { return createdAt; }
}
