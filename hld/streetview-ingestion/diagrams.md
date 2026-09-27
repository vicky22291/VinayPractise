# Diagrams: Google Maps Street View ingestion and storage

The D1 to D12 set from `hld/CLAUDE.md` §4, each drawn once: the diagrams already embedded in [`solution.md`](solution.md) are linked here, not repeated.

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [`solution.md` §6](solution.md#6-final-design-and-the-core-flows) |
| D4 | Happy path per FR | FR1 car-day: [Flow 1](solution.md#flow-1-a-car-day-lands-fr1). FR2 and FR3: [Flow 2](solution.md#flow-2-landed-to-published-fr2-fr3). FR4: [Flow 3](solution.md#flow-3-a-user-opens-a-panorama-fr4). FR5: [Flow 4](solution.md#flow-4-an-approved-blur-request-fr5). FR1 contributor photo: below |
| D5 | Failure paths | Depot uplink down: [Flow 5](solution.md#flow-5-the-depot-uplink-dies-failure). Station crash mid-drive, zombie worker fenced, CDN invalidation fails: below |
| D6 | Decision flow | Ingest station per cartridge: [§5.1](solution.md#51-how-do-you-move-14-pb-a-day-off-1000-cars-without-ever-losing-a-drive). Metadata lookup, publisher per chunk: below |
| D7 | Entity relationship | [`solution.md` §3.3](solution.md#33-data-model) |
| D8 | State machines | Drive lifecycle, panorama lifecycle: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

The whole system is one box. Cars and contributors push bytes in, Maps users pull blurred pixels out, and fleet ops, privacy reviewers, the road graph and KMS sit around it.
```mermaid
%% D1: context. Our system is one box. Every external actor and what flows on each edge.
flowchart LR
    CAR[Camera cars<br/>1,000, ~150 km a day]:::client -->|"cartridges, ~1.4 TB per car-day,<br/>rig-signed manifest"| SYS[Street View imagery system<br/>ingest, process, publish, serve]:::service
    CON[Contributors]:::client -->|"Photo Sphere, 2:1, up to 75 MB,<br/>pose, capture time"| SYS
    USR[Maps users]:::client -->|"point and date lookups, 60k/s peak,<br/>blur reports"| SYS
    SYS -->|"metadata JSON,<br/>blurred tiles ~1 M/s"| USR
    FLEET[Fleet ops and route planner]:::external -->|"courier cartridges<br/>when the uplink is thin"| SYS
    SYS -->|"dead-letter drives,<br/>roads to re-drive"| FLEET
    PRIV[Privacy reviewers]:::external -->|"house blur approvals,<br/>retention per country"| SYS
    ROAD[Maps road graph]:::external -->|"segments, junctions<br/>for pose snap and slots"| SYS
    KMS[Key management service]:::external -->|"fleet public key for rigs,<br/>unwrap and re-wrap drive keys"| SYS
    SYS -->|"blurred masters, poses,<br/>never raw"| DOWN[3D, Immersive View,<br/>ML extraction]:::external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Names, formats, sizes and rates on every edge. The station only moves ciphertext. Raw is ~1.35 TB per drive, a published panorama ~27 MB.
```mermaid
%% D2: data flow. Stores are cylinders, processes are rounded boxes. Rates are fleet-wide at 1,000 cars.
flowchart LR
    CART[(Cartridge + mirror<br/>4 TB NVMe, 8 TB until LANDED)]:::store -->|"segments encrypted on the rig,<br/>1 GB + CRC32C, 27 TB per depot a night"| ST(Depot ingest station):::critical
    ST -->|"ciphertext segments, 1 GB,<br/>~1.4 M a day, 15.6 GB/s averaged"| LB[(Landing bucket)]:::store
    ST -->|"signed manifest + wrapped key,<br/>~1,000 drives a day"| REG[(Drive registry)]:::store
    REG -->|"drive.landed event,<br/>~1,000 a day"| WF(Per-drive workflow):::service
    LB -->|"raw segments,<br/>~1.35 TB per drive"| WF
    LB -->|"day 30 lifecycle,<br/>~1.35 PB a day at peak"| AR[(Raw in Archive<br/>key shred at 180 d)]:::store
    BR[(Blur registry)]:::store -->|"footprints by S2 cell"| WF
    WF -->|"JPEG tiles, ~40 KB, ~683 per pano,<br/>~405 TB a day"| TB[(Tiles bucket)]:::store
    WF -->|"PANORAMA rows STAGED, ~1 KB,<br/>15 M a day, ~170/s"| IDX[(Panorama index)]:::store
    TB -->|"tile manifest,<br/>one HEAD per pano"| PUB(Publisher):::service
    PUB -->|"chunk txn, ~100 panos per 1 km,<br/>~1.7 txn/s"| IDX
    IDX -->|"range scans on cache miss,<br/>~6k reads/s"| API(Metadata API + cache):::service
    API -->|"metadata JSON,<br/>60k req/s peak"| U[Maps client]:::client
    TB -->|"CDN fill on miss,<br/>~100k tiles/s, 4 GB/s"| CDN[(CDN edge)]:::cache
    CDN -->|"JPEG tiles, ~1 M/s,<br/>~320 Gbps"| U
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D4. Contributor photo upload (FR1, small)

A Photo Sphere is a drive of one segment: start upload, bytes to a URL, create, then the same pipeline and publisher as a car-day.
```mermaid
%% D4 (FR1, contributor): start, bytes, create, LANDED, pipeline, publish. Same registry, same blur stage, same slot rule.
sequenceDiagram
    autonumber
    participant C as Contributor app
    participant A as Publish API
    participant R as Drive registry
    participant B as Landing bucket
    participant W as Pipeline
    participant T as Tiles bucket
    participant P as Publisher
    participant I as Panorama index
    C->>A: photo.startUpload, size, CRC32C
    A->>R: per-account rate limit ok, register a drive of one segment
    R-->>A: drive_id, write-only credential for one object
    A-->>C: upload URL
    C->>B: PUT bytes, up to 75 MB, CRC32C checked at write
    C->>A: photo.create, upload ref, pose, capture time
    A->>A: check 2:1 aspect, at least 7.5 MP, not at sea, within 50 km of EXIF GPS
    A->>R: complete, registry checks size and CRC in the bucket, LANDED, emit drive.landed
    A-->>C: photo id, processing
    R->>W: drive.landed, same workflow as a car-day
    W->>W: pose, blur with detector and registry footprints, moderation
    W->>T: tiles v1, tile manifest last
    W->>I: PANORAMA row STAGED
    P->>T: HEAD tile manifest
    P->>I: txn, move slot pointer only if newest capture, epoch check
```

## D5. Ingest station crashes mid-drive

The station trusts the registry, not its own log: it re-registers, gets the missing list, resumes the half-sent segment and skips every verified one.
```mermaid
%% D5: failure path. Crash during segment 701 of 1,400. Registration and upload are idempotent, so a restart is the whole recovery.
sequenceDiagram
    autonumber
    participant S as Depot station
    participant R as Drive registry
    participant B as Landing bucket
    Note over S,B: drive D registered, seq 1 to 700 uploaded, station holds ciphertext only
    S->>B: resumable PUT raw/D/701.seg, chunk 5 of ~16
    Note over S,B: station loses power, cartridge still in its bay, nothing wiped
    S->>R: register drive D again, same signed manifest
    R-->>S: drive_id exists, status UPLOADING, fresh credential
    S->>R: complete
    R->>B: list raw/D/, compare sizes and CRCs with manifest
    R-->>S: not LANDED, missing seq 701 to 1,400
    S->>B: resume the seq 701 session, ask committed offset
    B-->>S: 256 MiB committed, send the remaining 64 MiB chunks
    loop seq 702 to 1,400, 16 in parallel
        S->>B: create-only PUT, ifGenerationMatch=0
    end
    S->>R: complete
    R->>R: all 1,400 match, one txn, LANDED, emit drive.landed
    R-->>S: LANDED
    S->>S: wipe cartridge, return it to the pool
```

## D5. Zombie worker fenced at publish

A publish worker stalls past its lease. The new owner finishes the drive, and the zombie's late transaction fails the epoch check.
```mermaid
%% D5: failure path. Two workers believe they own drive D. Only the holder of the current lease_epoch can commit a chunk.
sequenceDiagram
    autonumber
    participant O as Orchestrator
    participant A as Worker A
    participant B as Worker B
    participant I as Index and PIPELINE_RUN
    O->>A: lease drive D publish, epoch 7
    A->>I: txn chunk 1, epoch 7 matches, commit
    Note over A,B: A stalls, heartbeats stop, lease expires
    O->>I: bump lease_epoch to 8
    O->>B: lease drive D publish, epoch 8
    B->>I: txn chunk 1, epoch 8, already CURRENT, no-op
    B->>I: txns chunks 2 to 40, epoch 8, commit
    Note over A,B: A wakes up, still believes it holds epoch 7
    A->>I: txn chunk 2, epoch 7
    I-->>A: abort, lease_epoch is now 8
    A->>A: drop the work, exit
    B->>I: txns chunks 41 to 150, epoch 8, commit
    B-->>O: publish done, orchestrator marks drive D PUBLISHED in the registry
```

## D5. CDN invalidation fails during a takedown

Order is bump, delete at origin, invalidate, verify. The first invalidation is rejected, the verification GET keeps returning 200, and the panorama is not done until it returns 404.
```mermaid
%% D5: failure path. The takedown checklist for one panorama P, with the CDN rejecting the first invalidation.
sequenceDiagram
    autonumber
    participant K as Takedown job
    participant I as Panorama index
    participant T as Tiles bucket
    participant E as CDN
    participant OC as On-call
    Note over K,E: request APPROVED, P is at tile_version 3
    K->>T: write v4 at all zooms, tile manifest last
    K->>I: txn tile_version 3 to 4, blur_version +1
    K->>T: hard delete v3 objects, soft delete is off
    K->>E: invalidate /P/v3/*
    E-->>K: rejected, 500 requests a minute used up
    K->>E: verify GET /P/v3/0/0_0.jpg
    E-->>K: 200, the edge still holds v3, max-age 30 days
    K->>K: P not done, request stays APPROVED, back off
    opt still 200 near the 24 h SLO
        K->>OC: page, takedown SLO at risk
    end
    K->>E: invalidate /P/v3/*, retry
    E-->>K: accepted, takes effect in ~10 s
    K->>E: verify GET /P/v3/0/0_0.jpg
    E->>T: miss, fetch from origin
    T-->>E: 404, deleted before the invalidation, so no refill
    E-->>K: 404
    K->>K: P done, request APPLIED once all 17 panoramas return 404
```

## D6. Metadata lookup decision flow

One lookup: cache first, then 1 to 4 short range scans, widen once, else 404.
```mermaid
%% D6: decision flow inside the metadata API for GET panos:lookup.
flowchart TD
    REQ[lookup lat, lng,<br/>radius 50 m, date optional]:::service -->|"quantize to S2 L20"| C{cell + date bucket<br/>in cache?}:::decision
    C -->|"hit, ~90%"| RET[return cached answer]:::cache
    C -->|"miss"| D{date given?}:::decision
    D -->|"no"| CUR[scan 1 to 4 L16 cells,<br/>keep status CURRENT]:::service
    D -->|"yes"| AT[scan 1 to 4 L16 cells, newest<br/>CURRENT or HISTORICAL per slot<br/>at or before date]:::service
    CUR -->|"candidate rows"| N{nearest pano<br/>within radius?}:::decision
    AT -->|"candidate rows"| N
    N -->|"yes"| L[read neighbour slots,<br/>build arrows]:::service
    L -->|"pano, links, tile_version"| PUT[cache put, TTL 5 min,<br/>return 200]:::cache
    N -->|"no"| W{already widened?}:::decision
    W -->|"no"| WIDE[widen to 100 m,<br/>re-cover with L16 cells]:::service
    WIDE -->|"new covering"| D
    W -->|"yes"| NF[404, no imagery here]:::external
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D6. Publisher decisions per chunk

Tiles first, then the blur_version guard, then the fence, then one rule per panorama: current means newest capture, not newest publish. One transaction per 1 km chunk.
```mermaid
%% D6: decision flow inside the publisher for one 1 km chunk of ~100 STAGED panoramas.
flowchart TD
    CH[next 1 km chunk,<br/>~100 STAGED panos]:::service -->|"pano ids"| TM{HEAD tile manifest,<br/>present for every pano?}:::decision
    TM -->|"no"| HOLD[hold chunk, re-run the<br/>tile shard, retry later]:::service
    TM -->|"yes"| BV{output blur_version at<br/>least the current one?}:::decision
    BV -->|"no, old outputs"| RB[re-blur with the<br/>current registry first]:::service
    RB -->|"new tiles + manifest"| TM
    BV -->|"yes, open txn"| EP{lease_epoch matches<br/>PIPELINE_RUN?}:::decision
    EP -->|"no"| AB[abort txn,<br/>zombie fenced]:::external
    EP -->|"yes"| SAME{pano already CURRENT,<br/>a retry?}:::decision
    SAME -->|"no"| NEW{capture newer than the<br/>slot current, or slot empty?}:::decision
    NEW -->|"yes"| FLIP[set CURRENT, old one HISTORICAL,<br/>move slot pointer]:::service
    NEW -->|"no"| HIST[insert as HISTORICAL,<br/>slot untouched]:::service
    SAME -->|"yes, no-op"| MORE{more panos<br/>in chunk?}:::decision
    FLIP -->|"next pano"| MORE
    HIST -->|"next pano"| MORE
    MORE -->|"yes"| SAME
    MORE -->|"no"| COMMIT[commit one txn,<br/>go to next chunk]:::service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D8. Drive lifecycle

LANDED is the commit point: the cartridge may be wiped only from there on. Raw moves to Archive at day 30 and its per-drive key is destroyed at day 180.
```mermaid
%% D8: DRIVE.status in the registry. Statuses exactly as in solution.md.
stateDiagram-v2
    direction LR
    [*] --> CAPTURED: manifest registered
    CAPTURED --> UPLOADING: first segment sent
    UPLOADING --> UPLOADING: complete, missing list
    UPLOADING --> LANDED: all CRCs match
    LANDED --> PROCESSING: drive.landed
    PROCESSING --> PUBLISHED: last chunk flipped
    PROCESSING --> DEAD_LETTER: 3 failures on a shard
    PUBLISHED --> PROCESSING: reprocess request
    PUBLISHED --> RAW_ARCHIVED: day 30
    DEAD_LETTER --> RAW_ARCHIVED: day 30
    RAW_ARCHIVED --> RAW_SHREDDED: day 180, key destroyed
    RAW_SHREDDED --> [*]
```

## D8. Panorama lifecycle

Exactly one CURRENT per slot. A takedown re-versions tiles in place and keeps the status. Removing a CURRENT panorama promotes the newest HISTORICAL one in the same transaction, so the slot is never empty.
```mermaid
%% D8: PANORAMA.status in the index.
stateDiagram-v2
    direction LR
    [*] --> STAGED: tile stage writes row
    STAGED --> CURRENT: newest in slot
    STAGED --> HISTORICAL: older than slot current
    CURRENT --> HISTORICAL: newer capture published
    HISTORICAL --> CURRENT: promoted, current removed
    CURRENT --> CURRENT: takedown, tile v+1
    HISTORICAL --> HISTORICAL: takedown, tile v+1
    CURRENT --> REMOVED: QA removal
    HISTORICAL --> REMOVED: QA removal
    REMOVED --> [*]: tiles deleted
```

## D9. Deployment / topology

Depots upload into an ingest region pair. The pipeline runs in region A, so raw is read in-region. Three serving regions hold index replicas behind a global CDN.
```mermaid
%% D9: where each component runs, what crosses a region boundary, replication per store.
flowchart LR
    subgraph DEP[50 depots]
        ST[Ingest station per depot<br/>8 bays, pool of 80, 10 Gbps]:::critical
    end
    subgraph ING[Ingest region pair, A and B]
        REG[Drive registry, Paxos<br/>A and B + witness region]:::service
        LB[(Landing bucket, dual-region<br/>one copy in A, one in B)]:::store
    end
    subgraph PIPE[Pipeline region, A]
        WF[Workflow + publisher<br/>~1,300 cores]:::service -->|"blur batches"| GPU[GPU pools, 250 owned<br/>fresh 175, backfill 75 + preemptible]:::service
    end
    subgraph S1[Serving region 1]
        I1[(Index replica<br/>Paxos leader)]:::store -->|"local stale reads"| A1[Metadata API + cache]:::service
    end
    subgraph S2[Serving region 2]
        I2[(Index replica)]:::store -->|"local stale reads"| A2[Metadata API + cache]:::service
    end
    subgraph S3[Serving region 3]
        I3[(Index replica)]:::store -->|"local stale reads"| A3[Metadata API + cache]:::service
    end
    ST -->|"WAN, ciphertext segments,<br/>27 TB per depot a night"| LB
    ST -->|"WAN, register, complete"| REG
    LB -->|"raw reads, same region"| WF
    WF -->|"tiles, ~405 TB a day"| TB[(Tiles bucket<br/>multi-region)]:::store
    WF -->|"chunk txns, ~170 panos/s"| I1
    I1 -->|"Paxos log"| I2 & I3
    TB -->|"fill on miss, ~4 GB/s"| CDN[Global CDN<br/>~1 M tiles/s, ~320 Gbps]:::cache
    CDN -->|"tiles"| U[Maps clients]:::client
    A1 & A2 & A3 -->|"metadata, nearest region"| U
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Crosses a region boundary:** depots to the ingest pair (~125 Gbps fleet-wide, 50 x 2.5 Gbps averaged, ciphertext only). A to B landing replication (the same bytes). Pipeline to tiles bucket (405e12 B x 8 / 86,400 s = ~37.5 Gbps). Publisher to the index leader (~170 panos/s). Leader to followers (Paxos log). Tiles to CDN on a miss (~4 GB/s).
- **Never crosses:** unblurred raw stays in the ingest pair. Serving regions hold only blurred tiles and metadata.
- **Replication:** landing bucket 2 regions, erasure-coded inside each. Registry Paxos in A and B plus a witness in a third region, because two regions alone lose the majority when one dies. Index 3 regions, one replica each. Tiles multi-region. CDN global.

## D10. Scaling / partitioning

The index is range-split on a Hilbert-ordered key, the registry is keyed by drive, ingest scales by adding depots, and a hot cell is a read problem absorbed by caches.
```mermaid
%% D10: partition keys, the unit of ingest scale-out, and where a hot cell goes. Red: the depot station, the only fixed pipe.
flowchart LR
    ST[Depot station x 50<br/>20 cars each, unit of scale-out,<br/>10x cars = 500 stations]:::critical -->|"register + complete,<br/>~1,000 drives a day"| REG[(Registry<br/>key drive_id)]:::store
    PUB[Publisher<br/>~170 panos/s]:::service -->|"1 km chunk = ~7 L16 cells,<br/>Hilbert neighbours, often 1 split"| SB
    subgraph IDX[Panorama index, range splits on s2_cell_l16, capture_time DESC, pano_id]
        SA[(Split 1<br/>cells a to b)]:::store
        SB[(Split 2<br/>cells b to c)]:::store
        SC[(Split 3<br/>cells c to d)]:::store
    end
    U[Maps clients<br/>60k lookups/s peak]:::client -->|"lookups"| MC[Metadata cache<br/>key S2 L20 + date, 5 min]:::cache
    MC -->|"misses, ~6k reads/s,<br/>1 to 4 cells each"| SA
    HOT[Viral cell<br/>10,000x reads]:::client -->|"same L20 key,<br/>~1 miss per 5 min"| MC
    HOT -->|"arrow clicks,<br/>GET pano by id"| CDN[CDN<br/>1 min TTL]:::cache
    CDN -->|"~1 miss per pano a minute,<br/>via the API"| SC
    HOT -.->|"rejected"| RS[Split or salt the hot cell,<br/>writes are only ~170/s]:::decision
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Shard count:** splits are cut by size and load, not fixed. The index grows ~4 TB a year (3.75 B rows x ~1 KB). At an assumed ~10 GB per split, that is ~400 new splits a year.
- **Chunk locality:** 1 km / ~140 m per L16 cell = ~7 cells, adjacent on the Hilbert curve, so a chunk usually commits in one Paxos group, else two-phase commit over two.
- **Ingest:** stations share nothing but the registry. 10x cars is 10x stations, and the registry still sees only ~10k drives a day.

## D11. Failure mode map

Component on the first edge, what fails in the box, blast radius on the second edge, mitigation in the last box.
```mermaid
%% D11: one tree. Component, what fails, blast radius, mitigation. Red: the depot station.
flowchart TD
    ROOT[Street View imagery system]:::service
    ROOT -->|"depot station"| F1[Uplink down 3 days]:::critical -->|"blast: backlog grows,<br/>cars keep driving"| M1[Pool of 80 buffers 3 days,<br/>courier on day 3, no wipe before LANDED]:::service
    ROOT -->|"cartridge"| F2[Lost in transit]:::decision -->|"blast: one car-day,<br/>ciphertext only"| M2[Re-offload from the mirror,<br/>kept until LANDED,<br/>else re-drive, ~$1k]:::service
    ROOT -->|"drive registry"| F3[Region lost]:::decision -->|"blast: ingest pauses<br/>at 50 depots, seconds"| M3[Multi-region Paxos,<br/>stations retry, nothing wiped]:::service
    ROOT -->|"pipeline worker"| F4[Dies or stalls<br/>past its lease]:::decision -->|"blast: one shard,<br/>~100 panos late"| M4[Shard re-runs, epoch fences<br/>the zombie, DEAD_LETTER after 3]:::service
    ROOT -->|"blur model"| F5[Recall regression<br/>in a release]:::decision -->|"blast: every pano it published,<br/>privacy incident"| M5[Canary on 1% with human audit,<br/>roll back, re-blur backfill first]:::service
    ROOT -->|"serving"| F6[Region or metadata<br/>cache lost]:::decision -->|"blast: latency up,<br/>seconds of errors"| M6[Index in 3 regions,<br/>sized for 3x miss load, global CDN]:::service
    ROOT -->|"CDN invalidation"| F7[Rejected during<br/>a takedown]:::decision -->|"blast: one pano's old<br/>tiles stay at the edge"| M7[Retry with backoff, APPLIED<br/>only on 404, page near 24 h]:::service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

## D12. Rollout / migration

The four phases of `solution.md` §8 Migration. Durations are assumptions. Each phase closes with a rollback point, and slots make "publish from the old pipeline again" one chunk transaction per km.
```mermaid
%% D12: from the old rig and pipeline to this one. A rollback point closes each phase.
gantt
    title Migration to segments, shadow pipeline and slot publish
    dateFormat YYYY-MM-DD
    axisFormat %b %Y
    section 1 Segment format
    New rigs write segments, old drives converted        :p1, 2026-10-01, 60d
    Rollback = station keeps the old-format path         :milestone, r1, after p1, 0d
    section 2 Shadow pipeline
    New pipeline on 5 percent of drives, publish nothing :p2, after p1, 45d
    Compare pose error and blur recall on audit set      :p2b, after p2, 14d
    Rollback = shadow off, nothing was published         :milestone, r2, after p2b, 0d
    section 3 Publish switch
    Pilot country                                        :p3, after p2b, 30d
    Country by country                                   :p3b, after p3, 90d
    Rollback = old pipeline re-blurred, slots flip back  :milestone, r3, after p3b, 0d
    section 4 Optional re-tile
    Re-tile history in backfill lane if format changed   :p4, after p3b, 180d
    Rollback = pause lane, delete v n after v n+1 checks :milestone, r4, after p4, 0d
```
