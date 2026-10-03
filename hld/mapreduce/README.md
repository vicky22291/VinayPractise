# MapReduce: a distributed batch processing framework

> One-line answer: a cluster resource manager (active plus standby, state in ZooKeeper) hands containers to one job master per job; the job master cuts the input into ~128 MB splits, runs one map task per split on a node that holds a replica of it, and each map task sorts its output by (reduce partition, key) into one file plus an index on local disk, served by a per-node shuffle service that outlives the task; reduce tasks pull their slice of every map output (or, for big jobs, read one merged file that map tasks pushed to a merger), merge-sort it, run the reduce function, and write to a private temp file that becomes visible only through a commit the job master grants to exactly one attempt; failures are handled by re-running work (a lost node costs the map outputs it held, never committed output), slow machines by backup copies of the last tasks, and the thing that breaks first at scale is the shuffle: M x R small random reads.

Tier 2, problem #48 in [`hld/README.md`](../README.md). Asked as "design MapReduce", "design Hadoop", "design a distributed word count over 10 TB", "sort 1 PB across a cluster", and as the shuffle half of "design Spark". Interviewers rarely want the API, they want the mechanisms: what a worker death costs, why completed maps re-run but completed reduces do not, how output stays exactly-once with backup tasks, why the shuffle hurts, and what happens when one key holds 20% of the data. Reusable blocks: [`../distributed-file-system/`](../distributed-file-system/) (the GFS/HDFS underneath), [`../query-engine/`](../query-engine/) (Spark's descendant of the same shuffle), [`../cluster-manager/`](../cluster-manager/) (containers and autoscaling), [`../distributed-job-scheduler/`](../distributed-job-scheduler/) (chaining jobs into DAGs), [`../delta-lake-transactions/`](../delta-lake-transactions/) (committing output on object stores), [`../../concepts/fan-out-fan-in.md`](../../concepts/fan-out-fan-in.md) (stragglers), [`../../concepts/zookeeper.md`](../../concepts/zookeeper.md) (master election). Sources in [`research/`](research/).

## Problem statement (as asked)

A company keeps petabytes of logs, crawled pages and table snapshots in a distributed file system on a cluster of a few thousand commodity machines. Hundreds of engineers who know nothing about distributed systems want to write two functions, `map(k1, v1) -> list(k2, v2)` and `reduce(k2, list(v2)) -> list(v3)`, and run them over terabytes. Design the framework that splits the input, runs the functions on thousands of machines, groups every value by key across machines, survives machines dying in the middle, keeps one slow machine from holding up the job, shares the cluster between many teams, and writes output that is exactly what one failure-free run would write.

## Functional requirements

Core:
- **Submit a job and get its output.** A user submits map and reduce functions (plus optional combiner and partitioner), an input path, an output path and R (the number of reduce partitions). They can poll progress and counters, and kill the job. Output is R files, visible all at once.
- **Run the map phase in parallel, close to the data.** Split the input, run one map task per split on many machines, prefer machines that already store the split.
- **Group by key across machines (shuffle) and run the reduce phase.** Every value for a key reaches the same reduce task. Keys arrive sorted within a partition.
- **Survive failure.** Worker death, task crash, a slow machine and master death do not fail the job in the common case, and never produce duplicate or partial output.
- **Share the cluster between teams.** Many jobs run at once. Each team gets its guaranteed share. A small job is not stuck behind a 500 TB job.

Below the line (say it out loud):
- The distributed file system itself (problem #3). We read splits and replica locations from it and write output through it.
- A general DAG engine, SQL, in-memory caching between jobs, iterative ML. That is Spark (problem #17). Users chain MapReduce jobs with a workflow scheduler (problem #6).
- Streaming. Exactly-once side effects from inside user code (writes to an outside database): the user must make those idempotent.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Cluster | 4,000 nodes, each 32 vCPU, 128 GB RAM, 12 x 8 TB HDD, 25 Gbps NIC. Racks of 40 nodes, 2.5:1 oversubscribed to the spine |
| Load | 100k jobs/day (peak ~12 submits/s). 10 PB read, 3 PB shuffled, 1 PB written per day |
| Job mix | 90% small (≤ 50 GB input), 9.5% medium (50 GB to 10 TB), 0.5% large (10 to 500 TB) |
| Throughput | Sort 100 TB on 1,000 nodes in under 30 min |
| Latency | Not interactive. Submit to first task running < 5 s when the queue has capacity. A 5 GB job finishes in < 1 min |
| Fault tolerance | Any number of worker deaths. Losing 10% of workers during the map phase adds < 10% to its run time; a death in the reduce wave costs at most one reduce task (~5 min in the 100 TB sort). A job master restart keeps all completed work |
| Stragglers | One slow node adds < 10% to job time. Backup tasks cost < 5% extra compute |
| Correctness | Deterministic functions: output equals one failure-free sequential run. Output appears all at once or not at all. Counters exact |
| Sharing | Each queue gets its guaranteed share back within 60 s. Cluster CPU utilisation > 70% |
| Availability | Submit and status API 99.9%. Resource manager failover < 30 s without killing running jobs |

## What interviewers probe (the ladder)

1. Walk word count over 10 TB from submit to output files. How many map tasks, how many reduce tasks, and why those numbers?
2. A worker dies after the map phase finished. Why do its completed map tasks re-run, and why do completed reduce tasks not?
3. Two copies of the same reduce task (a retry and a backup) both finish. Why is the output not duplicated?
4. The map function uses a random number. What breaks?
5. One key (`"the"`, or one customer id) holds 20% of the data. What happens to the job, and what are the fixes?
6. The 100 TB sort has 780,000 maps and 10,000 reduces. Why is the shuffle slow on HDDs, and what do push-based shuffle and remote shuffle services change?
7. The master dies. In the 2004 paper the job aborts. What do you build instead?
8. A 500 TB job and 200 small jobs share the cluster. How does each team get its share without wasting idle capacity?
9. The output goes to S3, where rename is a copy. How does the commit protocol change?
10. Why did Google and most of the industry move from MapReduce to Flume, Dataflow and Spark?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram per functional requirement, deep dives that mutate the design, final design with six rehearsal flows, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/map-side-sort-spill-and-combine.md`](deep-dives/map-side-sort-spill-and-combine.md) | Splits, the sort buffer, spills, merge, combiner, partitioner, map output file plus index |
| [`deep-dives/shuffle-pull-push-and-remote.md`](deep-dives/shuffle-pull-push-and-remote.md) | The M x R block problem, the shuffle service, slow start, push-merge (Magnet), Riffle, remote shuffle services |
| [`deep-dives/data-skew-and-partitioning.md`](deep-dives/data-skew-and-partitioning.md) | Hot keys, sampling partitioners, salting, two-phase aggregation, skew joins |
| [`deep-dives/fault-tolerance-and-recovery.md`](deep-dives/fault-tolerance-and-recovery.md) | Heartbeats, task retries, lost map output, fetch failures, job master and resource manager recovery, non-determinism |
| [`deep-dives/stragglers-and-speculation.md`](deep-dives/stragglers-and-speculation.md) | Backup tasks, LATE, Mantri, why speculation cannot fix skew |
| [`deep-dives/output-commit-and-exactly-once.md`](deep-dives/output-commit-and-exactly-once.md) | Temp files and rename, commit permission, FileOutputCommitter v1 and v2, object store committers and manifests |
| [`deep-dives/scheduling-locality-and-multi-tenancy.md`](deep-dives/scheduling-locality-and-multi-tenancy.md) | Resource manager vs job master, delay scheduling, queues, preemption, small-job paths |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `mapreduce.excalidraw` | My drawing. Missing until I draw it |
