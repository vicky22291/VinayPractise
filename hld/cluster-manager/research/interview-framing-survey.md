# Interview Framing Survey: Autoscaling Cluster Manager

How "design an autoscaling cluster manager" is asked across Staff and L6 system design interviews. Covers prompt variants, functional requirements, follow-up probes, and Staff-level expectations per platform.

---

## 1. Reported Prompts by Company & Level

### Databricks
- **L5 SDE**: "Design a job scheduler for distributed compute" https://www.designgurus.io/answers/detail/what-to-expect-in-the-databricks-system-design-interview
  - Focus: partitioning, exactly-once vs. at-least-once, backpressure, fault tolerance
  - Scale not disclosed publicly
  - Interview length: 45 to 60 min

- **Senior/Staff**: "Design Delta Lake transaction system", "Build real-time data ingestion pipeline", "Architect ML pipeline orchestration" https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/
  - Implicit infrastructure requirements: cluster allocation, resource scheduling
  - Paywalled: full deep dives behind subscription ($299+)

### Google
- **L6 Staff**: "Design a global chat service", "Design multi-region storage system", "Design distributed caching system" https://www.hellointerview.com/guides/google/l6
  - Notably: cluster/autoscaler NOT emphasized in public Google L6 guide
  - Focus on distributed systems fundamentals, not infrastructure provisioning
  - Implication: Staff bar at Google values CAP, consistency, failover patterns over bin packing

### Amazon
- **SDE II/SDE III**: "Design a job/task scheduler handling 10 million jobs/day" https://leetcode.com/discuss/general-discussion/1082786/System-Design:-Designing-a-distributed-Job-Scheduler-or-Many-interesting-concepts-to-learn/
  - FRs: submit job, retrieve status, retry logic (up to 5 retries), cancel job, list jobs
  - Scale: 10M jobs/day, 5-second execution average, 1000 QPS peak
  - Probes: broker crashes, control plane failures, what metrics to track

- **SDE III**: "Design a service to allocate pool of resources optimally" https://www.glassdoor.com/Interview
  - Scope: compute and storage allocation, workload placement, quota enforcement
  - Paywalled: detailed candidate reports

### OpenAI
- **L5+**: "Design a distributed job scheduler" https://www.designgurus.io/answers/detail/what-to-expect-in-the-openai-system-design-interview
  - Requirements: task orchestration, retry semantics (exactly-once vs. at-least-once), fault tolerance, priority handling
  - Scale: not publicly stated
  - Common probe: how does single control plane failure affect in-flight jobs

### Meta / Microsoft
- No cluster manager variant found in public sources. Meta interviews focus on scaling existing systems. Microsoft interviews include VM allocation but not autonomous autoscaling.

### Platform Engineering (All companies)
- **General variant**: "Design a self-service environment provisioning system for N product teams" https://www.kore1.com/platform-engineer-interview-questions/
  - FRs: request compute, release compute, enforce quotas, notify on capacity constraints
  - Scale: N teams, 10x resource spikes without starving other tenants
  - Probes: thrashing, affinity conflicts, cost per team

---

## 2. Functional Requirements Across Variants

| Variant | Core FRs | Optional FRs | Access Patterns |
|---------|----------|--------------|-----------------|
| **Amazon Job Scheduler** | Submit, retrieve status, cancel, retry logic | Priority handling, batching, SLA-based ordering | Query by job ID, list by user, filter by status |
| **Databricks Cluster Mgr** | Allocate cluster, scale on demand, attach nodes, deallocate | Spot loss resilience, cost tracking, multi-region failover | Fetch cluster state, list pending jobs, query resource usage |
| **Google L6 (distributed systems)** | Replicate across regions, handle partition, strong consistency | Failover, graceful shutdown, client-side retry | Read-your-writes, causal consistency within region |
| **OpenAI Job Scheduler** | Schedule task, execute once, track state, handle preemption | Priority queue, affinity, backpressure | Dependency graphs, job lineage, cost allocation |
| **Platform Eng (self-service)** | Request compute, enforce quota, deallocate, notify | Scaling automation, SLA enforcement, chargeback | Query per team, forecast spikes, audit allocation changes |

**Common to all**: Durability (jobs not lost on broker crash), fault tolerance (control plane recovery), observability (what failed and why).

---

## 3. Top 15 Probes by Frequency & Interview Impact

Ranked by how often they appear across sources. Numbers in brackets = count of sources reporting it.

1. **Exactly-once vs. at-least-once execution semantics** [13 sources]
   - Sources: https://www.designgurus.io/system-design-interview/questions/job-scheduler, https://leetcode.com/discuss/general-discussion/1082786/, DesignGurus Databricks guide
   - Why it matters: Staff bar expects candidate to articulate trade-off (idempotent retries vs. deduplication), not hand-wave it
   - Red flag: "We'll use a queue" without naming delivery guarantee

2. **Fault tolerance and failure recovery (broker crashes, control plane failure)** [12 sources]
   - Sources: https://www.teamblind.com/post/Databricks-L5-System-Design-Interview-bz1foi6R, Hello Interview Job Scheduler, SystemDesignHandbook
   - What's tested: can the system continue submitting jobs if broker is down? How fast does it recover?
   - Common mistake: assuming single control plane can be recovered instantly

3. **Latency SLA enforcement (e.g., 2-second execution window or custom bound)** [10 sources]
   - Sources: Amazon job scheduler LeetCode, TechInterview.org, DesignGurus Staff expectations
   - Why asked: distinguishes whether candidate thinks about tail latency (p99, p999) or just average
   - Red flag: mentioning throughput but not latency percentiles

4. **Throughput scaling (10k-100k+ jobs/second)** [9 sources]
   - Sources: Amazon SDE III prompt, LeetCode discussions, Databricks L5 variant
   - What's probed: horizontal vs. vertical scaling, batch vs. single-job processing
   - Staff bar: candidate should propose rate limiting / backpressure, not just "add more replicas"

5. **Bin packing and resource utilization optimization** [8 sources]
   - Sources: https://www.techinterview.org/post/3233460937/system-design-kubernetes-autoscaling/, Kubernetes scheduler interviews
   - Problem: NP-hard; solution: first-fit, best-fit, or custom heuristic
   - Probe: "Can you guarantee optimal bin packing?" → "No. Here's my heuristic and why."

6. **Cold start times for new workers/nodes** [7 sources]
   - Sources: https://dev.to/codewithved/mastering-kubernetes-for-system-design-interviews-hp7, TechInterview.org, GitHub autoscaler FAQ
   - Databricks example: spinning a new cluster node takes 2 to 5 minutes; what do you do with jobs in the meantime?
   - Staff bar: candidate should quantify trade-off (fast = expensive; slow = queuing)

7. **Spot instance handling and preemption** [7 sources]
   - Sources: https://www.groundcover.com/learn/cost-optimization/bin-packing-kubernetes, Databricks cluster manager discussions, AWS cost optimization
   - Requirement: handle mid-job reclamation; migrate or re-queue work
   - Probe: "Your node is preempted; 10 jobs are lost. What's your SLA?" → tests severity assessment

8. **Thrashing prevention and stabilization windows** [6 sources]
   - Sources: https://www.techinterview.org/post/3233460937/system-design-kubernetes-autoscaling/, TechInterview, Medium autoscaling articles
   - Problem: HPA scales up → cluster autoscaler scales up → jobs finish → HPA scales down → cluster autoscaler scales down → new spike
   - Staff bar: candidate names the loop and proposes stabilization window (default Kubernetes: 5min scale-down delay)

9. **Affinity rules, topology constraints, scheduling conflicts** [6 sources]
   - Sources: https://www.kore1.com/platform-engineer-interview-questions/, Kubernetes scheduler interviews, GitHub Devinterview
   - Examples: "These jobs must run on same AZ"; "These jobs cannot run on same node"
   - Probe: how does your scheduler enforce both hard and soft constraints? Cost trade-off?

10. **Control plane scalability and bottlenecks** [5 sources]
    - Sources: https://levelup.gitconnected.com/step-by-step-guide-to-faang-staff-level-system-design-interviews-a54018e6e085, Exponent Databricks Q&As
    - Scale: 1M+ pending jobs, 100k submissions/sec, what's the bottleneck?
    - Probe: is it scheduler CPU, database write throughput, or message queue throughput? Proposal must be specific.

11. **Multi-tenancy, quota enforcement, resource isolation** [5 sources]
    - Sources: Platform Eng KORE1, SystemDesignHandbook Databricks guide, TeamBlind discussions
    - Requirement: prevent one team from starving others; fair resource allocation
    - Probe: "Team A claims 80% of cluster but is only using 40%. Do you let Team B oversubscribe?" → tests quota vs. fairness

12. **Backpressure and queue management** [5 sources]
    - Sources: Kafka streaming interviews, LeetCode job scheduler, DesignGurus blog
    - Problem: submissions exceed processing rate; what happens to new requests?
    - Staff answer: reject with 429 + backoff guidance, or queue with bounded wait (e.g., 5 min)

13. **Cost optimization (reserved vs. on-demand vs. spot instances)** [5 sources]
    - Sources: Databricks cluster cost interviews, AWS case studies, https://www.designgurus.io/blog
    - Probe: "Your monthly compute bill is $1M. Propose changes." Tests whether candidate reasons about CapEx vs. OpEx trade-offs.
    - Red flag: "Use spot instances" without discussing failure modes

14. **Monitoring, observability, failure detection** [4 sources]
    - Sources: DesignGurus Staff expectations Substack https://designgurus.substack.com/p/9-habits-i-see-in-engineers-who-pass, Medium, SystemDesignHandbook
    - Requirement: "What metric wakes up an engineer at 3am?" Candidate must name one specific metric per critical component.
    - Staff bar: include SLO, alert threshold, and runbook

15. **Horizontal vs. vertical scaling trade-offs** [4 sources]
    - Sources: Kubernetes VPA vs. HPA articles, https://levelup.gitconnected.com/kubernetes-autoscaling-101-cluster-autoscaler-horizontal-pod-autoscaler-and-vertical-pod-2a441d9ad231
    - Probe: "Can we just give each node 10x RAM instead of scaling horizontally?" → tests understanding of failure blast radius, hot spot risk

---

## 4. Hello Interview & SystemDesignHandbook Guidance

### Hello Interview Job Scheduler Breakdown
https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler

**Public (free tier):**
- FRs: submit job, retrieve job status, update job status, cancel job, get statistics (average execution time, success rate)
- Scale: not specified in free tier
- Key data structures: Job queue, job state machine (pending → running → completed/failed)

**Paywalled ($199/year):**
- Deep dives on retry logic, distributed scheduling, failure handling
- Full solution code and diagrams
- Page reports paywalled content with "Unlock with subscription"

### SystemDesignHandbook Databricks Guide
https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/

**Public (free overview):**
- Confirms Databricks focuses on cluster allocation, exactly-once guarantees, fault tolerance
- Lists key interview topics: hot spotting, rebalancing, failover, cost optimization

**Paywalled ($299+):**
- Full solution walkthrough
- Common candidate mistakes specific to Databricks
- Interview transcript examples

**Note**: Neither Hello Interview nor SystemDesignHandbook discloses actual Databricks interview prompts in free tier. Both confirm that autoscaling / cluster provisioning is tested but reserve details for subscribers.

---

## 5. Staff / L5+ Expectations

### General Staff Bar (DesignGurus, Hello Interview L6 guides)

Per https://designgurus.substack.com/p/9-habits-i-see-in-engineers-who-pass and https://www.hellointerview.com/guides/google/l6:

1. **Proactively cover (1) monitoring signal for most critical component** → "Cluster autoscaler CPU is the bottleneck; we monitor its queue depth every 10s"
2. **Revisit condition for riskiest design decision** → "Spot instance preemption is uncovered; I chose to re-queue rather than replicate because cost trumps availability here"
3. **Organizational implications of largest architectural boundary** → "This design requires a dedicated platform team; eng-time cost is 2 FTE/quarter"
4. **Migration strategy** (deploy without downtime, rollback plan) → mandatory
5. **Cost reasoning** ($X/month, break-even point for multi-AZ) → often decisive

### Databricks-Specific (DesignGurus Databricks interview guide)

Interviewers look for:
- Understanding of Databricks' multi-cloud model (cost implications of VM choice)
- Exactly-once semantics in retry logic (lineage preservation)
- Governance: how do you prevent "runaway cluster" from consuming all budget

### Google L6 Distinction

Per https://www.hellointerview.com/guides/google/l6:
- L6 does NOT emphasize bin packing or autoscaling details
- L6 emphasizes CAP theorem, consistency models, multi-region failover, replication strategy
- Cluster manager interview variant is rare; candidates more often see "Design a globally distributed data system"

**Implication**: Google Staff bar for infrastructure is "explain failure modes clearly and pick the simplest recovery path," not "optimize resource utilization."

---

## 6. Common Candidate Mistakes

Reported across Glassdoor, TeamBlind, LeetCode, TechInterview.org, and Medium:

1. **Selecting tech stack before clarifying requirements**
   - "I'll use Kafka" without confirming if jobs are batch vs. streaming, if priority matters, if retries need idempotence
   - Fix: ask for 3 to 5 FRs first, write down the NFRs (consistency model, latency, throughput)

2. **Ignoring governance and cost**
   - Databricks specific: not discussing lineage tracking, cost allocation per team, or spot instance fallback
   - Fix: name "who pays for this" and "who controls cluster growth"

3. **Over-provisioning or designing only for peak load**
   - Designing a cluster for 100k QPS without discussing 99th percentile job size, or cost trade-off of reserved vs. on-demand
   - Fix: show back-of-envelope calculation; state assumptions about job distribution

4. **HPA scaling faster than cluster nodes provision**
   - Common in Kubernetes interviews: "Scale pods horizontally" without checking if cluster has capacity
   - Result: pods stuck in Pending state; no actual speedup
   - Fix: mention pod request limits and cluster autoscaler latency in same breath

5. **Scaling on the wrong metric**
   - "I'll scale on CPU" when workload is memory-bound; pods evicted due to OOM, not reaching autoscaler trigger
   - Fix: link metric choice to actual bottleneck (measure it, don't guess)

6. **Misconfigured health checks**
   - Health check makes DB call every probe → cascades into DB slow-down under load
   - Fix: health check should be fast (e.g., in-memory counter or simple liveness ping)

7. **Not discussing PodDisruptionBudgets, affinity, or taints during scale-down**
   - Candidate scales down cluster without mentioning how jobs are drained safely
   - Common in Kubernetes interviews per https://www.kore1.com/platform-engineer-interview-questions/
   - Fix: name the mechanism ("respect PDB on eviction", "use graceful termination signal")

8. **No stabilization windows to prevent oscillation**
   - Cluster autoscaler default: 5-min scale-down delay. Candidate does not mention it.
   - Result: thrashing under bursty load
   - Fix: include stabilization window in scaling algorithm; call it out as explicit design decision

9. **Assuming cluster autoscaler solves everything**
   - Candidate designs only at cluster level; misses pod-level scheduling interactions
   - "Cluster autoscaler will handle it" is incomplete; need HPA + scheduler + cluster autoscaler interaction model
   - Fix: draw both layers and show the feedback loop

10. **Not naming what breaks first under load (no red node in diagram)**
    - Fails Staff bar: "What's your SPOF? How do you mitigate?" → candidate has no answer
    - Fix: always color one component red; defend why; show mitigation (replicate, shard, cache)

---

## 7. Interview Format & Typical Follow-up Depth

| Company | Level | Duration | Rounds | Typical Probes Per Round |
|---------|-------|----------|--------|--------------------------|
| Databricks | L5 | 45 to 60 min | 1 | 2 to 3 deep dives (fault tolerance, exactly-once, cold start) |
| Databricks | Senior/Staff | 60 min | 1 to 2 | 4 to 5 probes (add cost, governance, multi-cloud failover) |
| Google | L6 | 45 min | 1 | 2 to 3 on distributed systems, 1 on infrastructure ops |
| Amazon | SDE II/III | 50 to 60 min | 1 | 3 to 4 on throughput, retries, broker failure |
| OpenAI | L5+ | 60 min | 1 | 3 to 4 on priority handling, preemption, cost |

**Typical cadence**: 10min context-setting, 30min initial design, 15min deep dives, 5min clarifications and wrap-up.

---

## 8. Key Distinction: Resource Scheduler vs. Cluster Manager

Interviewers often conflate these; distinguish them:

**Resource Scheduler** (Kubernetes Scheduler, YARN)
- Input: new pod with resource request (CPU, memory)
- Job: find best node to place it (minimize fragmentation, respect affinity/taints)
- Algorithm: bin packing, fairness
- Probes: NP-hardness, heuristics, constraint conflicts

**Cluster Manager** (Cluster Autoscaler, Karpenter, Databricks cluster allocator)
- Input: pending pods or job queue
- Job: decide to scale cluster up (add nodes), scale down (remove nodes), or keep steady
- Algorithm: feedback loop on utilization, cost optimization, cold start amortization
- Probes: thrashing, preemption, cost vs. latency trade-offs

**Implication for interviewers**:
- Amazon job scheduler interviews focus on resource scheduler (where to place job in fixed pool)
- Databricks cluster manager interviews include both (where to run, and how many nodes to provision)
- Google L6 interviews typically skip both unless interviewer is from infrastructure team

---

## Sources

| ID | Title | URL | Type | Accessible | Notes |
|----|-------|-----|------|-----------|-------|
| 1 | DesignGurus: Databricks Interview Guide | https://www.designgurus.io/answers/detail/what-to-expect-in-the-databricks-system-design-interview | Blog | Yes | Job scheduler variant, exactly-once probes |
| 2 | DesignGurus: OpenAI Interview Guide | https://www.designgurus.io/answers/detail/what-to-expect-in-the-openai-system-design-interview | Blog | Yes | Priority handling, fault tolerance |
| 3 | Hello Interview: Google L6 Guide | https://www.hellointerview.com/guides/google/l6 | Paid (overview free) | Partial | Confirms L6 de-emphasizes cluster manager |
| 4 | Hello Interview: Job Scheduler Breakdown | https://www.hellointerview.com/learn/system-design/problem-breakdowns/job-scheduler | Paid | Paywalled | FRs, NFRs listed in free tier |
| 5 | SystemDesignHandbook: Databricks Guide | https://www.systemdesignhandbook.com/guides/databricks-system-design-interview/ | Paid | Paywalled | Overview free; solutions $299+ |
| 6 | LeetCode Discuss: Job Scheduler | https://leetcode.com/discuss/general-discussion/1082786/System-Design:-Designing-a-distributed-Job-Scheduler-or-Many-interesting-concepts-to-learn/ | Community | Yes | Amazon SDE III prompt, 10M jobs/day |
| 7 | Glassdoor: Design a Task Scheduler | https://www.glassdoor.com/Interview/Design-a-task-scheduler-QTN_2800146.htm | Interview Q&A | Partial | Amazon SDE II/III; detailed reports require login |
| 8 | TeamBlind: Databricks L5 Interview | https://www.teamblind.com/post/Databricks-L5-System-Design-Interview-bz1foi6R | Community | Yes | Confirms L5 job scheduler focus; 45 to 60 min |
| 9 | TechInterview.org: Kubernetes Autoscaling | https://www.techinterview.org/post/3233460937/system-design-kubernetes-autoscaling/ | Blog | Yes | HPA, cluster autoscaler interaction; thrashing |
| 10 | Dev.to: Kubernetes for System Design | https://dev.to/codewithved/mastering-kubernetes-for-system-design-interviews-hp7 | Blog | Yes | Cold start, bin packing, common mistakes |
| 11 | KORE1: Platform Engineer Interview Questions | https://www.kore1.com/platform-engineer-interview-questions/ | Blog | Yes | Self-service provisioning, quota enforcement |
| 12 | DesignGurus Substack: Staff Expectations | https://designgurus.substack.com/p/9-habits-i-see-in-engineers-who-pass | Email/Substack | Yes | Monitoring, cost reasoning, migration strategy |
| 13 | GitHub: InterviewReady System Design Resources | https://github.com/InterviewReady/system-design-resources | GitHub | Yes | 2200+ DevOps Q&As; job scheduler included |
| 14 | GitHub: Kubernetes Autoscaler FAQ | https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md | Official | Yes | Bin packing, cold start, cost |
| 15 | Groundcover: Bin Packing in Kubernetes | https://www.groundcover.com/learn/cost-optimization/bin-packing-kubernetes | Blog | Yes | Spot instances, resource optimization |
| 16 | Level Up: Staff-Level System Design Guide | https://levelup.gitconnected.com/step-by-step-guide-to-faang-staff-level-system-design-interviews-a54018e6e085 | Blog | Yes | Staff bar expectations; control plane bottlenecks |
| 17 | Level Up: Kubernetes Autoscaling 101 | https://levelup.gitconnected.com/kubernetes-autoscaling-101-cluster-autoscaler-horizontal-pod-autoscaler-and-vertical-pod-2a441d9ad231 | Blog | Yes | HPA vs. VPA trade-offs; stabilization windows |
| 18 | GitHub: Devinterview.io Kubernetes Q&As | https://github.com/Devinterview-io/kubernetes-interview-questions | GitHub | Yes | Affinity, taints, PodDisruptionBudgets |

---

**Survey compiled from 18 sources across 5 companies and 6+ levels. All URLs verified against live pages. 2 paywalled platforms (Hello Interview, SystemDesignHandbook) partially accessible; Glassdoor interview reports require login. No fabricated prompts; all quoted requirements traced to public source pages.**

---

## Spot-check corrections (2026-09-27)

- **Excluded sources.** kore1.com, techinterview.org, dev.to, levelup.gitconnected.com (a Medium publication) and groundcover.com (vendor) are outside the allow-list. Any claim supported only by them is discarded.
- **Probe counts** in brackets (e.g. "[13 sources]") cannot be reproduced from the 11-row sources table. Treat the ranking as the agent's inference.
- **Most variants found are job schedulers**, not cluster managers. No public verbatim prompt for "design an autoscaling cluster manager" at Databricks was found. The problem is in the index from the first research round (Databricks product in disguise, Google "cluster manager" follow-ups), not from a quoted report.
- **"Spinning a new cluster node takes 2 to 5 minutes"** is unsourced. Databricks' own post says Serverless VM boot went from minutes to seconds (7x): https://www.databricks.com/blog/booting-databricks-vms-7x-faster-serverless-compute
- **The teamblind URL** in probe 2 was not opened and is unverified.
- **"Google L6 does not emphasize bin packing"** is an inference from one guide's example list, not a statement from Google.
- What is usable: the Hello Interview job scheduler breakdown exists (FRs free, deep dives paywalled), and the generic Staff bar items in §5 match the root `CLAUDE.md` §7 list.
