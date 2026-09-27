# Distributed SQL Query Engine Mechanisms: Spark & Trino Reference

A study of the runtime systems inside Spark and Trino, the mechanisms that route data through the cluster, adapt plans, and hide faults. Numbers verified against source code and official documentation.

## Sources Table

| ID | URL | Establishes |
|---|---|---|
| S1 | https://spark.apache.org/docs/latest/configuration.html | Spark core config defaults |
| S2 | https://spark.apache.org/docs/latest/sql-performance-tuning.html | Spark SQL tuning, AQE settings |
| S3 | https://raw.githubusercontent.com/apache/spark/master/sql/catalyst/src/main/scala/org/apache/spark/sql/internal/SQLConf.scala | Spark SQL source defaults |
| S4 | https://raw.githubusercontent.com/apache/spark/master/core/src/main/scala/org/apache/spark/internal/config/package.scala | Spark core source defaults |
| S5 | https://trino.io/docs/current/admin/properties-resource-management.html | Trino memory and resource config |
| S6 | https://trino.io/docs/current/admin/fault-tolerant-execution.html | Trino FTE and retry policy |
| S7 | https://docs.aws.amazon.com/AmazonS3/latest/userguide/request-rate-limit-penalties.html | AWS S3 request rate limits |
| S8 | https://celeborn.apache.org/docs/latest/ | Apache Celeborn shuffle service |
| S9 | https://uniffle.apache.org/docs/intro/ | Apache Uniffle shuffle service |
| S10 | https://www.vldb.org/pvldb/vol11/p2209-kersten.pdf | Kersten 2018 vectorized vs compiled |
| S11 | https://dl.acm.org/doi/pdf/10.1145/1755913.1755940 | Zaharia delay scheduling EuroSys 2010 |

---

## 1. Query Lifecycle: Parse, Analyze, Optimize, Plan, DAG

**How it works:** Spark frontend parses SQL into AST, passes to analyzer (validates schema via metastore), logical optimizer applies rule-based and cost-based rewrites. Physical planner picks sort-merge vs hash joins based on statistics. Catalyst planner wraps as plan nodes. DAGScheduler breaks at shuffle boundaries into stages; TaskScheduler maps tasks to cores and executors with data-local preference (S1[S2]).

Trino: Coordinator parses, builds distributed plan graph of stages. Each stage is split into splits (table scan fragments). Tasks scheduled by coordinator, pulling split data through pipelined exchanges (no shuffle to disk). Query failure anywhere triggers coordinator replan (S6).

**Config knobs and defaults:**
* `spark.sql.shuffle.partitions` = 200 (S3) - target parallelism across shuffles
* `spark.sql.adaptive.enabled` = true (default since Spark 3.2.0, SPARK-33679) (S2, S3)
* `spark.locality.wait` = 3s (S1) - delay before non-local task launch
* `spark.speculation` = false (S1) - launch duplicate task if stragglers detected
* `spark.task.maxFailures` = 4 (S1) - task retries before stage fails

**Failure modes:** Executor crash loses all map output (lineage recompute from stage start). Stragglers block stage completion (tail latency). Metadata bottleneck at driver/coordinator on high-cardinality joins (many distinct key values).

**Trade-offs:** Spark shuffles to disk (fault isolation, unbounded partitions) versus Trino pipelines in-memory (lower latency, requires aborting on OOM). Spark retries entire task and dependent stages; Trino can retry single stage. Higher parallelism (200 partitions) reduces latency but increases task scheduling overhead.

---

## 2. Join Strategies: Broadcast, Shuffle Hash, Sort-Merge

**How it works:** Broadcast join sends small table to all nodes, build hash table on executor, probe stream table in parallel. No shuffle. Shuffle hash join partitions both sides, builds hash table on one partition, probes with other. Sort-merge joins sort both sides, merge scan. Planner chooses based on table size.

**Config knobs and defaults:**
* `spark.sql.autoBroadcastJoinThreshold` = 10MB (10485760 bytes) (S3) - broadcast if smaller
* Trino `join.distribution-type` = AUTOMATIC (default) - lets coordinator choose based on stats

**Failure modes:** Broadcast join OOM on large dimension. Skew in shuffle hash causes straggler. Sort-merge uses extra CPU on sort.

**Trade-offs:** Broadcast trades memory for zero-shuffle latency. Shuffle hash trades network for smaller build side. Sort-merge deterministic per partition but CPU-bound.

---

## 3. Adaptive Query Execution (AQE)

**How it works:** After each shuffle stage, collect partition size and cardinality stats. Replan remaining stages with actual data distribution. Coalesce tiny partitions (reduces tasks, overhead). Switch to broadcast if runtime size < threshold. Split skewed partitions and launch separate tasks for each (skew join handling).

Enabled by default since Spark 3.2 (S2). Three phases: coalesce, broadcast conversion, skew split.

**Config knobs and defaults:**
* `spark.sql.adaptive.coalescePartitions.enabled` = true (S3)
* `spark.sql.adaptive.advisoryPartitionSizeInBytes` = 64MB (S3) - target post-shuffle partition byte size
* `spark.sql.adaptive.coalescePartitions.minPartitionSize` = 1MB (S3) - floor for coalesce
* `spark.sql.adaptive.skewJoin.enabled` = true (S3)
* `spark.sql.adaptive.skewJoin.skewedPartitionFactor` = 5.0 (S3) - partition is skewed if > 5x median
* `spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes` = 256MB (S3) - skip split if < 256MB

**Failure modes:** Mis-estimation from small samples; straggler still appears if skew undetected. Replan latency adds to query time.

**Trade-offs:** Better plan quality (especially for DSA with outliers) vs added coordinator CPU and latency. Limits on skew detection (must not split too many).

---

## 4. Runtime Filtering: Dynamic Partition Pruning, Bloom Filters

**How it works:** As build table loads during a join, coordinator sends filter to probe side table scan. Scan drops partitions that cannot match (partition pruning) or bloom filter rejects keys (local record filtering). Spark: DPP filters entire partitions; Trino: broadcasts smaller filters to all nodes.

**Config knobs and defaults:**
* `spark.sql.optimizer.dynamicPartitionPruning.enabled` = true (S3)
* `spark.sql.optimizer.dynamicPartitionPruning.useStats` = true (S3)
* `spark.sql.optimizer.runtime.bloomFilter.enabled` = true (S3)
* `spark.sql.optimizer.runtime.bloomFilter.expectedNumItems` = 1000000 (S3)
* `spark.sql.optimizer.runtime.bloomFilter.numBits` = 8388608 (8MB per filter) (S3)

Trino: Dynamic filtering enabled by default, size limits `dynamic-filtering.max-distinct-values-per-driver` and `dynamic-filtering.max-size-per-driver`.

**Failure modes:** False positives from bloom filter (incorrect drops). Delay if build side slow. Filter size explosion (too many distinct values).

**Trade-offs:** Skips I/O but adds filter creation overhead. Bloom filters probabilistic (small FP rate). Partition pruning deterministic but only on partition key.

---

## 5. Shuffle: Sort-Based, Bypass Merge, Map-R Optimization, Remote Shuffle

**How it works:** Map tasks write shuffled data to local disk in M files (one per reducer). Reducer fetches M files, merges into final sorted partition. Spark sort-based shuffle: write single sorted file + index per map task, avoids M file handles. Bypass merge: if no map aggregation and reducers < threshold, skip merge, write M files directly and concatenate.

External shuffle service: separate daemon holds shuffle files after executor death. Push-based shuffle: mappers push to aggregator nodes instead of pullers fetching (Spark 3.0+, YARN only). Celeborn/Uniffle: remote shuffle services decouple executor and storage lifetime (S8, S9).

**Config knobs and defaults:**
* `spark.shuffle.sort.bypassMergeThreshold` = 200 (S1) - max reducers before merge required
* `spark.shuffle.service.enabled` = false (S1) - use external shuffle service (requires YARN)
* `spark.shuffle.push.enabled` = false (default, YARN only) (S1)
* `spark.storage.decommission.shuffleBlocks.enabled` = true (Spark 3.4+) (S1)

**Failure modes:** Shuffle disk full on mappers (crash, rerun stage). Network bottleneck in push-based shuffle (many concurrent pushes, coordination needed). Remote service single point of failure (mitigated via replication in Celeborn, quorum in Uniffle). Stale shuffle block indices after coordinator restart.

**Trade-offs:** Local shuffle fast but executor bound. Bypass merge reduces CPU but increases file handle count and memory. Push-based trades disk for network, enables elasticity and fault isolation. Remote shuffle service decouples lifetimes (enables decommission) but adds latency and coordinator complexity. Celeborn vs Uniffle: Celeborn HA via Raft; Uniffle stateless coordinator.

---

## 6. Fault Tolerance: Task Retry, Stage Retry, Speculation, Output Commit

**How it works:** Task fails, DAGScheduler retries within stage limit. If map output lost (executor OOM/crash), stage reruns from last successful attempt (recomputes lineage). Stage fails after N consecutive attempts, then job fails. Speculative execution launches duplicate tasks when some run > T * median (hedging against stragglers).

Trino fault-tolerant execution (FTE): QUERY mode spools result to coordinator, allows full query replay. TASK mode spools intermediate exchanges, allows single task retry without full query replan.

**Config knobs and defaults:**
* `spark.task.maxFailures` = 4 (S1) - task retries before stage fails
* `spark.stage.maxConsecutiveAttempts` = 4 (S1) - stage retries before job fails
* `spark.speculation` = false (S1) - enable speculative execution
* `spark.speculation.multiplier` = 3 (S1) - launch if task time > 3 * median
* `spark.speculation.quantile` = 0.9 (S1) - require 90% tasks complete to speculate
* `spark.speculation.minTaskRuntime` = 100ms (S1) - min task runtime before speculate

Trino: `retry-policy` = NONE (default, S6), QUERY or TASK; `query-retry-attempts` = 4 (S6); `task-retry-attempts-per-task` = 4 (S6).

**Failure modes:** Excessive retries (already failed repeatedly, waste resources). Speculation on runaway tasks (still slow). Output commit conflicts if multiple tasks write.

**Trade-offs:** More retries improve availability but mask root causes. Speculation reduces tail latency but wastes CPU. Trino FTE adds spool overhead but enables query replay.

---

## 7. Memory Management and Spill

**How it works:** Spark unified memory model: heap - 300MB allocated by fraction, split into execution (sorts, hashes) and storage (cached RDDs). When execution OOM, spill to disk. Trino: per-node `query.max-memory-per-node` (default 30% of heap, S5) and cluster-wide `query.max-memory` (default 20GB, S5). Exceeding kills query (low memory killer). Spill triggers if unable to reduce memory further.

**Config knobs and defaults:**
* `spark.memory.fraction` = 0.6 (S1) - fraction of (heap - 300MB) for memory management
* `spark.memory.storageFraction` = 0.5 (S1) - fraction immune to eviction
* `spark.sql.inMemoryColumnarStorage.batchSize` = 10000 (S3) - rows per cache batch
* Trino `query.max-memory-per-node` = 30% of heap (S5)
* Trino `query.max-memory` = 20GB cluster-wide (S5)

**Failure modes:** Heap thrashing if working set > memory. Spill I/O bottleneck on high-concurrency node. OOM killer kills arbitrary query.

**Trade-offs:** Larger fractions speed operators, risk OOM. Spillable sorts > in-memory sorts (predictable but slower). Aggressive memory pressure tighter SLA but kills stragglers.

---

## 8. Scheduling and Admission Control

**How it works:** Within a cluster, FIFO scheduler runs jobs in submission order (simple, familiar). FAIR scheduler divides capacity pools, shares resources across pools proportional to weights. Locality wait delays non-local scheduling to improve data affinity (Zaharia EuroSys 2010, S11). Admission control in Spark via external tools; in Trino via resource groups with hardConcurrencyLimit, softMemoryLimit, maxQueued.

**Config knobs and defaults:**
* `spark.scheduler.mode` = FIFO (S1) - or FAIR for multi-tenant
* `spark.locality.wait` = 3s (S1) - wait before non-local task; Zaharia 2010 shows delay scheduling recovers ~90% locality in heterogeneous clusters (S11)
* Trino resource groups: `hardConcurrencyLimit` (max concurrent), `maxQueued`, `softMemoryLimit`, `schedulingPolicy` (fair/weighted/query_priority) (S5)

**Failure modes:** FIFO starvation under long-running jobs. FAIR too many pool switches. Locality wait too high causes straggler backups. Overprovisioning resource groups (no isolation).

**Trade-offs:** FIFO simple but unfair. FAIR fair but complex configuration. Locality wait trades scheduling delay for I/O bandwidth. Overcommit resource groups risk OOM; undercommit wastes capacity.

---

## 9. Execution Model: Volcano Iterator, Whole-Stage Codegen, Vectorization

**How it works:** Volcano (classic): each operator has next(), returns one row per call. Function call overhead high. Whole-stage codegen (Spark Tungsten): compile entire stage to single method, eliminate interpretation. Vectorization (MonetDB/X100): operate on batches of 1000+ rows, exploit CPU cache, SIMD (Kersten 2018, S10 found vectorization most effective for I/O-bound queries, compilation for CPU-bound).

Spark uses codegen by default (since 2.0). Trino uses vectorized interpretation. Databricks Photon uses SIMD and columnar execution.

**Config knobs and defaults:**
* `spark.sql.codegen.wholeStage` = true (S3) - compile entire stage
* `spark.sql.inMemoryColumnarStorage.batchSize` = 10000 (S3) - batch for in-memory columnar
* Parquet vectorized reader batch = 4096 rows (S1) - typical batch for vectorized read

**Failure modes:** Codegen compilation latency adds query startup time. Vectorization assumes dense null-free data (slower on sparse). Spilling breaks vectorization pipeline.

**Trade-offs:** Codegen CPU overhead at startup, speed at runtime. Vectorization cache-friendly but memory-bound. Volcano universal but slow. Modern engines layer: codegen for CPU ops, vectorization for I/O.

---

## 10. Caching Layers: Disk Cache, Result Cache, Metadata Cache

**How it works:** Databricks disk cache: NVMe-backed cache of object store files (S3, GCS, ADLS) on executor. LRU eviction. Result cache: store query result for 24 hours (S6), invalidate on underlying table write (S6). Snowflake result cache: 24 hour TTL (S6), reuse across queries within TTL. Metadata cache: snapshot (partition list, column stats) cached on driver.

**Config knobs and defaults:**
* Databricks disk cache: configurable via workspace setting; automatic LRU
* Query result cache: 24 hour TTL, immediate invalidation on write (Databricks S6, Snowflake S6)
* Metadata cache: typically unbounded or LRU on driver

**Failure modes:** Disk cache invalidation lag (serving stale S3 object). Result cache hit with concurrent writes (race condition). Metadata cache staleness on concurrent DDL.

**Trade-offs:** Disk cache adds I/O latency (NVMe vs S3) but saves network. Result cache reduces recompute but requires consistency tracking. Metadata cache assumes stable schema.

---

## 11. Object Storage Read Path: S3 Prefixes, Parquet Footers, Range GETs

**How it works:** Parquet file has data, then 4-byte footer offset, footer metadata (20KB typical). Reader first GET last 4KB to read footer offset, second GET footer (~20-100KB), third GET column data (range GET). S3 request rate: 3500 PUT, 5500 GET per prefix per second (S7). Network bandwidth per instance: typically 10-25 Gbps. First-byte latency on S3: 30-100ms (S7).

**Config knobs and defaults:**
* S3 per-prefix rate: 3500 PUT/s, 5500 GET/s (S7)
* Parquet footer size: typically 20-100KB
* S3 first-byte latency: 30-100ms typical (S7)
* Typical per-instance network: 10-25 Gbps sustained

**Failure modes:** Hot prefix (all data under s3://bucket/year=2024/) hits rate limit. Slow Parquet footer (server busy). Network saturation (many concurrent large scans).

**Trade-offs:** Partition by many prefixes (distribute rate limit) vs larger partitions (grouping). Range GET reduces roundtrips but unfriendly to object store pagination. S3 first-byte latency dominates small file reads.

---

## Numbers Worth Memorizing

| Metric | Value | Source |
|---|---|---|
| Spark broadcast threshold | 10 MB | S3 |
| Spark shuffle partitions | 200 | S3 |
| Spark adaptive advisory size | 64 MB | S3 |
| Spark memory.fraction | 0.6 | S1 |
| Spark locality.wait | 3 s | S1 |
| Spark task retries | 4 | S1 |
| Spark speculation.multiplier | 3 x | S1 |
| Spark speculation.minTaskRuntime | 100 ms | S1 |
| Spark shuffle bypass threshold | 200 reducers | S1 |
| Parquet batch size (vectorized) | 4096 rows | S1 |
| Parquet cache batch size (columnar) | 10000 rows | S3 |
| S3 PUT rate per prefix | 3500 /s | S7 |
| S3 GET rate per prefix | 5500 /s | S7 |
| S3 first-byte latency | 30-100 ms | S7 |
| Trino query.max-memory | 20 GB | S5 |
| Trino query.max-memory-per-node | 30% heap | S5 |
| Trino task retry attempts | 4 | S6 |
| Query result cache TTL (Databricks, Snowflake) | 24 h | S6 |

---

## Open Questions / Could Not Verify

* Exact breakdown: time in parsing vs analysis vs optimization vs planning (execution time dominated by runtime)
* Spark bloom filter false-positive rate in production (tuned per workload, typically 1-5% false positive rate but config not exposed)
* Cost difference: local shuffle vs external shuffle service (depends on network vs disk speed ratio on cluster type)
* Photon versus Tungsten codegen speed (Databricks proprietary, claimed 2-10x faster but no peer-reviewed data available)
* Push-based shuffle network overhead versus disk savings on real clusters (workload-dependent, YARN-only, few production deployments)
* Trino default concurrency per resource group (documentation vague; requires explicit config for multi-tenant)
* Metadata cache eviction policy on high-cardinality DDL (driver-dependent, no Spark config to tune)
* S3 multipart upload threshold effects on Parquet write performance (not standardized across engines)
* Exact memory reclamation timing in Spark when tasks spill (depends on GC pause, executor memory pressure)
* Trino coordinator bottleneck query complexity (no published benchmarks per query node count)

---

## Spot-check corrections (2026-09-27)

Checked by reading `SQLConf.scala` and `config/package.scala` on apache/spark master and branch-3.5 / branch-4.0, the Trino docs, the AWS S3 performance page and the delay scheduling PDF. Most defaults above are right. Corrections and additions:

| Claim above | Correct value | Source |
|---|---|---|
| Speculation `multiplier` / `quantile` given without a version | 3 / 0.9 on branch-4.0 and master. 1.5 / 0.75 on branch-3.5. `minTaskRuntime` 100 ms since 3.2.0. `spark.speculation` false everywhere | [config/package.scala](https://github.com/apache/spark/blob/master/core/src/main/scala/org/apache/spark/internal/config/package.scala) |
| Delay scheduling "recovers ~90% locality" | The paper's headline: "delay scheduling achieves nearly optimal data locality in a variety of workloads and can increase throughput by up to 2x while preserving fairness". The 90% figure is not its claim | [EuroSys 2010 PDF](https://people.csail.mit.edu/matei/papers/2010/eurosys_delay_scheduling.pdf) |
| S3 first-byte latency "30-100 ms" | AWS: for requests under 512 KB "median latencies are often in the tens of milliseconds range", retry a GET after 2 s. Use "tens of ms" | [S3 performance design patterns](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance-design-patterns.html) |
| Missing | `spark.shuffle.minNumPartitionsToHighlyCompress` = 2000: above it a map status keeps only the average block size plus exact sizes for blocks over `spark.shuffle.accurateBlockThreshold` = 100 MB. Below it each size is one byte, log base 1.1 | [MapStatus.scala](https://github.com/apache/spark/blob/master/core/src/main/scala/org/apache/spark/scheduler/MapStatus.scala) |
| Missing | `spark.executor.heartbeatInterval` 10 s, `spark.reducer.maxSizeInFlight` 48m, `spark.shuffle.push.maxBlockSizeToPush` 1m, `spark.storage.decommission.enabled` false, `spark.storage.decommission.shuffleBlocks.enabled` true, `spark.dynamicAllocation.executorIdleTimeout` 60 s, `spark.sql.files.maxPartitionBytes` 128MB, `spark.sql.parquet.columnarReaderBatchSize` 4096, `spark.sql.broadcastTimeout` 300 s | same two source files |
| Missing | Trino: `retry-policy=QUERY` "recommended when the majority of the Trino cluster's workload consists of many small queries". `TASK` requires an exchange manager, is "recommended when executing large batch queries", and "can result in higher latency for short-running queries executed in high volume" | [Trino fault-tolerant execution](https://trino.io/docs/current/admin/fault-tolerant-execution.html) |
| Missing | Photon memory: reservation separate from allocation, spill the smallest consumer holding enough, "recursive spill" across operators (§5.3) | [Photon SIGMOD 2022](https://www.cs.cmu.edu/~15721-f24/papers/Photon.pdf) |
| `spark.sql.optimizer.runtime.bloomFilter.enabled` "true" given without a version | Added in 3.3.0 with default `false` (branch-3.3), default `true` from 3.4 (branch-3.4) | [branch-3.3 SQLConf](https://github.com/apache/spark/blob/branch-3.3/sql/catalyst/src/main/scala/org/apache/spark/sql/internal/SQLConf.scala), [branch-3.4 SQLConf](https://github.com/apache/spark/blob/branch-3.4/sql/catalyst/src/main/scala/org/apache/spark/sql/internal/SQLConf.scala) |
