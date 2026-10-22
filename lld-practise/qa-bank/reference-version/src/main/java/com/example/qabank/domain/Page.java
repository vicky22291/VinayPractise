package com.example.qabank.domain;

import java.util.List;

/** One page of results. nextCursor is null on the last page. */
public record Page<T>(List<T> items, PageCursor nextCursor) {
    public Page {
        items = List.copyOf(items);
    }

    public boolean hasNext() {
        return nextCursor != null;
    }
}
