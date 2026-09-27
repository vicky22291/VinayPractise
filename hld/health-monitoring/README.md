# Server-health monitoring and alerting

> One-line answer: an agent on every server samples ~100 health series every 10 s, runs local health checks, and pushes to a region-local metrics stack (stateless distributors, ingesters holding the last 2 h in memory with RF = 3 across the region's 3 clusters, 2 h blocks to object storage), while a separate tiny heartbeat every 5 s goes to 3 liveness replicas; a host is declared dead only when 2 of 3 replicas miss it and probes from 3 other racks confirm, and a topology correlator folds a rack, PDU or switch failure into one event before an HA alert router groups, inhibits and pages with a dedup key. A single dead server is routine (30 to 80 a day at 500k servers) and goes to automated drain and repair, not to a human. The monitoring stack lives in each region with no dependency on the systems it watches, and is itself watched from another region plus an external dead man's switch. The red node is the ingester tier, because a cardinality explosion there blinds dashboards and alert rules at the same time.

Tier 3, problem #26 in [`hld/README.md`](../README.md). Reported as a Google L6 round. Closest public breakdown: [Hello Interview, Metrics Monitoring](https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring). Reusable blocks: [`../../concepts/time-series-db.md`](../../concepts/time-series-db.md) (storage engine, compression, Mimir architecture, cardinality), [`../../concepts/gossip-protocol.md`](../../concepts/gossip-protocol.md) (failure detectors, alert router HA), [`../../concepts/sharding.md`](../../concepts/sharding.md) (series hash ring), [`../../concepts/replication-and-quorums.md`](../../concepts/replication-and-quorums.md) (RF = 3, write quorum 2), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md) (dedup key on pages), [`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md) (per-tenant series limits), [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md) (why we do not put Flink on the alert path).

## Problem statement (as given)

Reconstructed from reports, there is no verbatim public prompt:
- Design a system that monitors the health of the servers in a large fleet across many datacenters.
- Collect health metrics (CPU, memory, disk, network, process liveness) and show them on dashboards.
- Detect when a server is down or unhealthy and alert the right on-call team.
- Let teams define their own alert rules.

The index row lists the concepts under test: time-series ingestion, cardinality, fault detection, alert dedup.

## What the web research changed

Sources checked on 2026-09-27. Research notes in [`research/`](research/).

| Change | Requirement | Evidence |
|---|---|---|
| KEEP | The four Hello Interview FRs (ingest, dashboards, alert rules, notifications) and its scale: 500k servers, 100 series each every 10 s, 5M samples/s | [Hello Interview](https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring) public outline |
| KEEP | Its four deep dives: weeks-long dashboard queries, alerts under 1 minute, availability during spikes and failures, cardinality explosion | Same page, "Potential Deep Dives" |
| ADD | **Detect dead and unhealthy servers with no rule written.** Liveness is not a threshold on a metric: a dead server sends no metrics, so no rule on its metrics can fire | The "server-health" half of the prompt and the index row ("fault detection") |
| ADD | **One page per failure, not per server.** Group, inhibit, dedup across alert router replicas | Index row ("alert dedup"). Google SRE: max **2 incidents per 12-hour shift** ([SRE book, Being On-Call](https://sre.google/sre-book/being-on-call/)) |
| ADD | **Single-server failure is routine.** Route it to automated drain and repair, page only on correlated failures and symptoms | Jeff Dean, LADIS 2009: servers fail at 2 to 4% a year, and a new cluster's first year has ~1,000 machine failures, ~20 rack failures (40 to 80 machines each), ~1 PDU failure (500 to 1,000 machines) ([slides](https://www.cs.cornell.edu/projects/ladis2009/talks/dean-keynote-ladis2009.pdf)) |
| ADD | **Monitoring must survive what it monitors.** No hard dependency on the storage systems it watches, alerting evaluated close to the data | [Monarch, VLDB 2020](https://www.vldb.org/pvldb/vol13/p3181-adams.pdf) §2: in memory, avoids Bigtable, Spanner and Colossus on the alerting path to avoid a circular dependency |
| UPDATE | "1 GB/s of raw ingestion" (Hello Interview, 100 to 200 B per point) becomes **~100 MB/s on the wire and ~7 MB/s stored**. Bytes are not the crux. Series count and correct verdicts are | Batched protobuf plus snappy on the wire, ~1.4 B per sample stored ([Gorilla, VLDB 2015](https://www.vldb.org/pvldb/vol8/p1816-teller.pdf)) |
| UPDATE | "Alerts under 1 minute" becomes two numbers: **host hard-down verdict in 30 s p99, correlated-failure page in 60 s p99**. Threshold rules fire within 15 s of their `for` window closing | Kubernetes, for scale: `node-monitor-grace-period` 50 s, eviction after 5 min ([kube-controller-manager](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-controller-manager/)) |
| UPDATE | Retention made concrete: **raw 15 days, 5 min rollups 90 days, 1 h rollups 13 months** | DesignGurus uses raw 7 d, 1 min 30 d, 1 h 1 y ([post](https://designgurus.substack.com/p/design-a-metrics-and-monitoring-system)). We keep raw longer because 2 weeks of incident lookback is cheap (9 TB) |
| DELETE | Below the line: logs, traces, ML anomaly detection (seam named), per-container metrics | Hello Interview below-the-line list |

## Final requirements

Functional:
1. Ingest health metrics from every server: ~100 series per server every 10 s.
2. Query and visualize metrics on dashboards with filters, aggregations and time ranges from 1 hour to 13 months.
3. Teams define alert rules: threshold over a time window, owned and versioned.
4. Detect dead and unhealthy servers automatically, with no rule written, and hand them to repair.
5. Notify the right on-call once per problem (PagerDuty, Slack, email, ticket), with grouping, dedup, silences and escalation.

Non-functional: 500k servers, 5M samples/s, 50M active series. Host hard-down verdict p99 30 s, correlated-failure page p99 60 s. Alert path 99.99% per region, dashboards 99.9%. No page caused by a partition on the monitoring side. At most 2 pages per 12 h shift per team on average. Dashboards p99 under 1 s for 6 h panels, under 5 s for 30 days.

## What interviewers probe

1. Push or pull? And how do you find out a server is dead if it pushes nothing?
2. A server stops heartbeating. Is it dead, or is the network between it and you broken? How long before you decide?
3. A PDU fails and 800 servers go dark at once. How many pages does on-call get?
4. You run 3 alert router replicas for HA. Why does on-call not get 3 pages?
5. Someone ships a metric with a `request_id` label. What happens to your ingesters?
6. Who monitors the monitoring system? What if the whole region's monitoring is down?
7. A server answers pings but drops 50% of its packets. Do you catch it?
8. Your auto-remediation drains dead servers. A bad health check marks 30% of a cluster unhealthy. What stops it from draining the cluster?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one diagram built one requirement at a time, deep dives that change the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/failure-detection.md`](deep-dives/failure-detection.md) | Heartbeats, observer quorum, confirmation probes, pipeline-relative silence, phi accrual and why we do not need it, gray failure |
| [`deep-dives/correlation-and-alert-storms.md`](deep-dives/correlation-and-alert-storms.md) | Failure-domain tree, one event per rack or PDU, inhibition, flapping, remediation safety budget |
| [`deep-dives/alert-routing-and-dedup.md`](deep-dives/alert-routing-and-dedup.md) | Alert router HA, gossiped notification log, peer timeout, dedup key, escalation, silences |
| [`deep-dives/alert-evaluation-and-latency.md`](deep-dives/alert-evaluation-and-latency.md) | Rule evaluators, standing queries at 15 s, `for` state restore, edge checks in the agent, why not Flink |
| [`deep-dives/ingestion-and-cardinality.md`](deep-dives/ingestion-and-cardinality.md) | The red node: agent WAL, distributor, ring, RF = 3, admission window, newest-first catch-up, series limits, why not Kafka |
| [`deep-dives/query-and-retention.md`](deep-dives/query-and-retention.md) | Downsampling, recording rules, query frontend split and cache, query limits |
| [`deep-dives/meta-monitoring-and-region-loss.md`](deep-dives/meta-monitoring-and-region-loss.md) | Who watches the watcher, dependency rules, cross-region watchers, dead man's switch, region loss |
| [`research/`](research/) | Three web surveys with spot-check corrections. Input to the files above |
| `health-monitoring.excalidraw` | My drawing. Missing until I draw it |
