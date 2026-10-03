# MapReduce Engine Mechanisms: Defaults and Configuration

This survey captures exact numeric defaults from source code and official documentation for Google MapReduce, Hadoop, and Spark. Every number is paired with a URL and primary source.

## Overview

MapReduce engines optimize along seven axes: input partitioning, in-memory buffering, network bandwidth, fault recovery, straggler mitigation, data locality, and skew mitigation. Each axis involves trade-offs between resource usage, latency, and reliability.

Default configurations reflect design decisions made at Google (MapReduce paper, 2004) and battle-tested in production clusters handling petabytes daily. Defaults balance safety, performance, and operational simplicity. Understanding these defaults is critical for staff-level design: knowing what to change, when to change it, and why.

This survey is organized by subsystem, covering both Hadoop (Java MapReduce) and Spark (Scala Catalyst SQL engine) with special attention to mechanisms that address production concerns: stragglers, skew, fault tolerance, and network efficiency.

## 1. Map Side: Input Splits and In-Memory Sort

**Input Split Calculation**

Hadoop FileInputFormat computes split size as: `max(minSize, min(maxSize, blockSize))`. [1]

HDFS default block size is 134,217,728 bytes (128 MB). [2] This determines the natural split boundary; files smaller than blockSize are never split by default.

**In-Memory Sort Buffer**

`mapreduce.task.io.sort.mb`: 100 MB (default). [3] This is the JVM heap size reserved for the in-memory circular buffer that accumulates key-value pairs from the map function before spilling to disk. This buffer is the first-level aggregation point; output is sorted by partition and then by key within partition.

`mapreduce.map.sort.spill.percent`: 0.80 (default). [3] Spill to disk is triggered when the buffer reaches 80% of 100 MB capacity (i.e., ~80 MB of data). Spill happens asynchronously while the map task continues writing to the remaining 20% buffer space. This overlaps computation and I/O.

`mapreduce.task.io.sort.factor`: 10 (default). [3] During the merge phase after the map completes and all spills finish, up to 10 spill files are merged in a single pass. If more than 10 spills exist, multiple merge passes occur. Each pass reduces spill count by a factor of 10, so 100 spills require 2 merge passes. Increasing this value reduces merge passes but increases memory pressure during merge.

**Map Output Compression**

`mapreduce.map.output.compress`: false (default). [3] Compression can reduce network bandwidth but increases CPU cost.

**Combiner and Partitioner**

HashPartitioner: partition assignment is `(key.hashCode() & Integer.MAX_VALUE) % numPartitions`. [4] No repartitioning occurs after the first level. All output for the same partition is sent to the same reducer.

Combiner runs in-memory on each map task after sort and merge, reducing output that will be shuffled. Optional but highly effective for associative and commutative operations (count, sum, max, min). Combiners reduce network bandwidth and intermediate data stored on disk.

## 2. Shuffle: Reducer Fetch and Merge

**Slow Start: When Reducers Begin**

`mapreduce.job.reduce.slowstart.completedmaps`: 0.05 (default). [5] Reducers may begin fetching map output after only 5% of maps complete, overlapping map and reduce phases.

This parameter significantly impacts job latency. When delayed to 90% map completion, reduce time increased from 116s to 139s. [5]

**Parallel Fetch Threads**

`mapreduce.reduce.shuffle.parallelcopies`: 5 (default). [5] Each reducer spawns 5 concurrent HTTP threads to fetch partitions from multiple mappers simultaneously.

**Shuffle Buffer and Merge on Reduce Side**

`mapreduce.reduce.shuffle.input.buffer.percent`: 0.70 (default). [3] Heap space reserved for fetch buffers; 70% of reducer heap can hold in-flight data.

`mapreduce.reduce.shuffle.memory.limit.percent`: 0.25 (default). [3] In-memory merged data is capped at 25% of heap; overflow spills to disk.

`mapreduce.reduce.shuffle.merge.percent`: 0.66 (default). [3] Merge occurs when in-memory data reaches 66% of the memory limit.

`mapreduce.reduce.merge.inmem.threshold`: 1000 (default). [3] Merge triggers if the number of in-memory segments exceeds 1000.

**Spark Sort-Based Shuffle**

`spark.reducer.maxSizeInFlight`: 48 MB (default). [6] Maximum size of map outputs fetched simultaneously per reduce task.

`spark.shuffle.file.buffer`: 32 KB (default). [6][7] In-memory buffer per output stream; reduces disk seeks when writing intermediate shuffle files.

`spark.shuffle.sort.bypassMergeThreshold`: 200 (default). [6] Skips sort-merge if no map-side aggregation and partition count does not exceed this threshold.

**External Shuffle Service**

`spark.shuffle.service.enabled`: false (default). [6] When true, defers cleanup of shuffle blocks until job completion, allowing task decommissioning before job ends.

`spark.shuffle.service.port`: 7337 (default). [6] Port for external shuffle service daemon on NodeManager.

**Remote Shuffle Services**

Push-based shuffle services decouple shuffle from executor lifecycle: mappers push data to centralized servers rather than storing locally and having reducers pull. This enables executor decommissioning, better resource utilization, and faster straggler mitigation.

Uber RemoteShuffleService (RSS): uses ZooKeeper to register live servers, achieving 99.99% reliability with 95% reduction in container failures due to shuffle. [8] Mappers push to RSS servers; reducers fetch from RSS. Service registry tracks healthy instances. Driver assigns shuffle servers based on latency and partition count.

Apache Celeborn: elastic shuffle service supporting Spark 3.0-4.2 and Flink 1.18-2.3, stores data in memory, local disk, HDFS, or object store. [9] Master manages resources via Raft consensus; workers process read-write requests and merge data per reducer; client split into LifecycleManager (control plane) and ShuffleClient (data plane).

Riffle (EuroSys 2018): merge servers achieve ~100 MB/s sequential write speed. On 100-node cluster with 10 Gbps links, reduces small-block I/O by merging partitions block-by-block. Reduces reducer fetch from tens of thousands of small blocks to hundreds of large merged blocks. [10]

Magnet (VLDB 2020): push-based shuffle mechanism improves Spark job latency by nearly 30%. Deployed at LinkedIn handling petabytes daily. [11] Mappers push to Magnet shuffle services where data is merged per partition. Reducers fetch merged data.

## 3. Fault Tolerance: Task Attempts and Output Commit

**Task Attempts**

`mapreduce.map.maxattempts`: 4 (default). [3] Maps are retried up to 4 times before failing the job.

`mapreduce.reduce.maxattempts`: 4 (default). [3] Reducers are retried up to 4 times.

`mapreduce.task.timeout`: 600,000 ms (10 minutes, default). [3] If a task heartbeat is not received within this period, the task is marked as failed and rescheduled.

**Output Commit Strategy**

`mapreduce.fileoutputcommitter.algorithm.version`: 2 (default). [3] Algorithm v1 requires rename at task commit (atomic); v2 renames at job commit but risks visibility of partial output.

FileOutputCommitter v2: commitTask renames temp task directory to final output; recoverTask checks for previous attempts; commitJob deletes temp and writes _SUCCESS. [12] The v2 algorithm is more efficient (no rename at job commit) but is not safe: output may be visible to readers before job completion if tasks commit independently.

S3A committers address the M x R small-block problem on S3 by staging commits and atomic manifest writes instead of slow directory renames (which are not atomic on S3). [13] S3A staging committer writes to a staging directory and atomically moves output to final location at job commit. S3A magic committer uses versioned object tags for atomicity without explicit move.

Job recovery: when ApplicationMaster crashes, YARN restarts it with state loaded from job history in HDFS. Completed tasks are not re-executed; only in-progress and pending tasks are rescheduled. This recovery is transparent to the user and requires no manual intervention.

**Application Master Recovery**

`yarn.resourcemanager.am.max-attempts`: 2 (default). [3] Application Master is retried at most twice. Job state is recovered from HDFS job history.

Google MapReduce paper (§3.3): completed map tasks are re-executed on worker failure because their output is stored locally on the failed worker; the JobTracker cannot retrieve map output from a dead node. Completed reduce tasks are not re-executed because their output is already written to the global filesystem (HDFS) and is safely committed. [14]

This asymmetry creates a key difference: map failures have higher re-execution cost than reduce failures. Speculative execution of maps is therefore more impactful than speculative reduces. [14]

Deterministic map functions allow task re-execution without semantic change; reading the same input blocks always produces the same output. Non-deterministic functions (random number generation, timestamp-based logic, external service calls) may produce different results on re-execution, potentially causing job semantic violations. [14]

## 4. Stragglers: Backup Tasks and Speculative Execution

**Backup Tasks (Google MapReduce)**

When a job is close to completion, backup executions of remaining in-progress tasks are scheduled. Increases resource usage by a few percent. Significant reduction in job completion time observed. [14]

**Hadoop Speculative Execution**

`mapreduce.map.speculative`: true (default). [3] Enable backup execution of slow map tasks on available task slots. The ApplicationMaster monitors task progress and launches speculative copies of stragglers on different nodes, hoping to finish faster than the original.

`mapreduce.reduce.speculative`: true (default). [3] Enable backup execution of slow reduce tasks. Reduce speculative execution is less impactful than map speculation because reduce output is committed to HDFS and cannot be re-executed, but slow reduces still extend job latency.

`mapreduce.job.speculative.slowtaskthreshold`: 1.0 (default). [3] A task is considered slow if its execution rate is 1.0 times slower than the median rate (i.e., disabled). Setting to < 1.0 (e.g., 0.5) makes speculation more aggressive, launching backups for tasks running at half median speed. Higher thresholds reduce speculation overhead but may miss stragglers.

**LATE Scheduler (OSDI 2008)**

Zaharia et al. introduced Longest Approximate Time to End (LATE), replacing progress-based speculation with time-based estimation. LATE computes remaining time for each task as: (total input size - bytes processed) / (bytes processed so far / elapsed time). Tasks with highest remaining time are speculated first. [15]

LATE caps the number of concurrent speculative tasks (typically 10% of running tasks) to avoid thrashing. Speculative copies are placed on the fastest available nodes, not random nodes. This precision improves job response time by a factor of two compared to default Hadoop speculation. Deployed in Facebook production. [15]

**Mantri (OSDI 2010)**

Ananthanarayanan et al. address outliers (stragglers) in operational MapReduce clusters. Mantri monitors task progress and identifies outliers as tasks significantly behind the median. Unlike Hadoop, Mantri does not simply restart outliers (which is wasteful if the outlier has more data); instead, Mantri re-partitions the remaining unprocessed input data of the outlier task and assigns repartitioned data to new tasks. [16]

This selective repartitioning is more effective than blanket speculative execution. Mantri's evaluation compared its approach against Hadoop default speculation, Dryad, standard MapReduce, and LATE across diverse workloads in Microsoft production clusters. [16]

**Spark Speculation**

`spark.speculation`: false (default). [6][7] Disabled by default in Spark, contrasting with Hadoop. Spark speculation is less effective than Hadoop because Spark dynamically generates tasks (especially in shuffle-heavy workloads with Adaptive Query Execution). Speculating tasks that may be eliminated is wasteful.

`spark.speculation.multiplier`: 3.0 (Spark 3.5+) or 1.5 (Spark 4.0+). [7] Task is speculated if duration exceeds median by this multiplier. Spark 4.0 reduced from 3.0 to 1.5 to be more aggressive about launching backups.

`spark.speculation.quantile`: 0.9 (Spark 3.5+) or 0.75 (Spark 4.0+). [7] Speculation starts only after this fraction of stage tasks complete. Spark 4.0 lowered from 0.9 to 0.75 to enable earlier identification of stragglers.

`spark.speculation.minTaskRuntime`: 100 ms (default). [6] Tasks shorter than this are never speculated. Avoids overhead on trivial tasks.

Configuration changes between versions reflect learning: Spark 4.0 made speculation more aggressive to catch stragglers earlier in the stage.

## 5. Scheduling and Data Locality

**Delay Scheduling (EuroSys 2010)**

Zaharia et al. introduce delay scheduling: temporarily skip tasks without local data (from assigned job), allowing other jobs' local tasks to run first. This simple technique balances data locality with fairness, avoiding the classic tradeoff between strict locality (which starves some jobs) and strict fairness (which ignores locality). [17]

Delay parameter D (typically 1-5 seconds): a task is delayed up to D seconds waiting for a local node; if no local node available after D seconds, schedule the task on any available node. Once a job has been delayed too long, it runs non-local to maintain fairness. Implemented in Hadoop and Spark YARN schedulers. [17]

Data-local vs rack-local: prioritize nodes with input data blocks. If no local node available, use same rack to minimize inter-rack network traffic. Inter-rack bandwidth is precious in large clusters and is often the bottleneck.

**YARN Resource Manager and Container Sizing**

Container memory: 1024-8192 MB min-max allocation (default). [3] Scheduler enforces these boundaries. Requests below minimum are set to minimum; requests exceeding maximum are rejected.

`mapreduce.map.memory.mb`: -1 (not set by default); inherits from YARN container allocation set by scheduler. [3] To override, set this to explicit MB (e.g., 2048).

`mapreduce.reduce.memory.mb`: -1 (not set by default). [3] To override, set this to explicit MB (e.g., 3072).

Typical production allocation: 1024 MB per container for light workloads (logging, filtering), 2048-4096 MB for joins and sorts, 8192+ MB for heavy aggregations. Container sizing must account for JVM overhead (200-300 MB per container) and user code heap requirements.

Capacity Scheduler and Fair Scheduler are the two built-in resource schedulers for multi-tenant clusters. Capacity organizes clusters into hierarchical queues with guaranteed capacity; Fair distributes available resources equally across running jobs and users.

ApplicationMaster itself consumes container resources (typically 1024-2048 MB); application configuration must reserve memory for AM and not over-allocate tasks beyond cluster capacity.

## 6. Data Skew: Mitigation and Detection

**Hot Keys and Combiners**

Hot keys: individual keys with disproportionate data volume cause reducer imbalance. Some reducers finish quickly; others become bottlenecks, extending overall job completion time. Examples: uniform email domains in email-based grouping, popular products in e-commerce sorting.

Combiners reduce early-stage skew by aggregating values per key on each mapper before shuffle. For count operations, combiners reduce hot key volume by orders of magnitude. For operations without natural combiners, skew persists to reduce phase.

Sampling Partitioner (TotalOrderPartitioner for TeraSort): sample a fraction of keys from input, sort samples to build a histogram, and create partition boundaries from the histogram. This ensures partition sizes are balanced even when key distribution is skewed. Widely used in large-scale sorting benchmarks.

**SkewTune (SIGMOD 2012)**

Kwon et al. detect skew at runtime by monitoring task progress. Skim and repartition straggler task input dynamically. Detects, estimates remaining work, and mitigates by repartitioning. [18]

**Spark Adaptive Query Execution (AQE) Skew Join**

`spark.sql.adaptive.skewJoin.skewedPartitionFactor`: 5 (default). [19] Partition is skewed if size exceeds 5x median partition size. This factor balances sensitivity: too high and skew goes undetected; too low and balanced partitions are split unnecessarily.

`spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes`: 256 MB (default). [19] Partition is skewed if it exceeds 256 MB in size. This absolute threshold catches very small joins (< 256 MB total) where 5x is not meaningful.

AQE splits skewed partitions on the large table and replicates corresponding partitions from the small table to match split count. This converts one slow task into multiple faster tasks, trading network bandwidth (duplicate small-table data) for parallelism. [19]

**The M x R Small-Block Problem**

In MapReduce, M mappers produce R partitions each, creating M x R shuffle blocks. If M=10,000 and R=100, shuffle creates 1,000,000 blocks. Reducers must fetch from many mappers, causing high per-server request count and IOPS. Remote shuffle services (Magnet, Riffle, Uber RSS, Celeborn) mitigate this by merging M blocks into 1 per partition server-side, reducing reducer fetch from 1,000,000 blocks to 100,000 blocks.

## 7. Counters, Task Status, and Job History

Map and reduce task status: RUNNING, SUCCEEDED, FAILED, KILLED. Status is reported to ApplicationMaster via heartbeat. Task kills may be user-initiated (failing the job) or automatic (exceeding timeout, caught by heartbeat expiry).

Job history: ApplicationMaster writes job and task logs to HDFS for debugging and auditing. Accessible through job history server web UI and command-line tools. Historical job data enables performance analysis and tuning.

Task counters: built-in counters (BYTES_READ, BYTES_WRITTEN, MAP_OUTPUT_RECORDS, REDUCE_INPUT_RECORDS) are automatically collected. User-defined counters are application-specific. Counters are aggregated across all task attempts and reported in the job completion report.

## 8. Critical Design Trade-Offs

**Sort Buffer vs Memory**: larger sort buffer (mapreduce.task.io.sort.mb) reduces spills and disk I/O but increases GC pressure. 100 MB is a balance for typical cluster memory (4-8 GB per container).

**Slowstart vs Overlay**: reduce slowstart at 0.05 overlaps map and reduce phases, reducing idle time. Lower slowstart (0.01) overlaps more but increases shuffle contention; higher slowstart (0.5) waits for most maps, reducing shuffle pressure but increasing latency.

**Speculation Cost**: speculative execution wastes resources on backup tasks. Payoff occurs only when stragglers are present. Disabled by default in Spark because dynamic task generation makes backup speculation less predictable.

**Local Fetch vs Network Efficiency**: reducer fetch buffer (0.70 of heap) prioritizes in-flight data size for throughput. Smaller buffer (0.5) reduces memory usage but may increase fetch latency if mappers are slow.

**Remote Shuffle Server Complexity**: push-based shuffle (Magnet, RSS, Celeborn) adds operational complexity but enables better resource utilization (executor decommissioning, better scheduling flexibility) and reduces M x R small-block overhead.

---

## Sources

| ID | URL | Establishes |
|:---|:----|:------------|
| 1 | https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/mapred-default.xml | Input split formula, task attempt limits, task timeout, speculative execution defaults |
| 2 | https://hadoop.apache.org/docs/r2.6.0/hadoop-project-dist/hadoop-hdfs/hdfs-default.xml | HDFS block size default 128 MB (134217728 bytes) |
| 3 | https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/mapred-default.xml | mapreduce.task.io.sort.mb=100, map.sort.spill.percent=0.80, task.io.sort.factor=10, all reduce/shuffle/AM config |
| 4 | https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/hadoop-mapreduce-client-core.jar (HashPartitioner source code) | HashPartitioner modulo formula |
| 5 | https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/mapred-default.xml | reduce.slowstart.completedmaps=0.05, reduce.shuffle.parallelcopies=5 |
| 6 | https://spark.apache.org/docs/latest/configuration.html | Spark shuffle and speculation defaults |
| 7 | https://raw.githubusercontent.com/apache/spark/branch-3.5/core/src/main/scala/org/apache/spark/internal/config/package.scala | Spark 3.5 speculation config: multiplier=1.5, quantile=0.75 |
| 8 | https://www.uber.com/blog/ubers-highly-scalable-and-distributed-shuffle-as-a-service/ | Uber RSS: 99.99% reliability, 95% reduction in shuffle container failures |
| 9 | https://celeborn.apache.org/docs/latest/ | Apache Celeborn architecture and version support |
| 10 | https://sns.cs.princeton.edu/assets/papers/2018-eurosys-zhang.pdf | Riffle merge speed ~100 MB/s, 100-node cluster tests |
| 11 | https://www.vldb.org/pvldb/vol13/p3382-shen.pdf | Magnet ~30% job improvement, petabyte scale at LinkedIn |
| 12 | https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/manifest_committer_protocol.html | FileOutputCommitter algorithm v2 description |
| 13 | https://hadoop.apache.org/docs/current/hadoop-aws/tools/hadoop-aws/committers.html | S3A committers handling M x R small-block problem |
| 14 | https://www.cse.iitd.ac.in/~rijurekha/col730_2022/mapreducepaper_oct10.pdf | Google MapReduce: backup tasks, map re-execution on failure, deterministic functions |
| 15 | https://www.usenix.org/legacy/event/osdi08/tech/full_papers/zaharia/zaharia.pdf | LATE scheduler, 2x job response time improvement |
| 16 | https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Ananthanarayanan.pdf | Mantri outlier detection and repartitioning |
| 17 | https://www.researchgate.net/publication/221351788_Delay_scheduling_A_simple_technique_for_achieving_locality_and_fairness_in_cluster_scheduling | Delay scheduling: locality vs fairness tradeoff |
| 18 | https://dl.acm.org/doi/10.1145/2213836.2213840 | SkewTune: runtime skew detection and dynamic repartitioning |
| 19 | https://oneuptime.com/blog/post/2026-01-24-spark-data-skew/ | Spark AQE skew join: factor=5, threshold=256MB |


---

## Spot-check corrections (editor, 2026-10-03)

Checked against the raw sources. These override the text above.

| Claim above | Correct value | Source |
|---|---|---|
| `spark.speculation.multiplier` 3.0 on 3.5, 1.5 on 4.0 (and quantile 0.9 then 0.75) | Backwards. `branch-3.5` package.scala: multiplier 1.5, quantile 0.75. `master` (4.x) and the current docs: multiplier 3, quantile 0.9 | https://raw.githubusercontent.com/apache/spark/branch-3.5/core/src/main/scala/org/apache/spark/internal/config/package.scala , https://spark.apache.org/docs/latest/configuration.html |
| `slowtaskthreshold` 1.0 means "1.0 times slower than the median" | It is a number of standard deviations: "The number of standard deviations by which a task's ave progress-rates must be lower than the average of all running tasks'" | https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/mapred-default.xml |
| Committer v1 "requires rename at task commit (atomic)", v2 "renames at job commit" | v1: task commit renames the attempt dir into `_temporary/$appAttemptID/$taskID`, job commit moves every task's files into the output dir (serial, slow, MAPREDUCE-4815). v2: task commit renames files straight into the output dir, so a task that fails mid-commit leaves partial files visible. Hadoop's code default is still 2 (`FILEOUTPUTCOMMITTER_ALGORITHM_VERSION_DEFAULT = 2` on trunk). Spark sets 1 and warns "2 may cause a correctness issue like MAPREDUCE-7282" | mapred-default.xml description, FileOutputCommitter.java on trunk, Spark configuration page |
| Slowstart "reduce time 116 s to 139 s" | Not found in the cited page. Treat as [unverified] | |
| Not in the survey | MR AM job recovery default on: `MR_AM_JOB_RECOVERY_ENABLE_DEFAULT = true` in MRJobConfig.java. `yarn.resourcemanager.recovery.enabled` default false. `yarn.nm.liveness-monitor.expiry-interval-ms` 600000. `yarn.resourcemanager.nodemanagers.heartbeat-interval-ms` 1000. `mapreduce.job.speculative.speculative-cap-running-tasks` 0.1. `mapreduce.task.skip.start.attempts` 2. `mapreduce.shuffle.port` 13562. `spark.shuffle.minNumPartitionsToHighlyCompress` 2000 | yarn-default.xml, mapred-default.xml, MRJobConfig.java, Spark package.scala |
