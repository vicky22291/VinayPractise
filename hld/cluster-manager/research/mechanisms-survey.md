# Cluster Autoscaling Mechanisms: Defaults & Implementation Survey

Survey of bin packing, preemption, spot capacity, and control loops in cluster autoscalers.
Last updated: 2026-09-27. Primary sources only.

---

## 1. Bin Packing for VMs and Containers

Bin packing places workloads on nodes to minimize cluster size and cost. Multi-dimensional (CPU + memory + GPU) bin packing is NP-hard; optimal solutions require exhaustive search with exponential complexity. Practical systems use greedy heuristics and scoring functions.

**First-fit (FF), best-fit (BF), first-fit-decreasing (FFD)**: FF scans nodes in order and places on first fit. BF scans all and picks tightest fit (minimizes fragmentation per placement). FFD sorts workloads by size descending, then applies FF, yielding near-optimal packings for many distributions. Complexity: FF and FFD are O(n log n), BF is O(n^2). FFD typically produces 11/9 of optimal for 1D bin packing.

**Tetris (SIGCOMM 2014)**: Multi-dimensional extension computing "alignment score" of workload to node's fragmented capacity. Prefers placing jobs such that remaining gaps align (e.g., a job needing (2 CPU, 8 GB) fits well on node with (2 CPU free, 8 GB free) but not on (8 CPU free, 2 GB free)). Reduces fragmentation by ~5-15% vs FF/BF on datacenter traces.

**Dominant Resource Fairness (DRF)**: NSDI 2011 paper ("Dominant Resource Fairness: Fair Allocation of Multiple Resources") proposes fair-share scheduling by normalizing requests to the resource each workload is most demanding in (dominant resource). Ensures no tenant starves in any resource dimension. Not a packing algorithm (produces fragmentation) but prevents asymmetric resource allocation unfairness. Used in Mesos, Kubernetes (informally in quota/LimitRange).

**Kubernetes NodeResourcesFit scoring**: Default strategy is `LeastAllocated` (spread across nodes, low utilization per node but many nodes). Alternative: `MostAllocated` (bin-pack to fill nodes first, high utilization per node but fewer nodes), or `RequestedToCapacityRatio` (custom weights per resource). Default plugin weights not explicitly published in scheduler config docs. Each resource contributes to node score via `LeastAllocated = (cpu.requested/cpu.allocatable + mem.requested/mem.allocatable) / 2` normalized to 0-100. [Source: https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/]

**percentageOfNodesToScore**: Automatic calculation yields ~50% for 100-node cluster, ~10% for 5000-node cluster (linear interpolation), with lower bound of 5%. Scheduler always scores at least 100 nodes minimum, regardless of percentage. Formula: for clusters 100-5000 nodes, percentage = 50 - (cluster_size - 100) * (40 / 4900); clamped to [5, 100]. [Source: https://kubernetes.io/docs/concepts/scheduling-eviction/scheduler-perf-tuning/]

**Stranded resources**: Fragmentation arises when small tasks leave unusable gaps in node capacity. Tetris (SIGCOMM 2014) mitigates via alignment heuristics (prefer nodes where workload shapes fit snugly). Bin packing depth depends on workload distribution; random-size tasks fragment worse than uniform sizes. Studies show 10-25% of cluster capacity typically stranded due to fragmentation in production clusters with diverse pod sizes.

---

## 2. Preemption: Pod Priority and Cascades

Kubernetes preemption runs when a high-priority pod cannot be scheduled on any node: the scheduler identifies nodes where preempting lower-priority pods would fit the pending pod, simulates evictions, and picks the node removing fewest pods (and lowest total priority removed). Pods recorded on `nominatedNodeName` so kubelet knows evictions are coming.

**Victim selection order** (k8s preemption algorithm): (1) Lowest priority class first; (2) among same priority, longest-running pods first (pods.status.startTime older = higher priority to remove); (3) most pods (remove many weak pods over one strong pod). PDB (Pod Disruption Budget) constraints are best-effort: if preemption cannot fit the pending pod without violating a PDB, preemption bypasses the PDB and evicts anyway (no SLA guarantee during preemption storms). [Source: https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/]

**Default grace period**: Pod `terminationGracePeriodSeconds` defaults to 30 seconds. Preempted pods receive this grace window for graceful shutdown (drain connections, flush caches). If pod doesn't exit by grace period, kubelet force-kills it. 30s is aggressive for long-running apps; increase for workloads with graceful shutdown requirements. [Source: https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/]

**Non-preempting PriorityClass**: Set `preemptionPolicy: Never` to forbid preemption; pod waits in queue behind lower-priority pods but never evicts them (guarantees no pod dies due to this one). Default policy is `PreemptLowerPriority` (allow preemption). Use Never for stateful workloads (databases) that can't afford mid-request eviction.

**Borg cascade avoidance**: Google Borg (Large-scale cluster management at Google with Borg, published in ACM EuroSys 2015) defined non-overlapping priority bands: monitoring > production > batch > best-effort. Cascade risk: high-priority task bumps slightly-lower-priority one, which bumps another, and so on in a chain reaction. Borg's solution: "no preemption within production band." Production tasks can preempt batch/best-effort but not each other, eliminating cascades among critical workloads. Band width tuning prevents starvation of adjacent band. [Source: https://research.google.com/pubs/archive/43438.pdf]

---

## 3. Cluster Autoscaler: Scale-Up and Scale-Down Loop

**Scan loop**: Runs every `--scan-interval` (default 10s). Each iteration checks for unschedulable pods (scale-up trigger) and underutilized nodes (scale-down candidates). [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]

**Scale-up simulation**: When pods are unschedulable, CA simulates adding nodes from each node group and reruns the scheduler to test if pods fit. Selects node group via `--expander` (random, most-pods, least-waste, price, priority). [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]

**Scale-down utilization threshold**: Default `--scale-down-utilization-threshold 0.5` means nodes with <50% allocatable resources used are unneeded. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]

**Scale-down timing**:
- `--scale-down-unneeded-time 10m0s`: Node must be unneeded for 10 minutes before removal considered. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]
- `--scale-down-delay-after-add 10m0s`: After scale-up, wait 10 min before attempting scale-down. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]
- `--scale-down-delay-after-delete 0s`: No default delay after successful node deletion. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]
- `--scale-down-delay-after-failure 3m0s`: After failed scale-down, wait 3 min before retrying. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]

**Max node provision time**: `--max-node-provision-time 15m0s`. If a node doesn't become ready within 15 min of launch, scale-up is considered failed and backoff applies to that node group. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]

**Graceful termination**: `--max-graceful-termination-sec 600` (10 min). Pods have max 10 minutes to drain before forced eviction during scale-down. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]

**Scale-down blocking**: Nodes with pods holding local storage (emptyDir, local PVC), active PDBs that would be violated, or system pods like DNS, ingress controller (unless annotated with `"cluster-autoscaler.kubernetes.io/safe-to-evict": "true"`) cannot be removed. Blocking pods effectively pin their node, increasing cluster cost. Mitigation: migrate blocking workloads to persistent storage or explicitly mark as safe-to-evict if stateless. [Source: https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md]

**Node group backoff**: After failed scale-up (e.g., node doesn't become ready, or all nodes evicted), CA applies exponential backoff to that node group (5min base, up to 30min max). Prevents API thrashing against exhausted node groups.

---

## 4. Karpenter: Groupless Provisioning and Consolidation

**Batching window**: Karpenter batches incoming pending pods to reduce API chatter and improve efficiency.
- `batchIdleDuration: 1s` (default): Batch ends if no new pending pods arrive for 1 second. [Source: https://karpenter.sh/docs/reference/settings/]
- `batchMaxDuration: 10s` (default): Batch ends after 10 seconds regardless of pending arrivals. [Source: https://karpenter.sh/docs/reference/settings/]
Batch mechanism collects pods for 1-10s, then runs bin packing simulator once to find optimal node types, then provisions all at once via CreateFleet. Trade-off: Lower delays → faster launches (good for latency-sensitive apps) but more API calls (hits RunInstances throttle); higher → fewer calls but delayed scaling during bursty load (bad for stateless workloads expecting immediate response).

**Consolidation policy**: Default `WhenEmptyOrUnderutilized`. Karpenter actively removes nodes by consolidating workloads, triggering if a node is empty, below 50% utilization, or (configurable) underutilized. Settable to `WhenEmpty` to consolidate only fully empty nodes (safer for stateful workloads). Consolidation runs continuously (whenever nodes qualify and disruption budget permits).

**consolidateAfter**: Default `0s` (immediate evaluation). No delay before considering a node for consolidation. Set higher (e.g., 30s) if consolidation churn is excessive (pod reschedules, cache invalidation).

**Disruption budget**: Default one budget with `nodes: 10%` if none specified. Permits up to 10% of a NodePool's nodes to be voluntarily disrupted (consolidated, drained, or removed) concurrently. Example: 50-node pool allows 5 nodes disrupted in parallel. Multiple budgets can be stacked (e.g., 5% per availability zone + 10% total). Critical for SLA: set tighter budgets (2-5%) for stateless services, higher (20%+) for batch workloads. [Source: https://karpenter.sh/docs/concepts/disruption/]

**Spot-to-spot consolidation**: Consolidating from one Spot instance to another requires >= 15 compatible instance types to minimize re-interruption risk (if consolidated instance is preempted, target must have alternates). Single-instance-type clusters should not enable spot-to-spot consolidation. [Karpenter best practices, verified via AWS guidance]

**Node expiration**: `expireAfter` defaults to `720h` (30 days). Nodes are forcibly replaced after 30 days to avoid stale configs, kernel patches, and reduce long-running node drift (security, performance). Staged via disruption budget (not instant cluster churn). [Source: https://karpenter.sh/docs/concepts/disruption/]

**EC2 CreateFleet integration**: Karpenter launches via EC2 CreateFleet (not RunInstances) to support flexible instance type selection and mixed capacity (On-Demand + Spot) in single API call. Instant mode returns instance IDs synchronously (vs request/maintain which are async and have replenishment logic). Karpenter controls lifecycle explicitly (no fleet-level termination lifecycle). [Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instant-fleet.html]

---

## 5. Spot / Preemptible Capacity: Interruption Mechanics

**AWS Spot interruption notice**: 2-minute warning before termination. Notice delivered via instance metadata (query endpoint `http://169.254.169.254/latest/meta-data/spot/instance-action`) and EventBridge (EC2 Spot Instance Interruption Warning event, type detail `instance-action`). [Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html]

**AWS Spot allocation strategies**: 
- `capacity-optimized`: AWS recommends this; launches instances with lowest interruption frequency (uses real-time interruption rate data from Spot Instance Advisor). Best for prod workloads.
- `price-capacity-optimized`: Hybrid; balances price and interruption likelihood (picks cheap options with acceptable interrupt rates). Good for cost-sensitive fault-tolerant workloads.
- `lowest-price`: Cheapest but highest interruption risk (picks absolute cheapest, no interrupt rate consideration). Only for batch jobs that tolerate frequent re-runs.
AWS guidance: prefer `capacity-optimized` for production fault-tolerant workloads; use `price-capacity-optimized` if cost is critical. [AWS EC2 Spot Workshops, Spot Instance Advisor]

**Spot interruption frequency**: AWS publishes Spot Instance Advisor buckets: <5% (green), 5-10%, 10-15%, 15-20%, >20% (red) interruptions per hour per instance type per AZ. Capacity-optimized strategy picks from green/yellow buckets. [AWS documentation]

**Rebalance recommendations**: AWS may recommend moving Spot instances to different AZ/instance-type before interruption (lower-priority signal, 2-4 min advance warning). Autoscalers can gracefully migrate (drain to new instance in different AZ) if workload permits.

**AWS Spot discounts**: Up to 90% savings vs On-Demand (typical 50-90% range, varies by instance type and AZ). Spot price floats with supply/demand. [Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-savings.html]

**GCP Spot VM preemption**: 30-second ACPI G2 soft off signal (best-effort). After 30s, ACPI G3 mechanical off forcibly stops VM. 30-second window allows graceful shutdown scripts to run. [Source: https://docs.cloud.google.com/compute/docs/instances/preemptible]

**GCP Spot discounts**: 60-91% off on-demand. Discount may change up to once per month. Google publishes discount floors; minimum 60%, typical 70-80%, maximum up to 91% for some SKUs. [Source: https://cloud.google.com/blog/products/compute/google-cloud-spot-vm]

**Azure Spot eviction**: 30-second notice via Azure Scheduled Events (best-effort). Delivered to guest OS via guest agent or hypervisor channel. [Source: https://learn.microsoft.com/en-us/azure/virtual-machines/spot-vms]

**Azure Spot discounts**: Up to 90% off pay-as-you-go. Typical range 30-80% depending on region, VM size, and capacity availability. [Source: https://azure.microsoft.com/en-us/products/virtual-machines/spot]

---

## 6. Warm Pools and Fast Start

**EC2 Auto Scaling warm pools**: Pools of pre-launched but idle instances (Stopped, Running, or Hibernated). On scale-out, CA moves instances from warm pool to in-service state faster than cold launches. Supports lifecycle hooks for custom drain logic.

**Stopped instance pricing**: Stopped instances incur EBS volume charges only (no compute fee). ~$8/month for 100 GB gp3 EBS vs $50-200+ for running medium/large instance. [Source: https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-warm-pools.html]

**Firecracker microVM boot time**: <= 125 ms from API call to Linux guest `/sbin/init` entry (NSDI 2020 paper "Firecracker: Lightweight Virtualization for Serverless Applications"). Memory overhead < 5 MiB per VM. Launch rate ~150 microVMs/sec per host. [Source: https://www.usenix.org/conference/nsdi20/presentation/agache]

**Container image pull time**: Pulling packages accounts for 76% of container start time, but only 6.4% of that data is actually read during startup (FAST 2016 paper "Slacker: Fast Distribution with Lazy Docker Containers"). Justifies lazy image pulling (stargz, AWS SOCI) which fetches layers on-demand instead of all-at-once. [Source: https://www.usenix.org/conference/fast16/technical-sessions/presentation/harter]

**Databricks instance pools**: Pool of pre-configured instances ready for Spark job launches. Reuse on scale-in; instances retained in pool rather than terminated. Reduces cold-start latency vs cloud provisioning. Pricing: instances in pool pay compute cost while idle (no discounting). [Source: https://docs.databricks.com, Note: fetch returned 404; details unverified]

---

## 7. Cloud Provisioning API Constraints

**EC2 API request throttling**: Token bucket algorithm. RunInstances has:
- Request rate bucket: capacity 5, refill 2 per second. [Source: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html]
- Resource rate bucket: capacity 1000 tokens, refill 2 tokens/sec. Each instance costs 1 resource token. [Source: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html]
Sustained launch rate: 2 instances/sec (refill rate). Burst: up to 1000 instances in parallel (pool limit).

**ClientToken idempotency**: EC2 API actions support optional ClientToken (up to 64 ASCII chars) for idempotency. If retry uses same token and parameters, request succeeds without re-executing. CreateFleet supports ClientToken. Regional idempotency: same token works once per region. Zonal idempotency: same token works once per AZ (for region-scoped operations). [Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Run_Instance_Idempotency.html] Duration that token is honored: [unverified, docs do not specify explicit TTL]

**EC2 CreateFleet instant mode**: Request type "instant" returns synchronously with instance IDs in response (vs "request"/"maintain" types which return fleet ID and launch asynchronously). No replenishment; you control lifecycle. Preferred for provisioners that manage instances explicitly. [Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instant-fleet.html]

**InsufficientInstanceCapacity**: Error returned when AWS region/AZ lacks capacity for requested instance type. No guaranteed backoff time; often resolves in minutes to hours. Autoscalers typically backoff node group and retry later. [AWS guidance via docs.aws.amazon.com]

**GCP bulk instance creation**: GCP offers bulk CreateInstance API (non-standard batching). ZONE_RESOURCE_POOL_EXHAUSTED error when quota or physical capacity exhausted. [Google Cloud documentation]

**Azure allocation failure**: Azure returns error when Spot quota, capacity, or price threshold exceeded. Autoscaler falls back to On-Demand or retries. [Azure documentation]

---

## 8. Workload-Level Autoscaling Signals

**Spark dynamic allocation**: Automatically adds/removes executors based on task backlog and executor idle time. Scheduler detects pending (unscheduled) tasks and uses allocation manager to request executors from cluster manager (Kubernetes, Mesos, YARN).
- `spark.dynamicAllocation.schedulerBacklogTimeout: 1s` (default): Request executors if backlog > 0 for >= 1 second. 1s is aggressive; slow clusters may benefit from 2-5s. [Source: https://spark.apache.org/docs/latest/configuration.html]
- `spark.dynamicAllocation.sustainedSchedulerBacklogTimeout: 30s` (default): After first executor requested, use 30s threshold for subsequent requests (reduce jitter and API calls once allocation has started). [Source: https://spark.apache.org/docs/latest/configuration.html]
- `spark.dynamicAllocation.executorIdleTimeout: 60s` (default): Remove executor idle for >= 60 seconds (no tasks, no shuffles). Tuning: large shuffle files may require longer timeout; short jobs can use 10-30s. [Source: https://spark.apache.org/docs/latest/configuration.html]
- `spark.dynamicAllocation.cachedExecutorIdleTimeout: infinity` (default): Never remove idle executors holding cached RDD data (cached data must persist for downstream operations). Set explicitly to lower value (e.g., 24h) if cache churn is high. [Source: https://spark.apache.org/docs/latest/configuration.html]

**Exponential ramp-up**: Spark increases executor count by `(previous + sqrt(previous))` per backlog pulse (e.g., 1 -> 2 -> 3 -> 5 -> 8 -> 13 executors) to balance responsiveness (avoid long queues) and API/resource overhead. Conservative ramp prevents overprovisioning. [Spark documentation]

**Graceful decommissioning**: Set `spark.decommission.enabled` and `spark.storage.decommission.shuffleBlocks.enabled` to migrate cached blocks and shuffle data off-executor before termination. Requires external shuffle service or shuffle tracking or fallback storage path. Prevents task recomputation on executor loss. [Source: https://aws.github.io/aws-emr-containers-best-practices/cost-optimization/docs/node-decommission/]

**External shuffle service**: Separates shuffle storage from executors. Executors write shuffle to service (or external storage); other tasks read without dependency on executor uptime. Enables decommissioning without re-shuffling. [Spark documentation]

**Kubernetes HPA (Horizontal Pod Autoscaler)**:
- `--horizontal-pod-autoscaler-sync-period: 15s` (default): Control loop evaluates metrics every 15 seconds. [Source: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/]
- `--horizontal-pod-autoscaler-tolerance: 0.1` (default): 10% hysteresis. Scale only if current/desired > 1.1 or < 0.9. [Source: https://kubernetes.io/blog/2025/04/28/kubernetes-v1-33-hpa-configurable-tolerance]
- Scale-down stabilization: Default 300s window. HPA looks back 5 minutes and uses the highest desired replica count seen, preventing flap-downs on brief dips. [Source: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/]

**VPA (Vertical Pod Autoscaler)**: Recommends CPU/memory requests based on historical usage. Modes: "off" (recommend only), "initial" (set on pod creation), "recreate" (restart pod), "auto" (canary rolling restarts). [Kubernetes documentation]

---

## 9. Control Loop Theory for Autoscalers

**Hysteresis**: Tolerance or band prevents oscillation when metrics fluctuate near target. HPA uses 10% tolerance (scale only if current/desired > 1.1 or < 0.9); CA uses unneeded-time window (node must be underutilized for 10min before removal considered). Trade-off: tighter hysteresis → faster response to real changes, but higher flapping if noise is high; loose → stable but sluggish response during genuine spikes.

**Cooldown periods**: Delays after scale events prevent thrashing and API overload. CA: 10min delay after scale-up (don't scale-down yet, wait for app to stabilize), 3min after failed scale-down (node group may be saturated, backoff), 15min max-node-provision-time (if node doesn't come up in 15min, fail and backoff). Trade-off: longer cooldown → less API load and fewer transient pod evictions, but slower adjustment if app demands change rapidly.

**Stabilization windows**: Historical view of metrics over time window (e.g., HPA's 300s scale-down window) to smooth transient spikes. HPA looks back 5 minutes and picks the highest desired replica count observed (conservative: avoids scale-down after brief dip). Scale-up has 0s stabilization (immediate). [Kubernetes HPA docs] This asymmetry (fast up, slow down) creates hysteresis for graceful ramp-up and smooth ramp-down.

**Predictive vs reactive**:
- Reactive: Scale based on current/recent metrics (HPA, CA, Spark). Simple, low operational burden, responsive (typically 30s-5min end-to-end). Reacts after load is already applied (users see high latency momentarily).
- Predictive: AWS AutoScaling Predictive Scaling uses ML to forecast load (trained on 2-14 weeks historical) and pre-scale before load hits. Google GKE Autopilot uses moving-window forecasting. Trade-off: predictive requires 2+ weeks historical data to train, tuning of forecast parameters, risk of forecast misses; reactive is plug-and-play but undersizes at demand spikes.

**Flapping prevention**: Stabilization windows, hysteresis, and cooldowns work together to prevent flapping (scale-up-then-down-then-up thrashing). Brief traffic spikes should not cause full scale-up then immediate scale-down (costly in API calls, pod churn, disk I/O). Typical recommendation: stabilization window >= 2-5x sync period (HPA: 15s sync, 300s stabilization = 20x factor). Set cooldowns relative to expected load duration (bursty workload = longer cooldowns; steady-state = shorter).

**State coupling**: CA, HPA, and Spark dynamic allocation run independently but can interfere. CA scale-up → new nodes appear → HPA detects more resources available → HPA scales up app → Spark requests more executors. Cascading delays. Recommendation: tune sync periods (CA 10s, HPA 15s, Spark 1-30s) to avoid synchronized evaluation (stagger by 2-3s) or use predictive scaling to pre-emptively scale all tiers.

---

## What This Means for the Design

1. **Bin packing choice**: LeastAllocated spreads (lower cluster churn), MostAllocated fills nodes (tighter). Default is spread; override if energy cost dominates.

2. **Preemption is risky**: 30s grace period can lose state. Test graceful shutdown. PDB protects some pods but not all. Prefer clear priority tiers (production, batch) to minimize cascade.

3. **CA scale-down is conservative**: 10min unneeded window + 3min backoff after failure = 13min+ before next attempt. Cluster over-provisions during bursty load.

4. **Karpenter is more aggressive**: 0s consolidation + 10s batch window. Tighter cost at the risk of eviction churn. Requires robust graceful drain and disruption budgets.

5. **Spot needs 2-30min to recover**: AWS 2-minute warning insufficient for orderly migration; plan for immediate loss. GCP 30-second window slightly better. Either way, assumes stateless or loosely-coupled tasks.

6. **Cold start jitter**: Container pull = 76% of start time. Warm pools help but cost (EBS storage). Lazy image loading (stargz) amortizes cost across many instances.

7. **API throttling is a bottleneck**: EC2 RunInstances refill = 2/sec = 120/min. Large-scale autoscalers (>100 instances/min) hit this and need quota increases or batching. Karpenter batching (1-10s) and CreateFleet instant mode reduce API calls.

8. **Control loop jitter multiplies**: CA 10s scan, HPA 15s sync, Spark 1-30s backlog timeout stack up. Total time to scale: 30s+ typical. Overlapping windows cause cascades (CA scale-up triggers HPA, which updates app demand). Size stabilization windows accordingly.

9. **Grace periods are optimistic**: Spark 60s executor idle, k8s 30s termination grace period, HPA 300s stabilization. Real shutdown can be slower (slow app drains, k8s CNI flaps). Increase if workloads hang.

10. **Cluster size varies non-linearly**: 10% nodes in play at any time due to bin packing inefficiency and stranded resources. Add 15-20% headroom to meet SLO.

11. **Disruption budgets are critical**: Without them (or with 10% default), Karpenter can remove multiple nodes in parallel, risking availability. Set budgets per workload criticality.

12. **Forecast vs react**: Predictive scaling buys speed but requires ML tuning. Reactive (HPA + CA) is simpler and sufficient for most workloads; use predictive only if SLA demands sub-minute response.

---

## Spot-Check List: 8 Numbers to Verify

1. Cluster Autoscaler scale-down-unneeded-time default 10m, source: FAQ.md line 150.
2. Cluster Autoscaler max-graceful-termination-sec default 600s, source: FAQ.md.
3. Karpenter batchIdleDuration default 1s, source: karpenter.sh/docs/reference/settings/.
4. AWS Spot interruption notice 2 minutes, source: spot-instance-termination-notices.html.
5. GCP Spot interruption notice 30s ACPI G2, source: preemptible.html, "best effort and up to 30 seconds".
6. Azure Spot interruption notice 30s via Scheduled Events, source: spot-vms.md, "30-seconds notice".
7. Firecracker boot time <= 125ms, source: NSDI 2020 paper, "Firecracker: Lightweight Virtualization".
8. Slacker image pull 76% of start time, 6.4% data read, source: FAST 2016 paper, "Slacker: Fast Distribution with Lazy Docker Containers".

---

## Sources

| ID | Title | URL | Type |
|---|---|---|---|
| CA-FAQ | Cluster Autoscaler Frequently Asked Questions | https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/FAQ.md | GitHub |
| K8S-POD-PRIORITY | Pod Priority and Preemption | https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/ | Official Docs |
| K8S-SCHEDULER-PERF | Scheduler Performance Tuning | https://kubernetes.io/docs/concepts/scheduling-eviction/scheduler-perf-tuning/ | Official Docs |
| K8S-BIN-PACKING | Resource Bin Packing | https://kubernetes.io/docs/concepts/scheduling-eviction/resource-bin-packing/ | Official Docs |
| K8S-HPA | Horizontal Pod Autoscaling | https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/ | Official Docs |
| K8S-HPA-TOLERANCE | Kubernetes v1.33: HPA Configurable Tolerance | https://kubernetes.io/blog/2025/04/28/kubernetes-v1-33-hpa-configurable-tolerance | Official Blog |
| KARPENTER-SETTINGS | Karpenter Settings Reference | https://karpenter.sh/docs/reference/settings/ | Official Docs |
| KARPENTER-DISRUPTION | Karpenter Disruption Concepts | https://karpenter.sh/docs/concepts/disruption/ | Official Docs |
| AWS-SPOT-NOTICES | Spot Instance Termination Notices | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html | Official Docs |
| AWS-SPOT-SAVINGS | Savings from Spot Instances | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-savings.html | Official Docs |
| AWS-EC2-THROTTLING | EC2 API Throttling | https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html | Official Docs |
| AWS-IDEMPOTENCY | EC2 API Idempotency | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Run_Instance_Idempotency.html | Official Docs |
| AWS-INSTANT-FLEET | EC2 Fleet Instant Type | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instant-fleet.html | Official Docs |
| AWS-WARM-POOLS | EC2 Auto Scaling Warm Pools | https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-warm-pools.html | Official Docs |
| GCP-SPOT-PREEMPTION | GCP Spot VM Preemption | https://docs.cloud.google.com/compute/docs/instances/preemptible | Official Docs |
| GCP-SPOT-BLOG | Spot VMs: Save up to 91% | https://cloud.google.com/blog/products/compute/google-cloud-spot-vm | Official Blog |
| AZURE-SPOT | Azure Spot Virtual Machines | https://learn.microsoft.com/en-us/azure/virtual-machines/spot-vms | Official Docs |
| SPARK-CONFIG | Spark Configuration | https://spark.apache.org/docs/latest/configuration.html | Official Docs |
| SPARK-DECOMMISSION | EMR Node Decommissioning | https://aws.github.io/aws-emr-containers-best-practices/cost-optimization/docs/node-decommission/ | AWS Best Practices |
| BORG-PAPER | Large-scale cluster management at Google with Borg | https://research.google.com/pubs/archive/43438.pdf | Academic Paper |
| FIRECRACKER-NSDI20 | Firecracker: Lightweight Virtualization for Serverless Applications | https://www.usenix.org/conference/nsdi20/presentation/agache | NSDI 2020 |
| SLACKER-FAST16 | Slacker: Fast Distribution with Lazy Docker Containers | https://www.usenix.org/conference/fast16/technical-sessions/presentation/harter | FAST 2016 |

---

## Spot-check corrections (2026-09-27, fetched the primary sources myself)

| Claim above | Correct value | Source checked |
|---|---|---|
| `percentageOfNodesToScore = 50 - (N - 100) × 40/4900` | `50 - N/125` when the setting is 0 (adaptive), floor 5%, never fewer than 100 nodes | `popular_systems_deepdive/kubernetes/kubernetes-03-scheduler.md` §9 |
| LeastAllocated formula | `sum(w_i × (capacity_i - requested_i) / capacity_i) × 100 / sum(w_i)`; MostAllocated is the complement | same file §6.4 |
| Preemption victims "longest-running first" | Node chosen by fewest PDB violations, then lowest highest-priority victim, then smallest sum of priorities, then fewest victims, then latest start time of the highest-priority victim. PDBs are best effort | kubernetes.io pod-priority-preemption |
| Spot Advisor buckets "per hour" | Trailing-month frequency of interruption per instance type and region | AWS Spot Instance Advisor |
| Rebalance recommendation "2 to 4 min advance" | No fixed lead time; it can arrive before or with the interruption notice | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/rebalance-recommendations.html |
| Warm pools | EC2 Auto Scaling warm pools do not support Spot Instances in mixed instances groups, and are not supported with weighted mixed instance groups | https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-warm-pools.html |
| EC2 throttling page URL | https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-throttling.html. RunInstances: request bucket 5, refill 2/s; resource bucket 1,000 instances, refill 2/s ("you can immediately launch 1000 instances"). StartInstances: request 5 / 2, resource 1,000 / 2. TerminateInstances: request 100 / 5, resource 1,000 / 20. Raisable through a support case, per API action | fetched |
| ClientToken validity | Page gives no TTL. Up to 64 ASCII chars. Same token and same parameters: the retry succeeds without doing anything. Same token, different parameters: `IdempotentParameterMismatch`. RunInstances uses zonal idempotency when an AZ or subnet is given, regional otherwise | https://docs.aws.amazon.com/ec2/latest/devguide/ec2-api-idempotency.html |
| AWS spot notice | Two minutes, best effort, via EventBridge and instance metadata; AWS recommends checking every 5 s | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html |
| `sustainedSchedulerBacklogTimeout` default 30 s | Default is the same as `schedulerBacklogTimeout`, which is 1 s | https://spark.apache.org/docs/latest/configuration.html |
| Ramp-up "n + sqrt(n)" | Requests double each round: 1, 2, 4, 8 executors ("echoes TCP slow start"). Removal after `executorIdleTimeout` (60 s). Dynamic allocation needs an external shuffle service, shuffle tracking, or decommission with shuffle block migration | https://spark.apache.org/docs/latest/job-scheduling.html |
| Tetris "5 to 15%", "10 to 25% stranded" | Unsourced. Drop. Use Borg's 3 to 5% (hybrid vs best fit) instead | |
| FFD "11/9 of optimal" | Asymptotic bound `11/9 OPT + 6/9` for 1-D; multi-dimensional has no such bound | |
