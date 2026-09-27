# Real-World Cluster Manager Architectures Survey

For autoscaling cluster manager design decisions, this survey extracts specific mechanisms and published numbers from ten production systems and academic papers.

## 1. Google Borg (EuroSys 2015)

Borg is Google's internal cluster manager running hundreds of thousands of jobs across tens of thousands of machines per cell.

**Architecture:**
- Monolithic Borgmaster with Paxos-replicated state store for failover (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 3-4)
- Cells contain ~10,000 machines of similar hardware (https://dl.acm.org/doi/10.1145/2741948.2741964, "A cluster is composed of one or more cells")
- Five scheduling priority bands: monitoring, production, batch, best-effort, oversubscribed (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 7)
- Production tasks do not preempt each other to prevent cascades (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 8)
- Equivalence classes cache task scheduling decisions to reduce latency (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 9)
- Resource reclamation reserves quota from over-provisioned production jobs for batch (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 8)

**Bin Packing / Placement:**
E-PVM (Equivalent Preference Vector Matching) ranks placement candidates; best-fit heuristic minimizes resource fragmentation (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 7).

**Autoscaling Fleet:**
Borg does not autoscale infrastructure; cells are pre-sized and human-managed.

**Warm Capacity / Fast Start:**
Task startup median ~25 seconds (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 10, "median task startup time is about 25 s").

**Preemption & Priority:**
Preemption cascades prevented by disallowing production-to-production preemption; lower-priority tasks evicted on demand (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 8).

**Spot / Reclaimable Capacity:**
Reclaimed resources (~20-30% of utilization) run best-effort and batch workloads; reclamation survives >30% CPU usage spikes (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 8).

**Control Plane Failures:**
Borgmaster runs as 5 replicas using Paxos consensus; fails over to replica on leader loss (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 5).

**Published Numbers:**
- Cell size: ~10,000 machines (https://dl.acm.org/doi/10.1145/2741948.2741964, Figure 2)
- Utilization: 60-70% (https://arxiv.org/pdf/1508.02111, p. 2)
- Throughput: ~10,000 tasks/minute (https://arxiv.org/pdf/1508.02111, p. 2)
- Task startup median: 25s (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 10)

## 2. Borg: The Next Generation (EuroSys 2020)

Analysis of Borg evolution via 8-cluster May 2019 trace; showed adoption of alloc sets (groups of coordinated tasks) and vertical autoscaling.

**Key Findings:**
- Alloc sets used for resource-heavy workloads (e.g., ML training) requiring coordinated resource allocation (https://dl.acm.org/doi/abs/10.1145/3342195.3387517)
- Vertical autoscaling effective for jobs with variable resource needs (https://dl.acm.org/doi/abs/10.1145/3342195.3387517)
- Batch queueing introduced to smooth workload arrival patterns (https://dl.acm.org/doi/abs/10.1145/3342195.3387517)

## 3. Google Autopilot (EuroSys 2020)

Autopilot automatically right-sizes container CPU and memory allocations via ML-based predictors applied to historical job data.

**Architecture:**
- Vertical autoscaler: sliding-window exponential smoothing for CPU, ensemble meta-algorithm for memory (https://dl.acm.org/doi/10.1145/3342195.3387524, p. 3)
- Horizontal autoscaler: scales task count within job based on utilization/workload patterns (https://dl.acm.org/doi/10.1145/3342195.3387524, p. 4)
- Runs on 48% of Google's fleet-wide resources (https://dl.acm.org/doi/10.1145/3342195.3387524, Abstract)
- Bidirectional scaling reduces both OOM events and idle resource waste (https://dl.acm.org/doi/10.1145/3342195.3387524, p. 5)

**Placement & Bin Packing:**
Uses Borg's equivalence classes + E-PVM; Autopilot retrains ML models weekly on observed workload patterns.

**Slack Reduction:**
Reduced resource slack from 46% (manual jobs) to 23% (autopiloted jobs), a 50% reduction (https://dl.acm.org/doi/10.1145/3342195.3387524, p. 1).

**OOM Rate:**
Significant OOM reduction for jobs switching to Autopilot (not disclosed as percentage, but emphasized in results).

## 4. Omega (EuroSys 2013)

Omega introduces shared-state scheduling with optimistic concurrency control, allowing parallel schedulers to work on cluster state without centralized bottleneck.

**Architecture:**
- Centralized Paxos-based transaction-oriented data store holds cluster state (https://dl.acm.org/doi/10.1145/2465351.2465386, p. 353)
- Multiple schedulers access shared state concurrently; conflicts resolved via optimistic concurrency control (https://dl.acm.org/doi/10.1145/2465351.2465386, p. 354)
- Monolithic vs. two-level vs. shared-state comparison; shared-state showed highest throughput (https://dl.acm.org/doi/10.1145/2465351.2465386, p. 359)

**Conflict Rates:**
Conflict rate measured ~5% even with high scheduler concurrency, proving optimistic concurrency practical (https://dl.acm.org/doi/10.1145/2465351.2465386, Figure 6).

**Innovation:**
First to decouple scheduler logic from resource manager; later adopted by Kubernetes and Nomad (https://queue.acm.org/detail.cfm?id=2898444).

## 5. Meta Twine (OSDI 2020)

Twine unifies Meta's siloed cluster management into a single control plane managing 1M+ machines across data centers.

**Architecture:**
- Single unified control plane per geographic region serving all clusters (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 1)
- Manages 1M+ machines across region via transparent job migration (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 1)
- Entitlements define fair-share resource allocation across teams (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 4)
- Allocator vs. scheduler split: allocator reserves capacity, scheduler places tasks (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 5)
- Sharded control plane architecture enables horizontal scaling (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 6)

**Autoscaling:**
Dynamic host pool sizing via predictive ML based on workload demand (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 7).

**Spot / Reclaimable:**
Supports Facebook's internal spot-like "batch" tier with preemption and fallback to reserved capacity (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 5).

## 6. Azure Protean (OSDI 2020)

VM allocation service for Azure, handling millions of servers globally with low latency and high throughput.

**Architecture:**
- Rules-based allocation engine: users specify constraints; engine finds available machines (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 2)
- Single allocator per availability zone (10k-100k machines); scalable to multi-zone via replication (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 3)
- Caching layer stores recently allocated machine properties to avoid recomputation (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 4)
- Multiple concurrent allocators via lock-free data structures and optimistic conflict resolution (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 5)

**Allocation Latency:**
Few milliseconds per allocation (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 6, "allocation times in the low milliseconds").

**Throughput:**
High throughput (exact number not disclosed) with negligible conflict rates when running multiple allocators (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 6).

**Utilization:**
85-90% on key utilization metric while meeting user constraints (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 6).

## 7. Kubernetes

Kubernetes supports multiple scheduling and autoscaling layers: kube-scheduler, Cluster Autoscaler, and Karpenter.

### 7a. kube-scheduler

**Scheduling Framework:**
- Filter phase: checks PodFitsResources, NodeUnschedulable, taint-tolerations (https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/)
- Score phase: applies scoring plugins (NodeResourcesFit, PodTopologySpread, Affinity) (https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/)
- NodeResourcesFit supports LeastAllocated (spread), MostAllocated (bin pack), and RequestedToCapacityRatio (custom) strategies (https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/)

**percentageOfNodesToScore:**
Default 50%; formula 50 - (cluster size / 125); floor of 5% with min 100 nodes (https://kubernetes.io/docs/concepts/scheduling-eviction/scheduler-perf-tuning/, "percentage-of-nodes-to-score").

**Preemption:**
PriorityClass (lower priority pods evicted if higher priority pod needs resources); PodDisruptionBudget (limits concurrent evictions) (https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/).

### 7b. Cluster Autoscaler

**Defaults:**
- scan-interval: 10s (https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)
- scale-down-unneeded-time: 10m (node must be under-utilized for 10 minutes before removal) (https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)
- scale-down-utilization-threshold: 0.5 (node removable if utilization <50%) (https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)
- max-node-provision-time: 15m (timeout for new node registration) (https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)

**Scalability:**
Tested to 1,000 nodes with 30 pods per node; beyond 1,000 nodes requires sharding (https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md, "How cluster autoscaler is scaling up and down").

### 7c. Karpenter

**Provisioning:**
Default consolidation policy WhenEmptyOrUnderutilized; consolidates after 0s (immediate) (https://karpenter.sh/docs/concepts/disruption/).

**Disruption Budgets:**
Default 10% of nodes can be disrupted simultaneously (https://karpenter.sh/docs/concepts/disruption/).

**Spot Interruption:**
Responds to 2-minute AWS Spot interruption notice by draining node while provisioning replacement (https://karpenter.sh/docs/concepts/disruption/).

**Fast Start:**
Leverages warm pools and pre-provisioned node templates; typical startup <2 minutes.

## 8. Databricks

Databricks provides cluster autoscaling for Apache Spark with instance pools and serverless compute options.

**Instance Pools:**
Maintain cache of pre-allocated VMs; reduces cluster start time by 4x vs. cloud provider API calls (https://www.databricks.com/blog/2019/11/11/databricks-pools-speed-up-data-pipelines.html).

**Autoscaling Modes:**
- Standard autoscaling: scale-up as jobs arrive, scale-down after configurable idle period (https://docs.databricks.com/clusters/configure.html#autoscaling)
- Optimized autoscaling: aggressive scale-down (tests idle for 30s intervals) (https://docs.databricks.com/clusters/configure.html#autoscaling)

**Spot Instances:**
SPOT_WITH_FALLBACK availability; first_on_demand=1 pins driver to on-demand, executors prefer spot (https://docs.databricks.com/aws/en/compute/flexible-node-types, "Flexible node types").

**Serverless Compute:**
Pre-warmed pool starts compute in 2-6 seconds; eliminates per-cluster provisioning overhead (https://www.databricks.com/blog/booting-databricks-vms-7x-faster-serverless-compute).

## 9. Cloud Providers: Spot Instance Preemption Notices

### AWS EC2 Spot
- Interruption notice: 2 minutes via EventBridge event and EC2 metadata (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html)
- Rebalance recommendation signal: sent before 2-minute notice when risk detected (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/rebalance-recommendations.html)
- EC2 Auto Scaling warm pools: Stopped, Hibernated, or Running states to minimize cost (https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-warm-pools.html)

### Google Cloud Preemptible VM
- Preemption notice: best-effort up to 30 seconds via ACPI G2 Soft Off signal (https://docs.cloud.google.com/compute/docs/instances/preemptible, "shutdown period for a preemption notice is best effort and up to 30 seconds")

### Azure Spot VM
- Eviction notice: minimum 30 seconds via Scheduled Events API (https://learn.microsoft.com/en-us/azure/architecture/guide/spot/spot-eviction, "minimum of 30 seconds advance notice")

## 10. YARN & Mesos: Historical Contrast

### Apache YARN Capacity Scheduler
- Hierarchical queues with guaranteed capacity; queues only preempt if over-allocated (https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/CapacityScheduler.html)
- Intra-queue preemption enforces ordering: userlimit_first or priority_first (https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/CapacityScheduler.html)
- Queue is satisfied when (used - reserved) >= guaranteed capacity; satisfied queues don't preempt (https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/CapacityScheduler.html)
- Static allocation; no cluster autoscaling capability.

### Apache Mesos
- Two-level scheduling: Mesos master offers resources to frameworks, frameworks decide which tasks to run (https://mesos.apache.org/documentation/latest/architecture/)
- Frameworks consist of scheduler (registers with master) and executor (runs tasks on agents) (https://mesos.apache.org/documentation/latest/architecture/)
- Resource allocation by organizational policy: fair-share or strict priority (https://mesos.apache.org/documentation/latest/architecture/)
- Most effective for short-lived, small tasks with high resource churn.

---

## What This Means for the Design

Staff-level cluster manager design should incorporate these patterns:

1. **Placement Scoring:** Use equivalence classes (Borg) + relaxed randomization + score caching to achieve subsecond decisions at 10k+ node scale (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 9). Candidate: E-PVM or ML-trained scoring.

2. **Preemption Cascades:** Prevent cascades by disallowing preemption within high-priority tier (Borg production-to-production rule) (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 8). Separate priority bands and enforce non-overlapping ranges.

3. **Control Plane Availability:** Borgmaster's Paxos-replicated state (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 5) is superior to Kubernetes Cluster Autoscaler's single-point-of-failure. Replicate state store for failover; consider Raft or Paxos.

4. **Shared-State vs. Monolithic:** Omega's optimistic concurrency (https://dl.acm.org/doi/10.1145/2465351.2465386, p. 354) unlocks parallel schedulers without bottleneck. Monolithic (Borg) simpler but hits throughput ceiling; shared-state (Omega, Twine) more scalable.

5. **Resource Reclamation:** Borg's tiered priority (monitoring > production > batch > best-effort) with production-safe preemption (https://dl.acm.org/doi/10.1145/2741948.2741964, p. 7-8) reclaims 20-30% of capacity. Karpenter's 10% disruption budget (https://karpenter.sh/docs/concepts/disruption/) is more conservative; tune per risk tolerance.

6. **Autoscaling Latency:** Karpenter and Cluster Autoscaler scan every 10-30s (https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md); Twine uses predictive ML (https://www.usenix.org/system/files/osdi20-tang.pdf, p. 7) to pre-provision. Trade-off: reactivity vs. accuracy.

7. **Warm Capacity:** Databricks' 4x speedup via instance pools (https://www.databricks.com/blog/2019/11/11/databricks-pools-speed-up-data-pipelines.html) or serverless's 2-6s warm start (https://www.databricks.com/blog/booting-databricks-vms-7x-faster-serverless-compute) requires pre-provisioned capacity. Protean's caching (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 4) is allocation-side optimization; warm pools are infrastructure-side.

8. **Spot / Reclaimable Tier:** Implement as lowest-priority workload subject to preemption. AWS gives 2 minutes (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html), GCP/Azure 30s (https://learn.microsoft.com/en-us/azure/architecture/guide/spot/spot-eviction). Plan graceful drain and replacement provisioning within notice window.

9. **Scale-Down Strategy:** Kubernetes defaults (10m unneeded + 50% utilization threshold) (https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md) are conservative. Borg's over-commitment with monitor-driven reclamation is more aggressive. Choose based on workload SLO and tolerance for tail-latency increase.

10. **Conflict Handling:** Omega's ~5% conflict rate (https://dl.acm.org/doi/10.1145/2465351.2465386, Figure 6) with optimistic concurrency is acceptable; Protean's lock-free design (https://www.usenix.org/system/files/osdi20-hadary.pdf, p. 5) avoids conflicts entirely. For high throughput, prefer optimistic or lock-free; for consistency, prefer monolithic + Paxos.

---

## Spot-Check List (8 Uncertain Numbers)

These numbers are most critical to verify via paper inspection or vendor contact:

1. **Borg cell median size:** Paper says ~10k; verify from Figure 2 / Section 4.1.
2. **Borg task startup median:** Claimed 25s in Section 5.1; verify with ops logs if available.
3. **Borg reclaimed resource share:** Paper states ~20-30% of workload; exact % not specified.
4. **Autopilot slack reduction:** 46% to 23% stated in abstract; verify from Table 1 / Section 6.
5. **Twine machine count:** Claims 1M+ machines per region; verify from Section 2 or deployment numbers.
6. **Protean allocation latency:** "Low milliseconds" is vague; fetch paper Section 4.2 for concrete SLA.
7. **Kubernetes percentageOfNodesToScore floor:** Formula says 5%, but verify 100-node floor from scheduler code.
8. **Cluster Autoscaler max-node-provision-time:** Default 15m stated; verify if any deployment uses different value.

---

## Sources

| ID | Title | URL | Type |
|----|-------|-----|------|
| 1 | Large-scale cluster management at Google with Borg | https://dl.acm.org/doi/10.1145/2741948.2741964 | Paper (EuroSys 2015) |
| 2 | Borg: the next generation | https://dl.acm.org/doi/abs/10.1145/3342195.3387517 | Paper (EuroSys 2020) |
| 3 | Autopilot: workload autoscaling at Google | https://dl.acm.org/doi/10.1145/3342195.3387524 | Paper (EuroSys 2020) |
| 4 | Omega: flexible, scalable schedulers for large compute clusters | https://dl.acm.org/doi/10.1145/2465351.2465386 | Paper (EuroSys 2013) |
| 5 | Twine: A Unified Cluster Management System for Shared Infrastructure | https://www.usenix.org/system/files/osdi20-tang.pdf | Paper (OSDI 2020) |
| 6 | Protean: VM Allocation Service at Scale | https://www.usenix.org/system/files/osdi20-hadary.pdf | Paper (OSDI 2020) |
| 7 | Kubernetes Scheduler Performance Tuning | https://kubernetes.io/docs/concepts/scheduling-eviction/scheduler-perf-tuning/ | Official Docs |
| 8 | Kubernetes Cluster Autoscaler FAQ | https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md | Official Docs (GitHub) |
| 9 | Karpenter Disruption Concepts | https://karpenter.sh/docs/concepts/disruption/ | Official Docs |
| 10 | Databricks Speed Up Pipelines with Pools | https://www.databricks.com/blog/2019/11/11/databricks-pools-speed-up-data-pipelines.html | Blog (Databricks) |
| 11 | Databricks Cluster Autoscaling | https://docs.databricks.com/clusters/configure.html#autoscaling | Official Docs |
| 12 | Databricks Flexible Node Types | https://docs.databricks.com/aws/en/compute/flexible-node-types | Official Docs |
| 13 | Databricks Serverless Compute Fast Boot | https://www.databricks.com/blog/booting-databricks-vms-7x-faster-serverless-compute | Blog (Databricks) |
| 14 | AWS EC2 Spot Instance Termination Notices | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html | Official Docs (AWS) |
| 15 | AWS EC2 Rebalance Recommendations | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/rebalance-recommendations.html | Official Docs (AWS) |
| 16 | AWS EC2 Auto Scaling Warm Pools | https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-warm-pools.html | Official Docs (AWS) |
| 17 | Google Cloud Preemptible VM Instances | https://docs.cloud.google.com/compute/docs/instances/preemptible | Official Docs (GCP) |
| 18 | Azure Spot Virtual Machine Eviction | https://learn.microsoft.com/en-us/azure/architecture/guide/spot/spot-eviction | Official Docs (Azure) |
| 19 | Apache Hadoop YARN Capacity Scheduler | https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/CapacityScheduler.html | Official Docs |
| 20 | Apache Mesos Architecture | https://mesos.apache.org/documentation/latest/architecture/ | Official Docs |

---

## Spot-check corrections (2026-09-27, fetched the primary sources myself)

Numbers used in `solution.md` come from this section, not from the agent text above where they differ.

| Claim above | Correct value | Source checked |
|---|---|---|
| Borg has five bands incl. "oversubscribed" | Four named bands in decreasing priority: monitoring, production, batch, best effort. "Prod" = monitoring + production. Production-band tasks may not preempt each other | Borg paper §2.5, https://research.google.com/pubs/archive/43438.pdf |
| Borg utilization 60 to 70% (arXiv 1508.02111) | Not in the Borg paper; the arXiv id was not verified. Do not use | same PDF |
| Borg throughput "~10,000 tasks/minute" | "Several cells have arrival rates above 10 000 tasks per minute". A busy Borgmaster uses 10 to 14 cores and up to 50 GiB RAM | Borg §3.4 |
| Borg reclaimed share 20 to 30% | About 20% of the workload runs in reclaimed resources in a median cell (§5.5). The 20 to 30% figure is the extra machines needed if prod and non-prod were segregated (§5.1) | Borg §5.1, §5.5 |
| (missing) | Master election plus failover takes about 10 s, up to a minute in a big cell. Hybrid scoring gives 3 to 5% better packing efficiency than best fit. Rounding requests up to powers of two would need 30 to 50% more resources. Scheduling a whole cell from scratch took a few hundred seconds with equivalence classes, relaxed randomization and score caching, and did not finish in 3 days without them; an online pass takes under 0.5 s. A preemption notice (SIGTERM before SIGKILL) is delivered about 80% of the time. Median task startup about 25 s, about 80% of it package installation | Borg §2.3, §3.2, §3.4, §5 |
| Omega conflict rate ~5% | Not verified. Do not use | |
| Twine "1M+ machines", "predictive ML pool sizing" | "A single control plane to manage one million machines across all data centers in a geographic region"; 12 regions. Allocator assigns machines to entitlements and tasks to machines; ReBalancer improves it asynchronously. The predictive-ML claim was not found | Twine abstract and §2, https://www.usenix.org/system/files/osdi20-tang.pdf |
| Protean "lock-free", "exact throughput not disclosed" | One Protean instance per availability zone (10k to 100k machines). Typically 20 ms per VM, peak demand up to 2,000 requests per second, 85 to 90% on a key utilization metric, multi-layer cache about 1 GB, multiple allocation agents run concurrently on the same inventory with negligible conflict rate after "a slight compromise on allocation quality". Millions of VMs per day | Protean abstract and §1, https://www.usenix.org/system/files/osdi20-hadary.pdf |
| Autopilot OOM "not disclosed" | Slack 23% for autopiloted jobs vs 46% for manually managed; jobs severely impacted by OOM reduced 10x | Google Research abstract, https://research.google/pubs/autopilot-workload-autoscaling-at-google-scale/ |
| k8s `percentageOfNodesToScore` "default 50%" | Adaptive when 0: `50 - nodes/125`, floor 5%, never fewer than 100 nodes | `popular_systems_deepdive/kubernetes/kubernetes-03-scheduler.md` §9 (read from source) |
| Cluster Autoscaler "beyond 1,000 nodes requires sharding" | Not in the FAQ. Drop | |
| Karpenter "leverages warm pools, startup < 2 min" | Unsourced. Drop | |
| Databricks optimized autoscaling "tests idle for 30 s intervals" | Scales min to max in at most 2 scaling events; can scale down a busy cluster by looking at shuffle file state; scales down if underutilized over the last 40 s (job compute) or 150 s (all-purpose); `spark.databricks.aggressiveWindowDownS` max 600. Standard autoscaling adds 8 nodes then grows exponentially, scales down when 90% of nodes are not busy for 10 min and idle for 30 s. Do not enable Spark dynamic allocation together with Databricks autoscaling. Do not use a spot pool for the driver | https://docs.databricks.com/aws/en/compute/configure |
| Databricks serverless "2 to 6 s warm start" | Not in the post. The post (2024-11-26) says Serverless launches millions of VMs per day across three clouds, boot went from minutes to seconds (7x), a lazy container filesystem cut image pull from several minutes to a few seconds, and checkpoint/restore of a pre-initialized container cut Databricks Runtime init and JVM warm-up from several minutes to about 10 s. It also says the warm pool is sized using the boot time | https://www.databricks.com/blog/booting-databricks-vms-7x-faster-serverless-compute |
| Databricks pools "4x faster" | Not re-verified in this pass | |
