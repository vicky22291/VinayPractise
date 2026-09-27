# Autoscaling cluster manager

> One-line answer: run three control loops per availability zone (AZ). A per-cluster **workload autoscaler** turns each Spark cluster's task backlog into a desired worker count. A per-AZ **cell scheduler** bin-packs the resulting containers onto VMs, preempting only best-effort work when nothing is free. A per-AZ **capacity manager** buys and releases VMs from the cloud with in-flight requests counted as supply. Start time comes from free slots on running VMs, a small hot pool of booted VMs, and pre-scaling before the known top-of-hour burst. Spot capacity is diversified across at least 6 instance types, drivers stay on-demand, and a reclaimed worker hands its shuffle files to a neighbour inside the 2-minute notice. The component that breaks first is the **provisioner**, because the cloud launch API gives one account 1,000 instances at once and then only 2 per second, and can say "no capacity".

Tier 2, problem #21 in [`hld/README.md`](../README.md). This is Databricks' own product in disguise (classic clusters, instance pools, serverless compute). Google asks the same thing as "Borg with autoscaling". No verbatim public prompt was found; see [`research/interview-framing-survey.md`](research/interview-framing-survey.md). Siblings: [`distributed-job-scheduler/`](../distributed-job-scheduler/) (#6) is the main client and hands tasks to this system, and #11 async provisioning is the cloud-call half of this design seen on its own.

## Problem statement (as asked)

Design the cluster manager for a managed data platform. Customers create compute clusters: one driver plus between `min` and `max` workers, with an instance shape, a runtime version, a spot policy and a priority. The platform must start clusters in seconds and grow and shrink each cluster with its workload. It must pack workloads tightly onto cloud VMs to keep cost down, use spot capacity where allowed and survive losing it, and let important work take capacity from cheap work when there is not enough. Customers are billed per second of compute, so every idle VM is margin lost.

Follow-ups that always come: a VM takes a minute to boot, so how do you start a cluster in 10 seconds? A spot VM is reclaimed mid-job, so what happens to the job? Bin packing is NP-hard, so what heuristic, and how do you avoid fragmentation? How do you stop the autoscaler from thrashing? The control plane dies, so do running jobs die? The cloud API throttles you at midnight, so now what?

## Functional requirements

Core:
- Create, resize and terminate a cluster (driver plus `min..max` workers). Asynchronous and idempotent.
- Place every driver and worker container on a VM: pack tightly, respect AZ, shape and isolation constraints.
- Autoscale each cluster between `min` and `max` from its own backlog, and autoscale the VM fleet from pending demand, releasing idle VMs.
- Run workers on spot VMs when the cluster's policy allows, and survive reclamation without failing the job.
- When capacity is short, higher-priority work preempts lower-priority work.

Below the line (say it out loud):
- The Spark engine and the job scheduler that triggers runs (#6). We expose a cluster; they use it.
- Billing, networking (VPC, security groups) and identity. They exist; we call them.
- Gang scheduling for GPU training (all N GPUs or nothing). A seam, not a first build.
- A cluster spanning AZs or regions. A cluster lives in one AZ.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale (one region, 3 AZs) | 300k cluster starts/day, 12k concurrent clusters at peak, about 100k containers and 800k vCPU requested, about 16k VMs at peak and 6k at trough. Top-of-hour burst: 5,000 cluster starts in the 60 s after 00:00 UTC |
| Start latency | Driver plus `min` workers running: p50 <= 10 s, p99 <= 60 s for clusters up to 50 workers |
| Autoscale reaction | Scale-up decision within 5 s of backlog; new workers within 10 s from warm capacity, 60 s cold |
| Efficiency | Fleet packing (requested / allocatable) >= 85% at peak; idle warm capacity <= 3% of fleet; >= 60% of worker vCPU on spot |
| Spot | < 0.1% of job runs fail because of a spot reclamation |
| Availability | Running clusters survive a full control-plane outage. Create API 99.95%. Cell scheduler failover < 15 s |
| Correctness | No leaked VM lives more than 15 min; no double-bought capacity beyond one control interval; a cluster create retried with the same key never makes two clusters |
| Consistency | Cluster spec strong (versioned row). Cell placement strong within the AZ (one leader, Raft store). Node usage and cloud inventory eventual, seconds |

## What interviewers probe (the ladder)

1. A VM takes 60 s to boot. How does a cluster start in 10 s? What does the warm capacity cost, and how big is it?
2. 5,000 clusters start at 00:00. Which box breaks first? (Not the scheduler. The cloud API.)
3. Bin packing is NP-hard. Which heuristic, which score, and how do you measure fragmentation?
4. A spot VM gets its 2-minute notice. Walk the next 120 seconds. Now the whole spot pool goes at once.
5. The autoscaler adds VMs, the job finishes, it removes them, a new job arrives. How do you stop thrashing? How do you avoid buying the same capacity twice?
6. Production job needs capacity now, the cloud says `InsufficientInstanceCapacity`. Who gets preempted, and how do you avoid a cascade?
7. The control plane is down for 10 minutes. What stops, what keeps running?
8. The provisioner crashed after calling the cloud but before recording the VM. What happens to that VM?
9. Two tenants on one VM: how are they isolated? Would you ever not share?
10. How do you migrate from "one VM per worker, customer's account" (classic) to a shared fleet?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/bin-packing-and-placement.md`](deep-dives/bin-packing-and-placement.md) | Scoring, stranded resources, equivalence classes, shape menu, spread limits, drain by attrition vs consolidation |
| [`deep-dives/warm-pools-and-fast-start.md`](deep-dives/warm-pools-and-fast-start.md) | Start-latency budget, capacity tiers, warm pool sizing as safety stock, calendar pre-scale, image and runtime warm-up |
| [`deep-dives/spot-capacity-and-interruption.md`](deep-dives/spot-capacity-and-interruption.md) | Spot policy, diversification, the 120 s timeline, shuffle migration budget, fallback, correlated loss, remote shuffle |
| [`deep-dives/preemption-and-priority.md`](deep-dives/preemption-and-priority.md) | Bands, when to preempt vs buy, victim selection, cascades, budgets, quota and fairness |
| [`deep-dives/autoscaling-control-loops.md`](deep-dives/autoscaling-control-loops.md) | The three loops, signals, in-flight accounting, hysteresis, scale-down safety, the races between loops |
| [`deep-dives/provisioning-and-reconciliation.md`](deep-dives/provisioning-and-reconciliation.md) | Cloud API limits, idempotent launches, capacity errors, orphan GC, multi-account sharding, control-plane failover |
| [`research/`](research/) | Raw web research notes with source links and spot-check corrections. Input to the files above, not study material |
| `cluster-manager.excalidraw` | My drawing. Missing until I draw it |
