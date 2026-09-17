# Multi-region metadata store with linearizable writes

> One-line answer: shard the keyspace into ranges keyed by `(tenant, path)`, make each range its own Raft group of 5 voters placed 2 + 2 + 1 across 3 regions with the leader pinned to the tenant's home region; a write commits after the leader has one remote ack (one cross-region round trip, about 70 ms); the leader serves linearizable reads under a clock-bounded lease with zero round trips; stale-tolerant readers use follower reads at a closed timestamp in their own region; a lost region leaves 3 of 5 voters, so every group re-elects inside the election timeout and epoch-fenced leases stop the dead region's old leaders from serving stale data; every name check and version check is a compare-and-swap inside one Raft group, so there is no cross-shard 2PC on the hot path.

Tier 2, problem #19 in [`hld/README.md`](../README.md). Asked at Databricks (Unity Catalog metastore style, "catalog service across regions") and Google ("design Spanner", "global config store", "lock service"). Building blocks: [`concepts/raft.md`](../../concepts/raft.md), [`concepts/paxos.md`](../../concepts/paxos.md), [`concepts/replication-and-quorums.md`](../../concepts/replication-and-quorums.md), [`concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md), [`concepts/mvcc-and-isolation.md`](../../concepts/mvcc-and-isolation.md), [`concepts/distributed-transactions.md`](../../concepts/distributed-transactions.md), [`concepts/sharding.md`](../../concepts/sharding.md). See [`research/`](research/) for sources.

## Problem statement (as asked)

Design a metadata store used by a data platform across three or more cloud regions. Metadata means catalog objects: schemas, tables, views, column definitions, ACLs, cluster and job configurations, secrets references. Clients in every region read it on every query and write it on every DDL, permission change, or job deploy. Writes must be linearizable: a `CREATE TABLE` in one region and the same name in another region must not both succeed, and a client must never read an older version after it has observed a newer one. The store must survive the loss of a whole region with no acknowledged write lost.

Say this out loud: "metadata" is small (bytes to a few KB per object), read-heavy (100:1 or more), and correctness-critical. That combination is exactly what consensus is for. Nobody runs Raft for petabytes; everybody runs it for the catalog that points at them.

## Functional requirements

Core:
- `get(key)`, `put(key, value, expected_version)`, `create(key, value)` that fails if the key exists, `delete(key, expected_version)`. Every write is a compare-and-swap on a version.
- `list(prefix, page)` over a namespace, consistent as of a single point in time.
- `txn([ops])` over a handful of keys inside one tenant (rename = delete old name + create new name atomically).
- `watch(prefix, from_version)` so caches and schedulers learn about changes without polling.

Below the line (say it out loud):
- Cross-tenant transactions. Tenants are the shard boundary; we refuse to build 2PC across them.
- Full-text or secondary-index search over metadata. A separate index built from the watch stream.
- Blob storage. Values above 64 KB are rejected; large artifacts go to object storage and the key holds the pointer.
- Multi-cloud. Three regions in one provider.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 1 B keys, average 1 KB, 1 TB live plus versions. 500k reads/s, 5k writes/s aggregate, 10x on Monday 9am in each region |
| Consistency | Linearizable writes. Reads linearizable by default. An explicit `stale_ok(max_age)` read mode for caches and dashboards |
| Read latency | Linearizable read from the home region p99 < 10 ms. Stale read from any region p99 < 5 ms |
| Write latency | p99 < 200 ms from the home region, p99 < 400 ms from a remote region |
| Availability | 99.99% for writes, 99.999% for stale reads. One region can be lost with RPO = 0 and RTO < 30 s, no operator action |
| Durability | Every acknowledged write on disk in 2 regions before the ack |
| Growth | Adding a fourth region moves no data and needs no downtime |

## What interviewers probe (the ladder)

1. Why not one Raft group for everything? What breaks first: throughput, key count, or the leader?
2. Three regions, three replicas, one per region. A region dies. Do you still have quorum? Now one more node dies. Now what?
3. A write from Frankfurt to a table whose home is Virginia. Walk the packets. How many cross-region round trips?
4. A read in Virginia right after that write. How do you serve it linearizably without a cross-region round trip? What clock assumption did you just make?
5. Virginia dies at 09:00:00. Second by second, when does the last write commit, when does a new leader exist, what do clients in Frankfurt see, what do clients still inside Virginia see?
6. The old Virginia leader comes back at 09:03 with a working network but a paused process. It thinks it is still leader. What stops it from answering a read?
7. Two clients in two regions both `CREATE TABLE sales.orders`. Show the exact step where one of them fails.
8. `list` under a prefix with 5 M keys. Where does it run, what does it cost, is it a consistent snapshot?
9. One tenant has 50 M tables and 40% of the write traffic. What is hot, and what is the fix?
10. How do you migrate from today's single-region Postgres with zero downtime and a rollback path?
11. What pages at 3am, and how do you know the store is actually linearizable in production?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/quorum-placement-and-region-loss.md`](deep-dives/quorum-placement-and-region-loss.md) | 3 vs 5 voters, 2 + 2 + 1, witnesses, what each layout survives, the region-loss timeline |
| [`deep-dives/write-path-and-leader-placement.md`](deep-dives/write-path-and-leader-placement.md) | Home region, leaseholder vs Raft leader, lease transfer, the one-RTT commit, CAS and create-if-absent |
| [`deep-dives/read-paths-and-clocks.md`](deep-dives/read-paths-and-clocks.md) | Lease reads, ReadIndex, follower reads at a closed timestamp, HLC vs TrueTime, what each read mode assumes |
| [`deep-dives/fencing-stale-leaders-and-partitions.md`](deep-dives/fencing-stale-leaders-and-partitions.md) | Epoch leases, pre-vote, check-quorum, the paused-leader problem, clients inside a dead region |
| [`deep-dives/sharding-transactions-and-hot-tenants.md`](deep-dives/sharding-transactions-and-hot-tenants.md) | Range splits, the directory, single-shard transactions by key design, when 2PC over Raft groups is unavoidable, hot tenant |
| [`deep-dives/migration-and-operations.md`](deep-dives/migration-and-operations.md) | Postgres to this store with dual writes and a rollback point, adding a region, Jepsen-style verification, the runbook |
| [`research/`](research/) | Raw web research notes with source links and spot-check corrections. Input to the files above, not study material |
| `multi-region-metadata-store.excalidraw` | My drawing. Missing until I draw it |
