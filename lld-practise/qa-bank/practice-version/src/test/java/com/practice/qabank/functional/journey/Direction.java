package com.practice.qabank.functional.journey;

// A vote's direction, and how its endpoints and errors name it.
enum Direction {
    UP("upvotes", "ALREADY_UPVOTED", "CANNOT_UPVOTE_OWN"),
    DOWN("downvotes", "ALREADY_DOWNVOTED", "CANNOT_DOWNVOTE_OWN");

    private final String countField;
    private final String alreadyCode;
    private final String ownCode;

    Direction(String countField, String alreadyCode, String ownCode) {
        this.countField = countField;
        this.alreadyCode = alreadyCode;
        this.ownCode = ownCode;
    }

    // Appended to a question or answer path.
    String pathSuffix() {
        return "/" + countField;
    }

    // The count's field in a vote body and in question and answer bodies.
    String countField() {
        return countField;
    }

    // The 409 code when the caller already holds a vote in this direction, whichever direction they tried.
    String alreadyCode() {
        return alreadyCode;
    }

    // The 403 code when the caller votes this way on their own question or answer.
    String ownCode() {
        return ownCode;
    }
}
