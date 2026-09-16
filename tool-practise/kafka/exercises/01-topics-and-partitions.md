# 01. Topics and partitions

> Goal: after this I can explain how a key picks a partition and why ordering is only per partition.

**Concept link:** `concepts/kafka.md`, `popular_systems_deepdive/kafka/`
**Time:** ~30 min
**Status:** todo

## Setup

```
$ cd tool-practise/kafka
$ docker compose up -d
$ docker exec -it kafka bash
$ cd /opt/kafka/bin && B=localhost:19092
```

## Steps

### 1. Create a topic with 3 partitions

Why: partitions are the unit of parallelism and ordering.

```
$ ./kafka-topics.sh --bootstrap-server $B --create --topic orders --partitions 3 --replication-factor 1
$ ./kafka-topics.sh --bootstrap-server $B --describe --topic orders
```

### 2. Produce without keys

Why: no key means round-robin (actually sticky batches) across partitions. No ordering guarantee across messages.

```
$ ./kafka-console-producer.sh --bootstrap-server $B --topic orders
>order-1
>order-2
>order-3
>order-4
^C
```

### 3. Consume and print the partition each landed in

```
$ ./kafka-console-consumer.sh --bootstrap-server $B --topic orders --from-beginning \
    --property print.partition=true --property print.offset=true --timeout-ms 5000
```

### 4. Produce with keys

Why: `hash(key) % partitions`. Same key always hits the same partition, so per-key order is preserved.

```
$ ./kafka-console-producer.sh --bootstrap-server $B --topic orders \
    --property parse.key=true --property key.separator=:
>user-a:created
>user-b:created
>user-a:paid
>user-b:paid
>user-a:shipped
^C
```

Consume again with `print.key=true` and confirm all `user-a` events share one partition.

### 5. Look at the raw log segment

Why: it is just a file. Seeing the bytes makes "append-only log" concrete.

```
$ ls /tmp/kraft-combined-logs/orders-0/
$ ./kafka-dump-log.sh --files /tmp/kraft-combined-logs/orders-0/00000000000000000000.log --print-data-log
```

## Break it

Add partitions to the topic after keyed messages exist.

```
$ ./kafka-topics.sh --bootstrap-server $B --alter --topic orders --partitions 6
```

Then produce `user-a:refunded`. Which partition did it land in? Is `user-a` still in order?

```
<paste>
```

## What I learned

- ...

## Interview soundbite

> ...

## Cleanup

```
$ docker compose down -v
```
