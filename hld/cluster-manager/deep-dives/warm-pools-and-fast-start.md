# Deep dive: warm pools and fast start

> One-line answer: a start is fast only if no stage waits on the cloud, so serve starts from four tiers in cost order (free slots ~5 s, a hot pool ~6 s, a fast cold path 30 to 60 s, and VMs bought 10 minutes ahead of the calendar burst), size the hot pool as safety stock over the cold lead time (about 100 VMs per cell, 2% of the fleet, $3M to $8M a year), shrink that lead time with a slim OS, lazy images and checkpoint/restore of a warmed runtime, and buy predictable demand just in time instead of stocking it ($3k per burst, not $295k a day).

Reusable block: [`../solution.md`](../solution.md) §2 and §5.1 (the summary this file zooms into), [`../../../concepts/serverless-architecture.md`](../../../concepts/serverless-architecture.md) (Firecracker, SnapStart and its reseeding caveat), [`../../../concepts/rate-limiting-and-load-shedding.md`](../../../concepts/rate-limiting-and-load-shedding.md) (token buckets), [`provisioning-and-reconciliation.md`](provisioning-and-reconciliation.md) (the launch budget), [`bin-packing-and-placement.md`](bin-packing-and-placement.md) (tier 0 is packing headroom).

---

## 1. The start-latency budget, stage by stage

| Stage | Warm (slot or hot VM) | Cold, eager (classic) | Fast cold | What removes or shrinks it |
|---|---|---|---|---|
| Admission, placement, Raft commit, push to agent | 20 + 1 + 5 + 20 ms | same | same | Equivalence classes, in-memory scoring |
| Launch call | 0 | 1 to 3 s | 1 to 3 s | Tiers 0, 1 and 3 skip it |
| OS boot to agent-ready | 0 | up to 60 s | ~10 s (slim end of solution §2) | Slim OS |
| Image fetch | 0, cached | several minutes | a few seconds | Local cache; lazy image loading |
| Sandbox and container start | 1 to 2 s | 1 to 2 s | 1 to 2 s | microVM sandbox (Firecracker boots in 125 ms) |
| Runtime init and executor registration | 3 to 5 s, local checkpoint | several minutes | ~10 s, checkpoint fetched | Checkpoint/restore of a warmed runtime |
| **Total** | **~5 to 8 s** | **minutes** | **30 to 60 s** | |

- The control plane is ~50 ms of a 6 s start; the node is the rest. Shaving the scheduler is pointless. The levers are "no new VM" (tiers) and "a faster node" (fast cold). Warm restore is 3 to 5 s because the hot VM already holds the checkpoint on local disk; a new VM fetches it first, which is our reading of why Databricks reports ~10 s. p50 <= 10 s means most starts never see the red box below; p99 <= 60 s means at most ~1% may.

```mermaid
%% One start, two paths. The red node is the cold lead time L, which sets both the p99 and the size of the hot pool.
flowchart LR
    REQ["Start: driver + workers"] -->|"admit, place, commit, ~50 ms"| Q{"Warm capacity<br/>for the shape?"}
    Q -->|"yes: free slot or hot VM"| SB["Sandbox + restore<br/>from local checkpoint, 4 to 7 s"]
    Q -->|"no"| L["Cold lead time L = 60 s<br/>launch, boot, image, restore"]
    SB -->|"executors register"| RUN["Running, p50 ~6 s"]
    L -->|"restore ~10 s is inside L,<br/>executors register"| RUN
    class REQ,SB,RUN service
    class Q decision
    class L critical
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## 2. Four tiers: what each costs idle and which demand it serves

| Tier | Start | Cost while idle | Serves | Size |
|---|---|---|---|---|
| 0. Free slots | ~5 s | Nothing extra: it is the 15% packing headroom | Small starts, autoscale-ups | ~15% of the fleet, fragmented |
| 1. Hot pool | ~6 s | Full VM price: $3M (spot) to $8M (on-demand) a year for 300 VMs | Unforecast bursts inside L | ~100 per cell |
| 2. Fast cold | 30 to 60 s | Nothing | The ~1% tail, and refilling tier 1 | Bounded by launch tokens |
| 3. Forecast | ~5 s at T | ~15 min of VM time per burst, ~$3k at 00:00 | 00:00 and other round hours | From the job calendar |

- Tier 0 is the biggest warm tier and was never bought for latency. It serves small starts only: a 20-worker cluster with a spread limit of 5 per VM needs 4 VMs with 40 free vCPU each, rare at 85% packing. The tiers are tried in cost order, not speed order: tier 3 is as fast as tier 1 but costs 15 minutes per burst instead of 24 hours a day, so everything predictable goes there.

```mermaid
%% Which demand lands on which tier. Tier 2 is also how tier 1 refills; tier 3 moves the known burst off the cold path entirely.
flowchart LR
    D0["Small start, autoscale-up"] -->|"fits in fragments"| T0["Tier 0: free slots, ~5 s"]
    D1["Unforecast burst within 60 s"] -->|"up to ~100 VMs per cell"| T1["Tier 1: hot pool, ~6 s"]
    D2["Tail past the hot pool"] -->|"launch, 1 token per VM"| T2["Tier 2: fast cold, 30 to 60 s"]
    D3["Known round-hour burst"] -->|"bought from T - 10 min"| T3["Tier 3: forecast VMs, ~5 s at T"]
    T2 -.->|"refills, lowest band"| T1
    class D0,D1,D2,D3 client
    class T0,T2,T3 service
    class T1 cache
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

## 3. Hot pool size is safety stock

- **Formula.** `target = mean + z × sd` of unforecast net demand (ad hoc starts plus autoscale-ups minus capacity freed) in VMs per window of length L, per `(cell, shape class)`, from the same hour of the week over recent weeks (assume 4). z = 2.33 for 99%. Floor 20. The 1% of windows left uncovered is the 1% of starts the p99 <= 60 s budget lets go cold. Worked (solution §2): L = 60 s, mean 10, sd 40: `10 + 2.33 × 40 = 103`, so ~100 per cell, 300 for the region, 2% of the 16k peak fleet.
- **By hour.** At 03:00, assume mean 2 and sd 12: `2 + 28 = 30` per cell. Recompute hourly. Raising the target back to 100 costs 70 launches per cell, which queue at the lowest band behind P1 and forecast demand (solution §5.2). **A shorter lead time shrinks it.** If unforecast arrivals are roughly independent (assumption), the mean scales with L and the sd with the square root of L. L = 30 s: `5 + 2.33 × 28.3 = 71` per cell. L = 15 s: 49. Halving the cold path cuts the region's pool from 300 to ~213 VMs, ~$1.1M a year. That is Databricks sizing its warm pool from boot time. The square-root rule fails for correlated bursts (one tenant firing 200 clusters), which is why one tenant may take at most 20% of a cell's hot pool per minute (§5.6).
- **Spot vs on-demand.** Drivers need on-demand, so ~20% of the pool is on-demand (drivers are 1 in 8 containers, plus `first_on_demand` floors). An on-demand hot VM can serve anything, since spot-tolerant workers may land on it; a spot one cannot host a driver. A reclaimed idle spot VM costs only its idle minutes, plus one launch token to refill. Blended $1.49/h, $13.1k per VM-year: 300 VMs is ~$3.9M a year.

```mermaid
%% How the hot target is computed and kept. The lead time enters through the window length; demand history comes from the cell's own start records.
flowchart LR
    H[("Start records, same hour of week")] -->|"net unforecast VMs per 60 s window"| ST["mean 10, sd 40<br/>per cell, peak hour"]
    ST -->|"mean + 2.33 × sd, floor 20"| TG["Target ~100 per cell"]
    TG -->|"20% on-demand, 80% spot"| WT[("WARM_TARGET row,<br/>cell store")]
    WT -->|"shortfall"| CAP["Capacity manager"]
    CAP -->|"refill request, lowest band"| PV["Provisioner"]
    class H,WT store
    class ST,TG,CAP,PV service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
```

## 4. The calendar pre-scale

- **What the forecast holds.** At T - 15 min the job scheduler (#6) publishes, per `(cell, shape class, capacity type, T)`, the containers of every run scheduled at T sized from its last run (drivers on-demand, workers by spot policy), packed into VMs, net of expected free slots, with a confidence (share of recent runs that fired). The cluster service routes each forecast run to the cell that bought for it, so forecast and routing agree.
- **The buy.** From T - 10 min the capacity manager adds the forecast to demand and spreads the launches: 4,000 VMs over 600 s is ~7 launches/s for the region, under the 16/s refill of 8 accounts. It leaves each account's 1,000-instance burst bucket full for what nobody forecast at T: spot replacements, P1, an under-forecast. VMs register as `WARM` by T - 1 min; 5,000 starts land on them, free slots and the hot pool at p50 ~6 s. At T + 5 min, forecast VMs still idle above the hot target are released.
- **Over-forecast** (runs paused, smaller clusters): the excess idles until T + 5. 20% over is 800 VMs × 15 min, ~$600 on-demand. **Under-forecast** (new jobs, a backfill): the excess goes to tier 0, then the ~300 hot VMs, then tier 2 from the untouched burst buckets. 20% under is 800 VMs: ~300 come from the hot pool and ~500 are bought cold at 30 to 60 s, and P1 may preempt P4. Being over costs $600; being under costs latency, so bias the forecast up. **Missing forecast** (job scheduler down): fall back to the hourly seasonal baseline per shape class. A capacity error during the buy is fine: 10 minutes leaves room to fail over types (3-minute unavailable cache).

```mermaid
%% The 00:00 pre-scale. Launches are spread under the refill rate so the burst buckets stay full; the forecast error decides what happens at T.
flowchart LR
    F["Job scheduler<br/>forecast at T - 15 min"] -->|"per cell, shape, capacity type"| CAP["Capacity manager"]
    CAP -->|"from T - 10 min, ~7/s region"| PV["Provisioner, 8 accounts"]
    PV -->|"WARM by T - 1 min"| POOL["Forecast VMs"]
    POOL -->|"at T, ~5 s starts"| CHK{"Actual vs forecast"}
    CHK -->|"over: idle VMs"| REL["Release at T + 5 min,<br/>~$600 per 20% over"]
    CHK -->|"under: overflow"| OV["Hot pool, then cold<br/>from full burst buckets"]
    class F client
    class CAP,PV,POOL,REL,OV service
    class CHK decision
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## 5. The fast cold path, and what checkpoint/restore breaks

- **Why the image is the target.** Borg: median task start ~25 s, ~80% of it package installation. Slacker (FAST 2016): pulling packages is 76% of container start time, and only 6.4% of that data is read at start. So fetch blocks on first read: startup touches ~1/16 of the bytes. Databricks cut image pull from several minutes to a few seconds this way, booted its VMs 7x faster with a purpose-built OS, and cut runtime init plus JVM warm-up from several minutes to ~10 s by restoring a checkpoint of a runtime that had already loaded its libraries and run warm-up queries.
- **The hazards**, each of which ships to production if nobody names it:

| Hazard | Why it happens | Fix |
|---|---|---|
| Cloned randomness | Every restore of one checkpoint starts with the same random-number-generator state: same "random" ids, temp names, sampling seeds, and a cloned secure-random state | Reseed every generator from the kernel in a post-restore hook; create executor and app ids after restore; test by restoring twice and comparing ids |
| Stale credentials, identity, sockets | Tokens, certificates, hostname, IP and open connections captured at checkpoint time; timers jump | Checkpoint before any tenant or host identity exists and with no open connections; fetch credentials and recompute deadlines after restore; never capture the instance role |
| Runtime version skew | A checkpoint of runtime 15.4.1 restored beside 15.4.2 jars, or JIT code compiled for CPU features another family lacks (6+ spot families per shape) | Key the checkpoint by `(runtime version, image digest, CPU family)`; on a miss, full init and an alert |

```mermaid
%% Restore on a new VM. The key check stops version and CPU skew; the post-restore hook fixes what a snapshot clones.
flowchart LR
    CK[("Checkpoint store<br/>key: runtime, image digest, CPU family")] -->|"lookup"| K{"Key matches<br/>this VM?"}
    K -->|"yes"| RS["Restore warmed runtime, ~10 s"]
    K -->|"no"| FULL["Full init, minutes, alert"]
    RS -->|"post-restore hook"| HK["Reseed RNGs, new ids,<br/>fetch credentials, reconnect"]
    HK -->|"executor registers"| DRV["Spark driver"]
    class CK store
    class K decision
    class RS,FULL,HK,DRV service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## 6. The cost math: stock, just in time, stopped VMs, and a slow-start SKU

- **Stock the peak:** `4,000 × $3.07 × 24 h ≈ $295k a day`, about $108M a year, 60% of the whole fleet bill. **Buy it just in time:** `4,000 × $3.07 × 0.25 h ≈ $3k` per burst. Only the unpredictable part is stocked: 300 hot VMs, $2.9M a year all spot, $8.1M all on-demand, ~$3.9M at the 20/80 split, 2% of the $180M bill. With 15% packing headroom, that is the exchange rate for a 10 s p50 (solution §8).
- **Stopped VMs are not a free warm pool.** A stopped VM pays only for disk, but starting one is rate limited like a launch (StartInstances has its own bucket of the same size, 1,000 burst and 2 per second); it reserves no capacity and can fail with `InsufficientInstanceCapacity` exactly when the shape is scarce; the OS still boots, saving only the image fetch; and EC2 Auto Scaling warm pools do not support Spot in mixed-instance groups, while our pool is 80% spot across 6+ families. The 00:00 burst is already covered by the forecast for ~$3k. It fits scarce, expensive shapes: a GPU VM idle for an hour costs ~10x a CPU VM (solution §10.11), so disk-only plus a boot is the right trade there, with a paid capacity reservation if stock is the real risk.
- **The SKU.** A segment that accepts 60 s starts (overnight batch) skips tier 1, so its demand leaves the safety stock. If it carries 40% of unforecast demand (assumption), mean and variance fall by 40%: `6 + 2.33 × 31 = 78` per cell, ~235 for the region, 65 fewer hot VMs, ~$0.9M a year. That is the budget for the SKU's discount, and saying that number is the point.

```mermaid
%% Where the warm-capacity money goes. Predictable demand is bought per burst, only the noise is stocked, a slow-start SKU shrinks the noise, and stopped VMs suit only expensive shapes.
flowchart LR
    B["Known 00:00 burst, 4,000 VMs"] -->|"stock all day"| X["$295k a day"]
    B -->|"buy at 23:50, hold 15 min"| J["~$3k per burst"]
    N["Unforecast noise, sd 40 per cell"] -->|"z 2.33 over L"| HP["Hot pool 300 VMs, ~$3.9M a year"]
    SKU["60 s start SKU, 40% of noise"] -->|"leaves the safety stock"| HP2["Hot pool ~235, ~$0.9M a year saved"]
    GPU["GPU shape, idle 10x cost"] -->|"disk only, 1 token and<br/>no capacity promise at start"| ST["Stopped pool"]
    class B,N,SKU,GPU client
    class X,J,ST service
    class HP,HP2 cache
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

## 7. What the interviewer is testing

- That you break 10 s into stages, see the control plane is ~50 ms of it, and speed up the node and the capacity, not the scheduler.
- That the warm pool is a formula (safety stock over the lead time), recomputed hourly, split by capacity type, and priced, and that a faster cold path shrinks it.
- That you buy predictable demand just in time, keep the burst buckets for the unpredictable, know what happens when the forecast is wrong either way, and name checkpoint/restore's hazards (cloned randomness, stale credentials, version skew) and stopped VMs' limits (rate limited like launches, no reservation, no spot in warm pools).

## 8. Numbers to say out loud

- Warm 5 to 8 s, fast cold 30 to 60 s, eager cold minutes; the control plane is ~50 ms of it.
- Hot pool `10 + 2.33 × 40 ≈ 100` per cell, 300 per region, 2% of the fleet, $3M to $8M a year (~$3.9M at 20% on-demand). Halving L cuts it ~30%.
- Forecast: publish T - 15 min, buy from T - 10 min at ~7 launches/s, release at T + 5 min. $3k per burst vs $295k a day to stock it.
- Slacker 76% / 6.4%. Borg 25 s / 80%. Databricks boot 7x faster, runtime init minutes to ~10 s. Firecracker 125 ms. StartInstances has its own 1,000 burst, 2 per second bucket, the same size as RunInstances'.
