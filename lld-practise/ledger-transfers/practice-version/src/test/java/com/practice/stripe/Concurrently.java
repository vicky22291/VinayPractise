package com.practice.stripe;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import java.util.function.IntFunction;

final class Concurrently {
    private Concurrently() {}
    static <T> List<T> run(int count, IntFunction<T> operation) throws Exception {
        var start = new CountDownLatch(1);
        try (var executor = Executors.newFixedThreadPool(count)) {
            var tasks = new ArrayList<Future<T>>();
            for (int i = 0; i < count; i++) {
                final int index = i;
                tasks.add(executor.submit(() -> {
                    if (!start.await(5, TimeUnit.SECONDS)) throw new AssertionError("Start barrier timed out");
                    return operation.apply(index);
                }));
            }
            start.countDown();
            var results = new ArrayList<T>();
            for (Future<T> task : tasks) results.add(task.get(10, TimeUnit.SECONDS));
            return results;
        }
    }
}
