# Kafka

> One-line answer: a partitioned, replicated, append-only log. Producers append, consumer groups read in parallel, offsets track progress.

**Concept links:** `concepts/kafka.md`, `popular_systems_deepdive/kafka/`
**Version practised:** Apache Kafka 4.0 (KRaft, no Zookeeper)

## Start / stop

```
$ cd tool-practise/kafka
$ docker compose up -d
$ docker exec -it kafka bash          # CLI tools live in /opt/kafka/bin
$ docker compose down -v
```

Inside the container, `B=localhost:19092` is the broker address. From the host use `localhost:9092`.

## CLI cheat-sheet

All scripts are in `/opt/kafka/bin/` inside the container.

| Command | What it does |
|---|---|
| `kafka-topics.sh --bootstrap-server $B --create --topic t --partitions 3 --replication-factor 1` | create topic |
| `kafka-topics.sh --bootstrap-server $B --describe --topic t` | leaders, ISR per partition |
| `kafka-topics.sh --bootstrap-server $B --list` | list topics |
| `kafka-console-producer.sh --bootstrap-server $B --topic t --property parse.key=true --property key.separator=:` | produce `key:value` lines |
| `kafka-console-consumer.sh --bootstrap-server $B --topic t --from-beginning --property print.partition=true --property print.offset=true` | consume with metadata |
| `kafka-console-consumer.sh --bootstrap-server $B --topic t --group g1` | consume as part of group `g1` |
| `kafka-consumer-groups.sh --bootstrap-server $B --describe --group g1` | lag per partition |
| `kafka-consumer-groups.sh --bootstrap-server $B --group g1 --reset-offsets --to-earliest --topic t --execute` | rewind a group |
| `kafka-producer-perf-test.sh --topic t --num-records 100000 --record-size 100 --throughput -1 --producer-props bootstrap.servers=$B acks=1` | throughput test |
| `kafka-dump-log.sh --files /tmp/kraft-combined-logs/t-0/00000000000000000000.log --print-data-log` | read the raw segment |
| `kafka-configs.sh --bootstrap-server $B --alter --entity-type topics --entity-name t --add-config retention.ms=60000` | change retention |

## Exercises

| # | File | Topic | Status |
|---|---|---|---|
| 01 | [`exercises/01-topics-and-partitions.md`](exercises/01-topics-and-partitions.md) | Create topic, produce with and without keys, see which partition each message lands in. | todo |
| 02 | [`exercises/02-consumer-groups.md`](exercises/02-consumer-groups.md) | Two consumers in one group, kill one, watch the rebalance and the lag. | todo |
| 03 | [`exercises/03-offsets-and-replay.md`](exercises/03-offsets-and-replay.md) | Commit, reset, replay from the beginning. What at-least-once looks like. | todo |
| 04 | [`exercises/04-acks-and-throughput.md`](exercises/04-acks-and-throughput.md) | `acks=0/1/all`, batching, `linger.ms`. Measure records/sec for each. | todo |
| 05 | [`exercises/05-replication-broker-loss.md`](exercises/05-replication-broker-loss.md) | 3 brokers, RF=3, kill the leader, watch ISR shrink and a new leader elected. | todo |

## Break-it ideas

- Kill a consumer mid-batch. Restart it. Count the duplicates.
- Set `retention.ms=10000` and watch messages vanish.
- Produce with `acks=0`, kill the broker immediately, count what survived.
- Produce 1M records with `linger.ms=0` vs `linger.ms=50`. Compare throughput.
