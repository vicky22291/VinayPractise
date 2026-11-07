package com.practice.stripe.ridemap;

/** An error returned by the MapDraw service. */
public class MapDrawError extends RuntimeException {
    private final int status;

    public MapDrawError(int status, String message) {
        super("MapDraw " + status + ": " + message);
        this.status = status;
    }

    public int status() {
        return status;
    }
}
