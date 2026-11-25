// SPOILER for code-review exercise 01. Run only after your review is written.
// Run: java code-review/answers/01-checkout-service/Repro.java   (JDK 21+, no dependencies)
// Each demo proves one finding from the answer key with a number, not an argument.

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.LongAdder;

public class Repro {

    public static void main(String[] args) throws Exception {
        volatileCounter();
        synchronizedThenCommit();
        hashMapLostPuts();
        sharedSimpleDateFormat();
        boxedLongEquality();
        doubleMoney();
        System.exit(0);   // daemon threads from a hung demo must not keep the JVM alive
    }

    // Finding C1: OrderStats.placed++ on a volatile long loses updates.
    static volatile long placed;

    static void volatileCounter() throws Exception {
        int threads = 8, perThread = 1_000_000;
        LongAdder adder = new LongAdder();
        runConcurrently(threads, () -> {
            for (int i = 0; i < perThread; i++) {
                placed++;
                adder.increment();
            }
        });
        System.out.printf("[C1] volatile ++    expected %,d got %,d (lost %,d)%n",
                (long) threads * perThread, placed, (long) threads * perThread - placed);
        System.out.printf("[C1] LongAdder      expected %,d got %,d%n", (long) threads * perThread, adder.sum());
    }

    // Finding P0-2: synchronized on a @Transactional method. The proxy commits AFTER the
    // synchronized method returns, so a second thread reads the old committed stock.
    static final class FakeDb {
        private int committedStock;
        FakeDb(int stock) { committedStock = stock; }
        synchronized int readCommitted() { return committedStock; }
        synchronized void write(int stock) { committedStock = stock; }
        // The fix: one atomic conditional write, like
        // UPDATE products SET stock = stock - :n WHERE id = :id AND stock >= :n
        synchronized boolean decrementIfEnough(int n) {
            if (committedStock < n) return false;
            committedStock -= n;
            return true;
        }
    }

    static final class CheckoutTarget {
        private final FakeDb db;
        CheckoutTarget(FakeDb db) { this.db = db; }

        // Body of placeOrder: read stock, check, compute the new value. Returns the pending write.
        synchronized Integer placeOrder(int qty) {
            int stock = db.readCommitted();
            if (stock < qty) return null;
            return stock - qty;
        }
    }

    static void synchronizedThenCommit() throws Exception {
        int trials = 200, oversold = 0;
        for (int t = 0; t < trials; t++) {
            FakeDb db = new FakeDb(1);
            CheckoutTarget target = new CheckoutTarget(db);
            AtomicInteger sold = new AtomicInteger();
            runConcurrently(2, () -> {
                Integer pending = target.placeOrder(1);   // lock taken and released here
                if (pending != null) {
                    sleepMs(2);                              // payment call, Kafka send, audit insert...
                    db.write(pending);                       // TransactionInterceptor commits after return
                    sold.incrementAndGet();
                }
            });
            if (sold.get() > 1) oversold++;
        }
        System.out.printf("[P0-2] synchronized + commit after return: last unit sold twice in %d of %d trials%n",
                oversold, trials);

        int fixedOversold = 0;
        for (int t = 0; t < trials; t++) {
            FakeDb db = new FakeDb(1);
            AtomicInteger sold = new AtomicInteger();
            runConcurrently(2, () -> {
                if (db.decrementIfEnough(1)) sold.incrementAndGet();
            });
            if (sold.get() > 1) fixedOversold++;
        }
        System.out.printf("[P0-2] conditional UPDATE fix:            last unit sold twice in %d of %d trials%n",
                fixedOversold, trials);
    }

    // Finding C2: PriceCache does get-then-put on a HashMap shared by 200 request threads.
    static void hashMapLostPuts() throws Exception {
        int threads = 8, perThread = 100_000, keys = 16;
        Map<Integer, Integer> plain = new HashMap<>();
        Map<Integer, Integer> concurrent = new ConcurrentHashMap<>();
        for (int k = 0; k < keys; k++) {
            plain.put(k, 0);
            concurrent.put(k, 0);
        }
        boolean finished = runConcurrently(threads, () -> {
            for (int i = 0; i < perThread; i++) {
                int key = i % keys;
                plain.put(key, plain.get(key) + 1);   // get-then-put, like PriceCache.priceOf
                concurrent.merge(key, 1, Integer::sum); // one atomic step
            }
        });
        if (!finished) {
            System.out.println("[C2] HashMap demo hung: a racing put corrupted the map into a loop. That is the bug too.");
            return;
        }
        int plainSum = plain.values().stream().mapToInt(Integer::intValue).sum();
        int concurrentSum = concurrent.values().stream().mapToInt(Integer::intValue).sum();
        System.out.printf("[C2] HashMap get-then-put  expected %,d got %,d%n", threads * perThread, plainSum);
        System.out.printf("[C2] ConcurrentHashMap.merge expected %,d got %,d%n", threads * perThread, concurrentSum);
    }

    // Finding C4: static SimpleDateFormat shared across threads.
    static final SimpleDateFormat DAY = new SimpleDateFormat("yyyy-MM-dd");

    static void sharedSimpleDateFormat() throws Exception {
        long dayA = 1_700_000_000_000L;               // 2023-11-14
        long dayB = 1_710_000_000_000L;               // 2024-03-09
        String expectA = new SimpleDateFormat("yyyy-MM-dd").format(new Date(dayA));
        String expectB = new SimpleDateFormat("yyyy-MM-dd").format(new Date(dayB));
        AtomicInteger wrong = new AtomicInteger();
        AtomicInteger crashed = new AtomicInteger();
        int threads = 8, perThread = 20_000;
        runConcurrently(threads, new Runnable() {
            final AtomicInteger id = new AtomicInteger();
            public void run() {
                boolean useA = id.getAndIncrement() % 2 == 0;
                for (int i = 0; i < perThread; i++) {
                    try {
                        String got = DAY.format(new Date(useA ? dayA : dayB));
                        if (!got.equals(useA ? expectA : expectB)) wrong.incrementAndGet();
                    } catch (RuntimeException e) {
                        crashed.incrementAndGet();   // corrupted internal Calendar state
                    }
                }
            }
        });
        System.out.printf("[C4] shared SimpleDateFormat: %,d wrong dates and %,d exceptions out of %,d calls%n",
                wrong.get(), crashed.get(), threads * perThread);
    }

    // Finding P1-9: OrderHistoryService compares two Long objects with ==.
    static void boxedLongEquality() {
        Long customerA = 127L, sameA = 127L;
        Long customerB = 128L, sameB = 128L;
        System.out.printf("[P1-9] Long 127 == Long 127: %b; Long 128 == Long 128: %b; equals: %b%n",
                customerA == sameA, customerB == sameB, customerB.equals(sameB));
    }

    // Finding P0-5: money in double, and a discounted price never rounded to the currency unit.
    static void doubleMoney() {
        double unit = 59.90 * (1 - 0.30);      // PriceCache: basePrice * (1 - discount)
        double total = unit * 3;               // CheckoutService: total += unitPrice * qty
        System.out.printf("[P0-5] 59.90 at 30%% off, qty 3: total = %s, sent as \"amount\":%s%n", total, total);
        System.out.printf("[P0-5] 19.99 at 10%% off: unit price = %s (a tenth of a cent)%n", 19.99 * (1 - 0.10));
        System.out.printf("[P0-5] 0.1 + 0.2 == 0.3 is %b%n", 0.1 + 0.2 == 0.3);
    }

    /** Runs task on N daemon threads at once. Returns false if they do not finish in 20 s. */
    static boolean runConcurrently(int threads, Runnable task) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(threads, r -> {
            Thread t = new Thread(r);
            t.setDaemon(true);
            return t;
        });
        CountDownLatch start = new CountDownLatch(1);
        List<Future<?>> futures = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            futures.add(pool.submit(() -> {
                start.await();
                task.run();
                return null;
            }));
        }
        start.countDown();
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(20);
        try {
            for (Future<?> f : futures) {
                f.get(Math.max(1, deadline - System.nanoTime()), TimeUnit.NANOSECONDS);
            }
            return true;
        } catch (TimeoutException e) {
            return false;
        } finally {
            pool.shutdownNow();
        }
    }

    static void sleepMs(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
