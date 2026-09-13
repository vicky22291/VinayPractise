# Apache Kafka Deep Dive Series

<!-- nav:start -->
**[← All systems](../README.md)** · [Start here: 00 Overview](kafka-00-overview.md) · [Pattern catalogue](patterns.md)
<!-- nav:end -->

**Series baseline: Apache Kafka 4.3** (4.3.0 released 2026-05-22; latest patch 4.3.1
released 2026-06-25). Every default, config name and KIP status was verified against
that release's source tree rather than quoted from memory.

Companion to the Kubernetes series in the same project; same 12-section structure,
same `[documented]` / `[inferred]` / `[unverified]` marking discipline, same mermaid
conventions.

## Contents

| File | Covers |
|---|---|
| [`kafka-00-overview.md`](kafka-00-overview.md) | Reading map, architecture, end-to-end trace, the ideas that generalise |
| [`kafka-01-log-storage.md`](kafka-01-log-storage.md) | Segments, record batch v2 format, indexes, retention, compaction, tiered storage |
| [`kafka-02-replication-isr.md`](kafka-02-replication-isr.md) | High watermark, ISR, leader epochs, ELR, unclean election, reassignment |
| [`kafka-03-kraft-controller.md`](kafka-03-kraft-controller.md) | Pull-based Raft, `__cluster_metadata`, QuorumController, broker lifecycle |
| [`kafka-04-producer.md`](kafka-04-producer.md) | Accumulator, sticky partitioning, idempotence, transactions, KIP-890 |
| [`kafka-05-consumer-rebalance.md`](kafka-05-consumer-rebalance.md) | Fetch mechanics, offsets, KIP-848, share groups, CoordinatorRuntime |
| [`kafka-06-broker-request-pipeline.md`](kafka-06-broker-request-pipeline.md) | Threading, timing-wheel purgatory, request phases, quotas, security |
| [`kafka-07-streams-connect.md`](kafka-07-streams-connect.md) | Topologies, state stores, KIP-441/1071, Connect, EOS sources, MirrorMaker 2 |
| [`kafka-08-scale-and-operations.md`](kafka-08-scale-and-operations.md) | Scale envelope, metric reference, tuning, runbooks, cost model |
| [`kafka-09-version-delta.md`](kafka-09-version-delta.md) | Release timeline, the 4.0 wall, maturity matrix, errata, upgrade playbooks |
| [`patterns.md`](patterns.md) | Cross-system pattern catalogue, now with a Kafka column beside Kubernetes |

## Reading order

01 → 02 → 04 + 05 → 06 → 03 → 07 / 08, with 09 kept open whenever quoting a number.
Section 7 of the overview explains why.

## Diagrams

112 mermaid diagrams, recoloured to this repo's legend in
[`../../templates/color-legend.md`](../../templates/color-legend.md). The
bundle shipped with a *component family* palette; the repo legend is a *role*
palette. The mapping applied:

| Original family | Now | Why |
|---|---|---|
| Client: producers, consumers, Streams, Connect | `client` blue | same meaning |
| Log storage: UnifiedLog, segments, indexes, cleaner | `store` purple | durable, not a losable cache |
| Replication: ReplicaManager, fetchers, ISR, epochs | `service` green | stateless compute |
| Request path: SocketServer, KafkaApis, purgatory, quotas | `service` green | stateless compute |
| Coordinators: group, transaction, share | `queue` cyan | backed by internal compacted topics |
| Control plane: QuorumController, `__cluster_metadata` | `service` green | **red is reserved for bottlenecks** |
| External: page cache, disks, object stores | `external` grey dashed | outside the broker process |

Three families collapse into green, because the role legend has no separate
role for "control plane" or "request path". That is the cost of the mapping.

**Red now means one thing: the thing that breaks first.** In this folder it is
on exactly two nodes:

- `QuorumController` (`kafka-03`), single-threaded `KafkaEventQueue`.
- `KafkaRequestHandlerPool` (`kafka-08`), `num.io.threads`, the first ceiling
  on almost every cluster.

All 286 diagrams across the three systems were re-validated by rendering with
mermaid-cli 11 after the recolour.
