# Diagrams: MapReduce, a distributed batch processing framework

The D1 to D12 set from `hld/CLAUDE.md` §4. A diagram is drawn once. The ones embedded in [`solution.md`](solution.md) are linked here, not repeated. Red is used for one thing only: the **shuffle service**, where M x R small random reads break first (7.8 B blocks of ~12.8 KB, ~1.8 h of seeks for the 100 TB sort).

| # | Diagram | Where |
|---|---|---|
| D1 | Context | [below](#d1-context-zoom-out) |
| D2 | Data flow with rates | [below](#d2-data-flow-dfd) |
| D3 | Final design | [`solution.md` §6](solution.md#6-final-design-and-the-six-core-flows). Zoom-in: [one worker node](#d3a-zoom-in-inside-one-worker-node) |
| D4 | Happy path per FR | FR1 + FR3 pull path: [`solution.md` §4.3](solution.md#43-group-by-key-across-machines-and-run-the-reduce-phase). FR5: [§4.5](solution.md#45-share-the-cluster-between-teams). FR2: [below](#d4-fr2-map-phase-with-locality-and-delay-scheduling). FR3 push-merge: [`solution.md` §6 Flow 2](solution.md#flow-2-sort-100-tb-on-1000-nodes-with-push-merge-15-min). FR4 is the failure set in D5 |
| D5 | Failure paths | Map host dies: [`solution.md` §4.4](solution.md#44-survive-failure). Node loss timeline and RM failover: [§10.4](solution.md#104-failure-timeline). New below: [merger lost after finalize](#d5-merger-node-lost-after-finalize), [job master dies in job commit](#d5-job-master-dies-during-job-commit), [duplicate mapDone from a backup](#d5-duplicate-mapdone-from-a-backup) |
| D6 | Decision flows | Speculation: [`solution.md` §5.2](solution.md#52-one-slow-machine-must-not-add-more-than-10-stragglers). Commit gate: [§5.4](solution.md#54-output-equals-one-failure-free-run-and-appears-all-at-once-commit-object-stores-non-determinism). New: [fetch failure vs node loss](#d6-fetch-failure-or-node-loss) |
| D7 | Entity relationship | [`solution.md` §3.3](solution.md#33-data-model) |
| D8 | State machines | Job: [`solution.md` §4.1](solution.md#41-submit-a-job-and-get-its-output). Task attempt: [below](#d8-task-attempt-lifecycle) |
| D9 | Deployment | Control plane zoom-in: [`solution.md` §5.5](solution.md#55-no-single-master-failover-under-30-s-100k-jobsday-control-plane-availability-and-scale). Racks: [below](#d9-deployment-racks-and-control-hosts) |
| D10 | Partitioning | Shuffle block count: [`solution.md` §5.1](solution.md#51-sort-100-tb-on-1000-nodes-in-under-30-minutes-the-shuffle). Partitioners and the hot key: [below](#d10-partitioners-and-the-hot-key) |
| D11 | Failure mode map | [below](#d11-failure-mode-map) |
| D12 | Rollout from Hadoop 1 | [below](#d12-rollout-from-the-hadoop-1-jobtracker) |

## D1. Context (zoom-out)

Our system is one box: submit two functions, get R output files that appear all at once.

```mermaid
%% D1: context. The MapReduce service as one box. Storage, identity and paging are outside it.
flowchart LR
    ENG[Data engineers<br/>CLI, notebooks] -->|"submit jar + conf, poll, kill"| MR[MapReduce service<br/>4,000 nodes, 100k jobs/day]
    WF[Workflow scheduler<br/>chains jobs] -->|"POST /jobs with request_id"| MR
    MR -->|"job finished event"| WF
    MR -->|"read 10 PB/day, write 1 PB/day"| DFS[(Distributed file system<br/>or object store)]
    MR -->|"authenticate, delegation tokens"| IDP[Identity<br/>Kerberos or OIDC]
    MR -->|"metrics, logs, alerts"| OBS[Metrics and paging]
    DS[Downstream readers<br/>query engine, ML training] -->|"read output after _SUCCESS"| DFS
    OPS[Fleet ops] -->|"add, drain, retire nodes"| MR
    class ENG,WF,DS client
    class MR service
    class DFS,IDP,OBS,OPS external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- The DFS ([`../distributed-file-system/`](../distributed-file-system/)) and the workflow scheduler ([`../distributed-job-scheduler/`](../distributed-job-scheduler/)) are other problems. We refused to build either, or a DAG engine.

## D2. Data flow (DFD)

Daily bytes and rates on every edge. Shuffle bytes are 30% of input but cost the most: tiny random reads, and ~97% cross a rack uplink (a reducer's 1,000 source nodes sit on 25 racks).

```mermaid
%% D2: data flow for the whole cluster per day. Averages over 86,400 s, peak 3x [estimate]. Stores are cylinders, processes are rounded.
flowchart LR
    CL[Client or<br/>workflow scheduler] -->|"job spec, JSON ~2 KB, 12/s peak"| JSV(Job service)
    JSV -->|"job row ~1 KB, 100k/day"| JDB[(Job store)]
    JSV -->|"admit, launch job master"| JM(Job master<br/>one per job)
    DIN[(DFS input)] -->|"128 MB splits, 10 PB/day,<br/>~116 GB/s avg, ~350 GB/s peak"| MAP(Map tasks<br/>~78 M/day)
    JM -->|"task launches, ~2,700/s peak"| MAP
    MAP -->|"mapDone sizes per partition,<br/>~1.25 KB, ~900/s avg"| JM
    JM -->|"journal events ~200 B,<br/>~16 GB/day [estimate]"| JR[(Journal on DFS)]
    MAP -->|"sorted runs + index, compressed,<br/>3 PB/day, ~35 GB/s"| LD[(Local disks<br/>map output)]
    LD -->|"index lookup + seek,<br/>~12.8 KB blocks in big jobs"| SS(Shuffle service<br/>per node)
    MAP -->|"one ~128 KB batched push per merger,<br/>1,000 per map, big jobs only"| SS
    SS -->|"partition segments, 3 PB/day,<br/>~97% cross a rack uplink"| RED(Reduce tasks)
    RED -->|"part files, 1 PB/day,<br/>x3 replicas = 3 PB/day of disk"| DOUT[(DFS output)]
    DOUT -->|"only after _SUCCESS or manifest"| DS[Downstream readers]
    class CL,DS client
    class JSV,JM,MAP,RED service
    class JDB,DIN,JR,LD,DOUT store
    class SS critical
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D3a. Zoom-in: inside one worker node

The final design is [`solution.md` §6](solution.md#6-final-design-and-the-six-core-flows). Inside each node, the shuffle service outlives every task, so a crashed or preempted container loses nothing it finished. It does the random reads, so it is red.

```mermaid
%% D3a: one worker node. 32 vCPU, 128 GB, 12 x 8 TB HDD. The shuffle service serves pulls and merges pushes.
flowchart LR
    subgraph NODE["Worker node"]
        NA[Node agent<br/>launch, cgroups, kill]
        MT[Map containers]
        RT[Reduce containers]
        SS[Shuffle service<br/>port 13562, sendfile]
        MG[Merger<br/>one file per partition]
        PC[Page cache<br/>~40 GB free]
        LD[(12 HDDs, ~1,200 random reads/s<br/>map output + merged files)]
        DN[(DFS data node)]
    end
    NA -->|"heartbeat 1 s, free resources"| RM[Resource manager]
    NA -->|"start, stop"| MT
    MT -->|"local 128 MB split read"| DN
    MT -->|"file + index"| LD
    MT -->|"push slices"| OTH[Shuffle services<br/>on other nodes]
    OTH -->|"pushed slices for my partitions"| MG
    MG -->|"append at offset"| LD
    OTH -->|"fetch partition p"| SS
    SS -->|"read index, seek"| PC
    PC -->|"miss"| LD
    RT -->|"read merged partition"| SS
    RT -->|"temp part file"| DN
    class NA,MT,RT,MG,RM,OTH service
    class LD,DN store
    class PC cache
    class SS critical
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D4. FR2: map phase with locality and delay scheduling

The RM skips a job for a few seconds rather than give it a slot with no local data. Reduces never wait: they read from every node anyway.

```mermaid
%% D4 for FR2: one map task placed node-local through delay scheduling, then sort, spill, merge, mapDone.
sequenceDiagram
    autonumber
    participant JM as Job master (job A)
    participant RM as RM scheduler
    participant N9 as Node N9 (no replica)
    participant N7 as Node N7 (holds replica)
    participant MT as Map task m_7
    JM->>JM: plan 780k splits, 3 replica hosts each
    JM->>RM: allocate(asks per host, per rack, any)
    N9->>RM: heartbeat, 1 slot free
    RM->>RM: A is next in fair order but has no split on N9, skip A
    RM-->>N9: slot goes to job B, which has local data on N9
    N7->>RM: heartbeat, 1 slot free
    RM-->>JM: container on N7, node-local
    JM->>JM: pick a pending split with a replica on N7, m_7
    JM->>MT: launch m_7 in the N7 container, token carries jm_attempt
    MT->>N7: read 128 MB split from the local data node
    MT->>MT: map, 100 MB buffer, spill at 80%, combine, merge spills
    MT->>N7: write file.out + file.out.index
    MT->>JM: mapDone(m_7 a0, N7, sizes per partition)
    Note over JM,RM: no node-local slot after W1 = 5 s, accept rack-local, after W2 accept any node
```

- Facebook's measurement: W1 = 1 s gave 68% to 80% locality for small jobs, 5 s gave "nearly perfect locality" ([EuroSys 2010](https://people.csail.mit.edu/matei/papers/2010/eurosys_delay_scheduling.pdf)). W2 is a few seconds more [estimate].

## D5. Merger node lost after finalize

Losing one merger costs seconds: only its 10 of 10,000 partitions fall back to pull, and merged data is a second copy, never the only one.

```mermaid
%% D5: node H dies after finalize. It held merged p70 to p79 and 780 original map outputs.
sequenceDiagram
    autonumber
    participant JM as Job master
    participant H as Node H (merger p70 to p79)
    participant R as Reducer r_77 on node X
    participant SS as Shuffle services (999 nodes)
    participant W as Re-run nodes
    Note over JM,H: finalize done, MergeStatus says p70 to p79 merged on H
    JM->>R: launch r_77 at finalize (slowstart 1.0), on X in H's rack
    Note over H: power loss
    R->>H: read merged p77, next 2 MB chunk
    H--xR: connection refused
    R->>R: drop merged data, switch to the unmerged block list
    R->>SS: fetch p77 slices of 779,220 maps, batched per host
    SS-->>R: segments, 780 random reads per node for this partition
    R->>JM: fetchFailed for the 780 maps whose output was on H
    JM->>JM: refused from 3+ reducers on 2+ racks, mark H lost
    JM->>W: re-run 780 maps, no push since the shuffle is finalized
    R->>W: fetch p77 slices of the re-run maps
    Note over R,W: 10 partitions fall back, 7,800 extra random reads per surviving node, ~6.5 s
```

## D5. Job master dies during job commit

Job commit on HDFS builds a `publish/` staging directory from the journal (only `commit_done` attempts), then does one rename of it to `output_path`, so it either landed or did not. A new job master checks which, and redoes it from the journal.

```mermaid
%% D5: HDFS job commit. Job master attempt 1 dies after journaling job_commit_started, before _SUCCESS.
sequenceDiagram
    autonumber
    participant JM1 as Job master attempt 1
    participant RM as Resource manager
    participant JM2 as Job master attempt 2
    participant D as DFS (journal, output)
    JM1->>D: journal job_commit_started, all 10,000 tasks commit_done
    JM1->>D: rename staging dir to output_path, one metadata op
    Note over JM1: container dies, no _SUCCESS yet
    JM1--xRM: allocate heartbeats stop
    RM->>RM: 60 s AM expiry, start attempt 2
    RM->>JM2: launch with jm_attempt 2
    JM2->>D: replay journal, job_commit_started, no job_commit_done
    JM2->>D: does output_path exist with this job's files?
    D-->>JM2: yes, the rename landed
    JM2->>D: write _SUCCESS only, journal job_commit_done
    Note over JM2,D: if output_path were absent, redo the rename from the staging dir
    JM2->>RM: unregister, job SUCCEEDED
```

- Readers never see half an output: the rename is atomic. Hadoop's v1 moves files one by one, which is why a crash there leaves parts visible without `_SUCCESS`.
- On an object store the same shape holds with one conditional put of the job manifest. A zombie attempt 1 is fenced by the RM killing its container, and its rename fails because `output_path` already exists.

## D5. Duplicate mapDone from a backup

The job master keeps the first `mapDone`. The merger keeps the first push. They can come from different attempts, so mergers tag slices with the attempt id and finalize keeps only the recorded attempt. Non-deterministic jobs (`conf.map.deterministic = false`) also get durable map output and push-merge off.

```mermaid
%% D5: map m_9 has a slow original a0 and a backup a1. Both finish and both pushed.
sequenceDiagram
    autonumber
    participant JM as Job master
    participant A0 as m_9 a0 (slow node S)
    participant A1 as m_9 a1 (backup, node F)
    participant MG as Merger p70 to p79
    participant R as Reducer r_77
    JM->>A1: launch backup, a0 has the longest time left
    A0->>MG: push slices of p70 to p79
    MG->>MG: map 9 not in bitmap, append to disk, tag attempt a0
    A1->>MG: push the same slices
    MG->>MG: map 9 already in bitmap, drop
    A1->>JM: mapDone(m_9 a1, F, sizes)
    JM->>JM: first mapDone wins, journal m_9 at F, kill a0
    A0->>JM: mapDone(m_9 a0, S, sizes)
    JM-->>A0: ignored, task done, container killed
    JM->>MG: finalize, keep only slices from recorded attempts
    MG-->>JM: MergeStatus p77, map 9 excluded (a0 is not the recorded attempt)
    JM->>JM: journal shuffle_finalized
    R->>JM: where is partition 77
    JM-->>R: merged file without map 9, m_9 unmerged at F
    R->>MG: read merged p77
    R->>A1: fetch p77 slice of m_9 from F
    Note over R,A1: every byte the reducer reads comes from the attempt the job master recorded
```

## D6. Fetch failure or node loss

Job master logic for one fetch failure report. In a pull shuffle the shuffle service is the bottleneck, so its timeouts are load, not death. Re-running 780 maps would only add load.

```mermaid
%% D6: deciding between back-off, re-running one map output, and declaring a node lost.
flowchart TD
    A[Reducer reports fetchFailed<br/>map m on host H] --> B{Error type?}
    B -->|"timeout or busy"| C[Back off with jitter, retry,<br/>do not re-run m]
    C -->|"5 timeouts in a row"| D
    B -->|"refused or unreachable"| D{3+ reducers on<br/>2+ racks report H?}
    D -->|"under 3 reports"| F[Retry same host,<br/>count the report]
    D -->|"all on one rack"| E[Suspect the reporters' uplink,<br/>alert, keep H]
    D -->|"yes"| G{Node agent heartbeat<br/>also missing?}
    N[RM node expiry, 60 s] -->|"node lost event"| I
    G -->|"no, agent alive"| H2[Shuffle service down:<br/>re-run reported maps only]
    G -->|"yes"| I[Mark H lost: all its map outputs<br/>and attempts, no 60 s wait]
    H2 --> J{Needed partitions of m<br/>in a live merged file?}
    I --> J
    J -->|"yes"| K[No re-run for m]
    J -->|"no"| L[Re-run m, publish<br/>the new location]
    class B,D,G,J decision
    class A,C,E,F,H2,I,K,L,N service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D8. Task attempt lifecycle

Follows the ATTEMPT states in the [erDiagram](solution.md#33-data-model). KILLED never counts toward the 4-attempt limit. FAILED does. Preemption (45 s below guarantee, ask first, 10 s grace, then kill) never picks a job master or a COMMIT_PENDING attempt, and takes maps before reduces, youngest first.

```mermaid
%% D8: one task attempt. Map attempts end at mapDone, reduce attempts pass through the commit gate.
stateDiagram-v2
    direction LR
    [*] --> STARTING: container granted
    STARTING --> RUNNING: first heartbeat
    STARTING --> FAILED: launch error
    RUNNING --> SUCCEEDED: map, mapDone kept
    RUNNING --> COMMIT_PENDING: reduce asks canCommit
    COMMIT_PENDING --> SUCCEEDED: yes, task commit done
    COMMIT_PENDING --> KILLED: no, another won
    COMMIT_PENDING --> FAILED: died mid-commit
    RUNNING --> FAILED: crash or 600 s silent
    RUNNING --> KILLED: preempted, race, zombie
    SUCCEEDED --> KILLED: map output lost
    SUCCEEDED --> [*]
    FAILED --> [*]
    KILLED --> [*]
```

- `SUCCEEDED --> KILLED` is maps only: node loss deletes a finished map's output. A committed reduce never leaves SUCCEEDED. `died mid-commit`: the gate said yes (journal `commit_granted`), the attempt died before its rename (no `commit_done`). The job master checks for the committed task dir, else reopens the gate. Losers are told to stop but killed only after `commit_done`, so a backup survives a winner that dies mid-rename.

## D9. Deployment: racks and control hosts

One region, 100 racks of 40 nodes. Shuffle crosses racks. Nothing crosses regions.

```mermaid
%% D9: placement. Control hosts run no tasks. Job masters run in ordinary containers on worker racks.
flowchart TB
    subgraph CTRL["Control hosts, 3 racks, no tasks"]
        RMA[RM active]
        RMS[RM standby]
        ZK[(ZooKeeper x5<br/>over 3 racks)]
        NN[DFS metadata<br/>active + standby]
    end
    subgraph R1["Rack 1 of 100"]
        N1[40 worker nodes<br/>node agent, shuffle service,<br/>DFS data node, tasks]
        JMA[Job master job A<br/>in a container]
    end
    subgraph R2["Rack 2 to 100"]
        N2[3,960 worker nodes]
    end
    SP[Spine switches]
    RMA -->|"leader lock, app state"| ZK
    RMS -->|"watch lock"| ZK
    N1 -->|"heartbeat 1 s"| RMA
    JMA -->|"allocate 1 s"| RMA
    N1 -->|"400 Gbps uplink, 2.5:1"| SP
    SP -->|"shuffle, DFS replicas 2 and 3"| N2
    N1 -->|"block reports"| NN
    class SP client
    class RMA,RMS,N1,N2,JMA service
    class ZK store
    class NN external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- Replication: DFS 3x (one replica on the writer's rack, two off-rack), ZooKeeper 5 over 3 racks (losing the rack with 2 leaves a quorum of 3), RM 2, job service 3 and job store 2 on the same control hosts. Map output 1x by design. Rack uplink math: 40 nodes x 100 GB out = 4 TB per rack through 50 GB/s = ~80 s for the sort. Fine.

## D10. Partitioners and the hot key

Hash needs no pre-pass but gives no global order. A sampled range gives a total order (TeraSort) but breaks on a stale sample. Neither splits one hot key. Detail: [`solution.md` §5.3](solution.md#53-one-key-holds-20-of-the-data-skew).

```mermaid
%% D10: how map output keys become R partitions, and where a hot key lands. The hot partition is a decision point, not the red node.
flowchart LR
    K[Map output record<br/>key k] --> P{Partitioner}
    P -->|"hash k mod R, default"| H[R = 2,000 hash buckets<br/>word count, joins]
    P -->|"sort jobs"| S[Pre-pass sample ~1 M keys<br/>9,999 split points]
    S -->|"R = 10,000 ranges, ~10 GB each"| RG[Range partitions<br/>ordered across part files]
    RG -->|"hot key in a sort"| F4[Sort on key plus record_id,<br/>equal keys spread to neighbours]
    H -->|"mapDone sizes show it"| HOT{Partition 42<br/>20 TB vs 10 GB median}
    HOT -->|"algebraic reduce"| F1[Combiner on map side<br/>780k partials, a few MB]
    HOT -->|"declared join"| F2[Salt k into N sub-keys,<br/>copy small side N times]
    HOT -->|"holistic reduce"| F3[Sketch per partial,<br/>or accept the long task]
    class K client
    class P,HOT decision
    class H,S,RG,F1,F2,F3,F4 service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D11. Failure mode map

One tree: component and failure on the edge, blast radius in the middle, mitigation at the leaf. Red is what breaks first under load. The widest blast radius is a bad release, contained by versioning the framework per job.

```mermaid
%% D11: each component, what fails, blast radius, mitigation. Only the shuffle service is red.
flowchart TD
    ROOT[Failure in a<br/>4,000-node cluster] -->|"worker node dies"| A1[Its attempts + 780 map outputs,<br/>under 1 min in map phase,<br/>up to ~5 min in reduce wave] --> A2[Fetch-failure fast path,<br/>re-run maps over 999 nodes]
    ROOT -->|"rack switch dies"| B1[40 nodes, 1% of cluster,<br/>their map outputs] --> B2[Rack-aware DFS replicas,<br/>re-run that rack's maps]
    ROOT -->|"shuffle service saturated"| C1[7.8 M random reads per node,<br/>~1.8 h, every big job]
    C1 --> C2[Push-merge per job,<br/>page cache for medium jobs]
    ROOT -->|"job master dies"| D1[One job, in-flight attempts] --> D2[Journal replay incl. shuffle_finalized,<br/>4 attempts, never preempted]
    ROOT -->|"active RM dies"| E1[No new containers ~20 to 30 s,<br/>tasks keep running] --> E2[Standby via ZooKeeper,<br/>work-preserving restart]
    ROOT -->|"ZooKeeper quorum lost"| F1[No RM failover possible] --> F2[5 servers over 3 racks,<br/>page cluster team]
    ROOT -->|"bad framework release"| G1[Every job on that version,<br/>widest blast radius] --> G2[Library per job,<br/>canary 1%, pin to old]
    class ROOT client
    class A1,B1,D1,E1,F1,G1 decision
    class A2,B2,C2,D2,E2,F2,G2 service
    class C1 critical
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout from the Hadoop 1 JobTracker

Move nodes, then queues, then features. Every phase can be undone without touching committed output.

```mermaid
%% D12: Hadoop 1 (one JobTracker, fixed slots) to RM + job master per job. A rollback point closes each phase.
gantt
    title Hadoop 1 JobTracker to RM plus per-job job masters
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Foundations
    Control hosts, ZooKeeper x5, RM pair, job store   :a1, 2026-11-02, 21d
    Rollback point, nothing runs on it yet            :milestone, m1, after a1, 0d
    section Nodes
    Drain 10 pct of TaskTrackers, start node agents   :b1, after a1, 14d
    Shadow run top 10 jobs per team, diff part files  :b2, after b1, 21d
    Rollback point, reimage nodes as TaskTrackers     :milestone, m2, after b2, 0d
    section Queues
    Move queues one at a time, grow node share        :c1, after b2, 42d
    Rollback point, point a queue back to JobTracker  :milestone, m3, after c1, 0d
    Retire JobTracker, keep binaries 30 days          :c2, after c1, 14d
    section Features
    60 s node expiry, AM recovery, 4 AM attempts      :d1, after c1, 14d
    Rollback point, restore defaults per queue        :milestone, m4, after d1, 0d
    Push-merge auto for big jobs, canary 1 pct        :d2, after d1, 28d
    Manifest committer for object store outputs       :d3, after d1, 21d
    Rollback point, per-job conf flags off            :milestone, m5, after d2, 0d
```

- Rollback never needs a data backfill. A job's output is committed or absent, and each job runs on one framework version. Gantt takes no classDefs, so this one is uncolored.
