# Diagrams: Warehouse management system (WMS) for a fulfillment network

> One-line answer: twelve views of one design. Each fulfillment center (FC) is a cell: one Postgres cluster that is the single writer for its bins (a movement ledger plus balances changed by guarded updates), cell services (scan API, per-SKU allocation lanes, a planner that releases work by deadline slack, task leases and timers), a CDC relay that ships versioned stock events to commerce, and an edge gateway in the building that journals every scan and keeps the floor picking through a network cut. The pick floor, ~375 pickers before the dawn cut-off, is the one red box in the final design. Every view here matches the corrected design in the deep dives: streams per install, progress-based leases, the balance hold on a short, counts judged by device time, and a reconciler at commerce's version.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: SKU (stock keeping unit), ASN (advance shipping notice), SSCC (Serial Shipping Container Code, a case, pallet or parcel id), GTIN (Global Trade Item Number, a product id), CDC (change data capture), WAL (write-ahead log), LSN (log sequence number), AZ (availability zone), DR (disaster recovery), WAN (wide area network, the building's link), AP (Wi-Fi access point), LTE (cellular data), mTLS (mutual TLS), UPH (units picked per hour per worker), FEFO (first expiry, first out), MDM (mobile device management), RF (replication factor). All times are Korea Standard Time.

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows) |
| D4 | Happy path per FR | FR1 pick confirmation: [solution §4.1](solution.md#41-track-inventory-per-bin-and-per-state-with-lots-expiry-cycle-counts-and-adjustments). FR1 cycle count: below. FR2 receive and put away: [solution §4.2](solution.md#42-receive-a-shipment-against-its-asn-inspect-it-and-put-each-unit-away-in-a-directed-bin). FR3 order to truck: [solution §4.3](solution.md#43-take-orders-from-commerce-allocate-stock-to-bins-release-picks-pack-label-and-hand-off). FR3 pack and ship: below. FR4 stock feed: [solution §4.4](solution.md#44-every-receipt-pick-short-pick-damage-and-shipment-reaches-commerce-within-seconds-and-dashboards-show-the-floor-live). FR4 capacity signal: below |
| D5 | Failure paths | Building WAN cut, over-pick after a lease expiry, duplicate order and a cancel during picking: below. 30 late scans: [solution §5.2](solution.md#52-a-handheld-loses-wi-fi-in-an-aisle-and-sends-30-scans-late-how-do-you-handle-duplicates-and-ordering-and-still-answer-in-300-ms). Cell primary failover: [solution §10.4](solution.md#104-failure-timeline). Lost stock event: [solution §5.6](solution.md#56-commerce-says-5-units-are-sellable-the-warehouse-says-3-who-is-right-how-fast-do-they-converge-and-how-do-you-prove-they-agree) |
| D6 | Decision flow | Scan apply, allocation bin choice: below. Short pick: [solution §5.4](solution.md#54-a-picker-reaches-a-bin-and-it-is-empty-what-happens-to-the-order-the-bin-record-and-availability-on-the-website). Handheld sequence gate: [solution §10.1](solution.md#101-internals-of-each-chosen-technology) |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Task: [solution §5.3](solution.md#53-a-picker-goes-on-break-mid-batch-a-tote-falls-off-a-conveyor-how-do-tasks-with-humans-in-the-loop-not-get-stuck-or-done-twice). Order line, bin status, balance hold, inbound container: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

The WMS network as one box: commerce sends orders and receives stock, vendors send ASNs and trucks, workers scan, parcels leave on trailers.

```mermaid
%% D1: the WMS network as one box with every external actor. The workers with handhelds are both an input (scans) and the capacity that runs out first.
flowchart LR
    CM[Commerce, 61<br/>orders, sellable stock] -->|"order_confirmed, cancels,<br/>capacity holds"| SYS[WMS network<br/>~100 FC cells + edges]
    SYS -->|"stock_changed, order_allocated,<br/>order_line_short, fc_capacity, status"| CM
    PR[Procurement and vendors] -->|"ASNs, inbound trucks"| SYS
    SYS -->|"over and short per ASN"| PR
    WK[Workers with handhelds<br/>~2,000 per large FC] -->|"scans"| SYS
    SYS -->|"tasks, next step"| WK
    SYS -->|"parcels, trailers,<br/>tracking ids"| CR[Line haul and<br/>delivery camps]
    SO[Site operations] -->|"labor plan, adjustments"| SYS
    SYS -->|"backlog, exceptions"| SO
    SYS -->|"fc_capacity, ledger exports"| NP[Network planning]
    SYS -->|"pages"| OC[On-call]

    class SYS service
    class WK,SO client
    class CM,PR,CR,NP,OC external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate. Network totals from solution §2 unless marked per FC; peak is ~10x average.

```mermaid
%% D2: data flow. Stores are cylinders, processes are rounded. Every number is an estimate from solution section 2.
flowchart LR
    CM[Commerce] -->|"order_confirmed JSON ~1 KB,<br/>~20/s avg, ~200/s peak"| IN(Intake and lanes)
    PR[Procurement] -->|"ASN ~50 KB,<br/>a few thousand a day"| IN
    HH[Handhelds] -->|"scan ~1 KB, 300/s avg,<br/>3k/s peak, at most 300/s per FC"| ED(Edge gateways)
    ED -->|"same events,<br/>journaled 24 h"| API(Scan API)
    IN -->|"one txn per SKU batch, ~10 ms"| DB[(Cell DBs<br/>ledger rows ~250 B,<br/>15M a day)]
    API -->|"4 to 6 rows per scan"| DB
    DB -->|"outbox via WAL, ~300 B,<br/>~115/s avg, ~1.2k/s peak"| RL(CDC relays)
    RL -->|"stock events, key sku_id,<br/>+ ~1.3k heartbeats/s, all partitions"| KF[[wms.stock-events<br/>64 partitions]]
    KF -->|"apply if newer"| CM
    DB -->|"daily partitions,<br/>~3.75 GB a day"| AR[(Ledger archive<br/>2 years, ~2.7 TB)]
    DB -->|"replica reads, ~5k SKUs<br/>per FC per 5 min"| RC(Reconciler)
    RC -->|"compare at version"| CM

    class IN,ED,API,RL,RC service
    class DB,AR store
    class KF queue
    class HH client
    class CM,PR external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design, 12 nodes, the pick floor in red: [solution §6](solution.md#6-final-design-and-the-six-core-flows).

## D4. Happy paths, one per FR

**FR1, pick confirmation in one transaction:** [solution §4.1](solution.md#41-track-inventory-per-bin-and-per-state-with-lots-expiry-cycle-counts-and-adjustments).

**FR1, a scheduled cycle count on a quiet bin.** No open tasks on the bin, so it goes straight to counting; the variance is one adjustment movement and one `stock_changed`.

```mermaid
%% D4 FR1 count: a blind count of a fast mover. The variance becomes a LOSS movement, available drops by one, and commerce hears within seconds.
sequenceDiagram
    autonumber
    participant S as Count scheduler
    participant D as Cell DB
    participant C as Counter handheld
    participant K as wms.stock-events
    S->>D: weekly count for fast movers, bin B-02-11
    D->>D: B-02-11 COUNT_PENDING, no open tasks, COUNTING, started_at noted
    D->>C: count task, blind, expected qty hidden
    C->>D: counted 23 of S-5520, system says 24, no movement stamped after the start
    D->>D: movement B-02-11 to LOSS, 1, reason COUNT
    D->>D: available 40 to 39, version 13, bin ACTIVE
    D->>K: outbox stock_changed S-5520 FC-07 39 v13
    Note over D,C: a variance over 5 units or about 200 dollars waits for a second approver
```

**FR2, receive a pallet and put a case away:** [solution §4.2](solution.md#42-receive-a-shipment-against-its-asn-inspect-it-and-put-each-unit-away-in-a-directed-bin).

**FR3, an order from confirmation to the truck:** [solution §4.3](solution.md#43-take-orders-from-commerce-allocate-stock-to-bins-release-picks-pack-label-and-hand-off).

**FR3, pack and ship in detail.** Packing and loading move units between containers; they never change available stock, only order status.

```mermaid
%% D4 FR3 pack and ship: a tote becomes a parcel, the parcel goes into a trailer, the trailer leaves. Status events go to commerce, stock events do not.
sequenceDiagram
    autonumber
    participant T as Tote T-881
    participant P as Pack station 12
    participant D as Cell DB
    participant L as Loader handheld
    participant C as Commerce
    T->>P: 00:41 off the conveyor, routed by truck
    P->>D: scan tote, lines for ord_5512
    P->>D: scan each item, tote to parcel p_77
    D-->>P: box size M, label with SSCC and tracking id
    D-->>C: order_packed ord_5512, ord_5512-1, tracking id
    L->>D: 01:20 scan p_77 into trailer TR-12, camp lane 4
    L->>D: 02:00 close TR-12, seal number
    D->>D: every unit in TR-12 to CARRIER, one transaction
    D-->>C: order_shipped ord_5512, ord_5512-1
```

**FR4, the stock feed to commerce:** [solution §4.4](solution.md#44-every-receipt-pick-short-pick-damage-and-shipment-reaches-commerce-within-seconds-and-dashboards-show-the-floor-live).

**FR4, the capacity signal and a flash-deal hold.** The capacity model recomputes remaining dawn capacity every 60 s as the smaller of pick and pack remaining, counting only fulfillments the WMS has acknowledged and booking each open deal as `max(granted, drawn) − picked` (or `− packed`) deal units. Deal orders carry `deal_id` and draw on their hold instead of being counted twice. Commerce subtracts its own open non-deal holds **and its live reservations** at the FC and cut-off, keeps counting acknowledged units until it has applied the matching `capacity_version`, treats a signal silent for 2 minutes in the last hour as 0, and skips an FC at zero when it chooses a pool.

```mermaid
%% D4 FR4 capacity: pickers times measured UPH times hours to the 00:40 last pick, minus acknowledged backlog, each deal's future work and a 2 percent reserve. Commerce also subtracts holds and live reservations.
sequenceDiagram
    autonumber
    participant F as Floor handhelds
    participant P as Capacity model
    participant K as wms.fc-capacity
    participant C as Commerce
    C->>P: 18:00 capacity_hold deal_d77, FC-07, dawn, 4,000, via orders.fc-07
    P->>K: capacity_hold_result deal_d77 granted 4,000
    C->>P: 22:05 deal sold out, every order_confirmed carries deal_id d77, drawn 4,000
    F->>P: 23:20, last 30 min of picks, 118 UPH measured
    P->>P: 372 pickers x 118 x 1.33 h to 00:40 is 58.5k units
    P->>P: minus 15k acknowledged non-deal, deal 4,000 minus 1,950 picked, 41.5k pick side
    P->>P: pack side 200 x 225 x 1.67 h minus backlog is about 55k, so pick binds, minus 1.2k reserve, 40.3k
    P->>K: fc_capacity FC-07 dawn 40,300, version 311
    K->>C: apply if newer
    C->>C: minus open non-deal holds and live reservations, about 1,800, then choose FC
    Note over P,C: promo night, 23:51, the surge has used it all
    P->>K: fc_capacity FC-07 dawn 0, version 342
    C->>P: 23:59 deal ends, capacity_release returns granted minus drawn minus open claims
    C->>P: by 00:29 last claim resolved, final capacity_release, grant 0
    C->>C: next dawn checkout routes to FC-03 or offers next day
```

## D5. Failure paths

**The building's WAN is cut at 23:30 for 25 minutes (solution Flow 5).** The edge keeps the floor picking from leased batches and applies the lease rules locally; the cloud cell stops the building's lease clocks, reports `floor_contact_age` on its heartbeats and stops new dawn orders after 5 minutes; the journal replays on reconnect before any clock restarts.

```mermaid
%% D5 WAN cut: survival mode in the building, lease clocks frozen and capacity 0 in the cloud, ordered replay with dedup when the link returns, then clocks restart.
sequenceDiagram
    autonumber
    participant H as Handhelds
    participant E as Edge gateway
    participant W as WAN, 2 carriers + LTE
    participant A as Cell services
    participant C as Commerce
    Note over W: 23:30:00 both carriers down, LTE down too
    E->>W: forward fails 3 times in 5 s
    E->>E: SURVIVAL mode, confirm planned steps, journal, local leases
    H->>E: picks and packs continue, labels from the leased id block
    A->>A: stop lease clocks for FC-07, heartbeats carry floor_contact_age
    A->>A: 23:35, no traffic from FC-07 for 5 min
    A->>C: fc_capacity FC-07 dawn 0
    A->>A: keeps allocating orders already received
    Note over W: 23:55:00 link back
    E->>A: replay journal in device order, about 65k scans
    A->>A: dedup by device, stream and seq, about 2 min, then restart clocks
    A->>C: stock events resume, capacity recomputed
    E->>E: ONLINE, next batches leased again
```

Detection ~5 s at the edge; commerce sees `floor_contact_age` grow within seconds; ~5 minutes for the capacity signal (so a 30-second blip does not reroute orders). With the cloud's clocks running instead, a simulated 25-minute cut re-releases 11,306 steps and sends 728 totes to problem solving at ~23:57. Data at risk: none, the journal is on two machines. Workers see nothing for planned steps; put-away decisions and re-allocation after a short wait for the link.

**A silent handheld returns after its step was re-issued and picked by someone else (an over-pick).** Both picks are physical facts. Because the new holder had already scanned that step, the late scan is an over-pick: its units go to a `PROBLEM` tote instead of being "deduplicated" away. Had the new holder not scanned yet, the step would go back to the original device and the re-released copy would be withdrawn.

```mermaid
%% D5 over-pick: the late scan carries an old epoch and the new holder already scanned the step. It is applied as a movement into a PROBLEM tote, never rejected, because the carton really left the bin.
sequenceDiagram
    autonumber
    participant H1 as Handheld hh-0342
    participant A as Scan API
    participant D as Cell DB
    participant H2 as Handheld hh-0519
    H1->>H1: picks 1 of S-7710 for t_93 epoch 1, then battery dies, scan queued
    D->>D: device silent, t_93 UNCONFIRMED, 20 min later RELEASED, epoch 2, possible over-pick
    A->>H2: t_93 leased, epoch 2
    H2->>A: pick 1 of S-7710 from C-04-02
    A->>D: applied, task DONE, line PICKED
    H1->>A: battery swapped after 25 min, stream s4 seq 520, t_93 epoch 1, pick 1
    A->>D: old epoch and the new holder scanned, movement C-04-02 to PROBLEM tote
    A->>D: release newest allocation if on_hand falls below allocated
    A-->>H1: accepted, take the PROBLEM tote to problem solve
```

**A duplicate `order_confirmed`, then a cancel while the order is half picked.** Intake deduplicates on `fulfillment_id` (`<order_id>-<n>`), so a re-sent message is a no-op while a re-source would arrive as a new fulfillment. Cancels name a fulfillment and optionally its lines. The answer depends on how far each line's units got, and comes back per line as `order_cancel_result` on `wms.order-status` (solution §3.2). A cancel for a fulfillment the cell has not seen leaves a 7-day tombstone, so the fulfillment is refused if it arrives later.

```mermaid
%% D5 duplicate and cancel: the relay re-publishes a fulfillment, then the buyer cancels. Allocated units are released, picked units go back to stock, loaded units are too late.
sequenceDiagram
    autonumber
    participant C as Commerce
    participant I as Intake
    participant D as Cell DB
    participant H as Picker handheld
    C->>I: order_confirmed ord_7001, fulfillment ord_7001-1
    I->>D: insert, allocate, order_allocated ord_7001-1
    C->>I: order_confirmed ord_7001-1 again, relay restart
    I->>D: same fulfillment_id, on conflict do nothing
    C->>I: order_cancel_requested ord_7001, ord_7001-1, all lines
    D->>D: line 1 allocated only, release it, available up
    D->>D: line 2 already in tote T-90, return-to-stock task
    D-->>C: order_cancel_result ord_7001-1, lines 1 and 2, cancelled, on wms.order-status
    D-->>C: stock_changed for line 1 on wms.stock-events
    H->>D: return-to-stock scan, T-90 to bin, available up
    Note over C,D: once a line is packed the answer for it is too_late
```

**Also in solution.md:** 30 late scans after a Wi-Fi gap ([§5.2](solution.md#52-a-handheld-loses-wi-fi-in-an-aisle-and-sends-30-scans-late-how-do-you-handle-duplicates-and-ordering-and-still-answer-in-300-ms)), the cell primary dying at 23:40 ([§10.4](solution.md#104-failure-timeline)), a lost stock event caught by the reconciler ([§5.6](solution.md#56-commerce-says-5-units-are-sellable-the-warehouse-says-3-who-is-right-how-fast-do-they-converge-and-how-do-you-prove-they-agree)).

## D6. Activity / decision flow

**Scan apply inside the cell.** Stream and sequence first, then whether the cell can apply it at all, then the task's epoch, then the physical guard. Nothing physical is ever rejected, and every path except a protocol reply ends in the same transaction that advances the stream and stores the reply, so the stream always advances.

```mermaid
%% D6 scan apply: protocol problems get a reply with no side effect. Unknown tasks, bins or barcodes become PROBLEM movements so the stream never blocks. Old epochs are over-picks only if the new holder already scanned.
flowchart TD
    IN[Scan: device, stream, seq,<br/>task, epoch, qty] -->|"open one transaction"| SQ{Stream known and<br/>seq equals last + 1?}
    SQ -->|"unknown stream, at or below last,<br/>or a gap"| PR[Reply only: register,<br/>stored result, or resend]
    SQ -->|"yes"| OK{Task, bin and<br/>GTIN known?}
    OK -->|"no"| EX[Movement to PROBLEM,<br/>exception task]
    OK -->|"yes"| EP{Epoch current?}
    EP -->|"old, new holder scanned"| OP[Movement to PROBLEM tote,<br/>over-pick]
    EP -->|"old, not yet scanned"| BK[Step back to this device,<br/>withdraw the copy]
    EP -->|"current"| GD{Guard holds?<br/>on_hand at least qty}
    BK -->|"then"| GD
    GD -->|"yes"| AP[Apply movement,<br/>task and line state]
    GD -->|"no"| GN[GAIN for the gap,<br/>then apply, count task]
    AP -->|"same transaction"| DD[Stream advanced, reply stored,<br/>release rule, commit]
    OP -->|"same transaction"| DD
    GN -->|"same transaction"| DD
    EX -->|"same transaction"| DD

    class IN client
    class SQ,OK,EP,GD decision
    class PR,EX,OP,BK,AP,GN service
    class DD store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

Only a transient error (lock timeout, failover) leaves the sequence where it is; the device retries the same `seq`. The release rule in the last box: if the movement drops `on_hand` below `allocated`, the newest allocations go back to the lane in the same transaction.

**Allocation bin choice inside a lane.** One SKU, all its waiting lines sorted by truck departure, one transaction that locks the SKU's availability row first and then bins in `location_id` order, after a fence check on the lane's epoch. The orderings are the ones Oracle WMS Cloud lists for allocation (FEFO, quantity ascending, location sequence; survey row 6a, verified). Minimum remaining life is checked at the line's **promise time**, not at allocation time.

```mermaid
%% D6 bin choice: FEFO for expiry-controlled SKUs, otherwise smallest quantity first to free bins, then walk order. The guard catches a pick or count that raced the lane.
flowchart TD
    L[Lane batch for one SKU<br/>lines sorted by truck] -->|"read candidates"| C[ACTIVE bins, not held,<br/>on_hand minus allocated above 0]
    C -->|"SKU flag"| E{Expiry-controlled?}
    E -->|"yes"| F[Earliest expiry first, skip lots<br/>short of minimum life at promise time]
    E -->|"no"| Q[Smallest quantity first,<br/>frees bins]
    F -->|"ties"| W[Then walk order<br/>near the line's zone]
    Q -->|"ties"| W
    W -->|"take units"| G{Guarded update<br/>changed 1 row?}
    G -->|"yes"| N[Next line]
    G -->|"no, raced by a pick or count"| C
    N -->|"no bins left for a line"| S[order_line_short<br/>no_stock, for the rest]
    N -->|"all lines done"| OB[Commit with outbox: stock_changed,<br/>order_allocated, then shorts]

    class L,C,F,Q,W,N service
    class E,G decision
    class S external
    class OB store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

**Also in solution.md:** short-pick handling ([§5.4](solution.md#54-a-picker-reaches-a-bin-and-it-is-empty-what-happens-to-the-order-the-bin-record-and-availability-on-the-website)), the handheld sequence gate ([§10.1](solution.md#101-internals-of-each-chosen-technology)).

## D7. Entity relationship

Locations, balances, the movement ledger, availability, orders, allocations, tasks, devices and the outbox, with keys and retention: [solution §3.3](solution.md#33-data-model).

## D8. State machines

**Task:** [solution §5.3](solution.md#53-a-picker-goes-on-break-mid-batch-a-tote-falls-off-a-conveyor-how-do-tasks-with-humans-in-the-loop-not-get-stuck-or-done-twice).

**Order line, inside the WMS.** Lines belong to one fulfillment (`<order_id>-<n>`). `SHORT` (`no_stock`) is reported to commerce, which decides re-source or refund. `NEXT_CUTOFF` (`missed_cutoff`) keeps the allocation and waits for the next cut-off's work unless commerce cancels that line. Cancels are per line, so declining one line leaves the rest of the fulfillment on tonight's truck. A partial short splits the line.

```mermaid
%% D8 order line: from order_confirmed to the trailer. REALLOCATING is the short-pick detour, NEXT_CUTOFF keeps the allocation for the next truck, CANCELLED depends on how far the units got.
stateDiagram-v2
    direction LR
    [*] --> RECEIVED : order_confirmed
    RECEIVED --> ALLOCATED : lane batch
    RECEIVED --> SHORT : no stock in FC
    ALLOCATED --> RELEASED : in a pick batch
    RELEASED --> PICKED : pick scans
    RELEASED --> REALLOCATING : short at the bin
    REALLOCATING --> RELEASED : cleanup pick
    REALLOCATING --> SHORT : no_stock
    REALLOCATING --> NEXT_CUTOFF : missed_cutoff
    ALLOCATED --> NEXT_CUTOFF : unreleased at 00:15
    NEXT_CUTOFF --> RELEASED : next cut-off work
    NEXT_CUTOFF --> CANCELLED : buyer declines
    PICKED --> PACKED : pack scan
    PACKED --> LOADED : trailer scan
    LOADED --> SHIPPED : trailer dispatched
    ALLOCATED --> CANCELLED : cancel request
    RELEASED --> CANCELLED : cancel request
    PICKED --> CANCELLED : return to stock
    SHIPPED --> [*]
    SHORT --> [*]
    CANCELLED --> [*]

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    class RECEIVED,ALLOCATED,RELEASED,PICKED,PACKED,LOADED service
    class SHIPPED,CANCELLED store
    class SHORT,REALLOCATING,NEXT_CUTOFF decision
```

**Bin status.** The count protocol lives on the bin. Only `ACTIVE` bins receive new pick and put-away tasks. A bin in `COUNT_PENDING` or `COUNTING` keeps its units in available (they are still there) and may still be allocated, because allocation changes `allocated`, not `on_hand`. A movement stamped at or after the count's start voids the count.

```mermaid
%% D8 bin status: a count waits for open tasks, is voided by any movement stamped after its start, and commits an adjustment against on_hand at commit time.
stateDiagram-v2
    direction LR
    [*] --> ACTIVE
    ACTIVE --> COUNT_PENDING : count requested
    COUNT_PENDING --> COUNTING : no open task
    COUNTING --> COUNT_PENDING : movement after start
    COUNTING --> ACTIVE : adjustment committed
    ACTIVE --> BLOCKED : damage, repair
    BLOCKED --> ACTIVE : cleared

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    class ACTIVE service
    class COUNT_PENDING,COUNTING decision
    class BLOCKED store
```

**Balance hold (one bin and SKU).** The short-pick hold lives on the `BALANCE` row (`held`), not on the bin: other SKUs in the same bin are untouched. While held, the balance's unallocated units are out of `available_qty`, its existing allocations stay, and only a count ends the hold.

```mermaid
%% D8 balance hold: a short holds one bin and SKU balance. The priority count keeps allocations up to what it finds, releases the rest, and ends the hold with either a release or a LOSS.
stateDiagram-v2
    direction LR
    [*] --> OPEN
    OPEN --> HELD : short pick here
    HELD --> OPEN : count finds units
    HELD --> EMPTY : count finds none
    EMPTY --> OPEN : put-away
    note right of HELD
        unallocated units out of available
        existing allocations kept until the count
    end note

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    class OPEN service
    class HELD decision
    class EMPTY store
```

**Inbound container (a pallet or case on an ASN).** Units become available only at `PUT_AWAY`.

```mermaid
%% D8 inbound container: expected on an ASN, received by SSCC scan, sampled, carted, put away. Missing and quarantined containers go back to procurement as variances.
stateDiagram-v2
    direction LR
    [*] --> EXPECTED : ASN received
    EXPECTED --> RECEIVED : SSCC scanned
    EXPECTED --> MISSING : truck closed
    RECEIVED --> QC_HOLD : sampled
    QC_HOLD --> RECEIVED : passed
    QC_HOLD --> QUARANTINED : failed
    RECEIVED --> ON_CART : cases on a cart
    ON_CART --> PUT_AWAY : bin and case scanned
    PUT_AWAY --> [*]
    QUARANTINED --> [*]
    MISSING --> [*]

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    class EXPECTED,RECEIVED,ON_CART service
    class PUT_AWAY store
    class QC_HOLD,QUARANTINED,MISSING decision
```

## D9. Deployment / topology

One building and its cell. The cell's database spans three AZs: a primary and two standbys, committing with `ANY 1 (az_b, az_c)`; the AZ c standby also serves reads, and failover promotes the more advanced standby. An async DR replica sits in a second region. Cell services run in two AZs; regional Kafka is shared by all cells.

```mermaid
%% D9: one building and its cell. Primary plus two quorum standbys, ANY 1. The WAN link is red: it is the one thing whose loss stops a building, so it has two carriers, a cellular backup, and survival mode behind it.
flowchart LR
    subgraph BLD[Building FC-07]
        HH[~2,000 handhelds] -->|"Wi-Fi, 802.11r roam"| APS[Wi-Fi APs]
        APS -->|"scans"| EG[Edge pair<br/>active, standby]
    end
    EG -->|"mTLS"| WAN[WAN<br/>2 carriers + LTE]
    subgraph REG[Primary region]
        subgraph AZA[AZ a]
            SVA[Cell services]
            PRI[(Primary)]
        end
        subgraph AZB[AZ b]
            SVB[Cell services]
            STB[(Standby, quorum)]
        end
        subgraph AZC[AZ c]
            RRC[(Standby, quorum,<br/>serves reads)]
            KFC[[Kafka, RF 3<br/>across AZs]]
        end
    end
    WAN -->|"scans"| SVA
    WAN -->|"scans, AZ failover"| SVB
    SVA -->|"transactions"| PRI
    SVB -->|"transactions"| PRI
    PRI -->|"WAL, ANY 1"| STB
    PRI -->|"WAL, ANY 1"| RRC
    PRI -->|"async WAL"| DRR[(DR replica<br/>second region)]
    SVA -->|"outbox via CDC"| KFC

    class HH,APS client
    class EG,SVA,SVB service
    class PRI,STB,RRC,DRR store
    class KFC queue
    class WAN critical

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

What crosses a boundary: scans over the WAN (~300 KB/s at most per building), WAL to the standbys in AZ b and AZ c (a commit waits for either, ~1 to 2 ms), async WAL to the DR region, outbox events to the shared Kafka. Nothing crosses from one cell to another: two buildings share only Kafka, device identity and the region. Losing AZ a promotes the more advanced of the two standbys (~30 s, solution §10.4); losing the region promotes the DR replica with a clock-based epoch, holds a recovery barrier until intake and the edge journals have replayed, and takes ~30 minutes in all (solution §5.7).

## D10. Scaling / partitioning

The network is partitioned by FC into cells. Inside a cell, allocation is partitioned by SKU hash into 16 lanes, one writer per SKU. The stock topic is keyed by `sku_id` across all FCs.

```mermaid
%% D10: cells by FC, lanes by SKU hash inside a cell. The hot promo SKU's availability row is red: in a burst of per-line transactions every allocation serializes on it and every other SKU queues behind. The fix is one batch per SKU per second.
flowchart LR
    ORD[Orders from commerce] -->|"topic per FC"| C07[Cell FC-07]
    ORD -->|"topic per FC"| C03[Cell FC-03]
    ORD -->|"topic per FC, ~100 cells"| CX[Other cells]
    C07 -->|"hash of sku_id mod 16"| L0[Lane 0<br/>~31k SKUs]
    C07 -->|"hash"| L9[Lane 9<br/>promo SKU S-9000,<br/>2,000 lines at 00:00]
    C07 -->|"hash"| L15[Lane 15]
    L9 -->|"before: one txn per line in a burst,<br/>6 s serialized, others 5.5 s p99"| HOT[S-9000 availability row]
    L9 -->|"after: one txn per SKU per s,<br/>~20 ms, others ~3 ms"| FIX[One batch per second]
    C07 -->|"outbox, key sku_id"| KS[[wms.stock-events<br/>64 partitions, all FCs]]
    C03 -->|"outbox, key sku_id"| KS

    class ORD external
    class C07,C03,CX,L0,L9,L15,FIX service
    class HOT critical
    class KS queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- At ~100 lines a second, one transaction per line is fine (~3 ms p50, ~8 ms p99); lanes are insurance against bursts, not a steady-state speed-up. In a burst (2,000 lines in 2 s, or at once), per-line transactions serialize on the SKU's availability row: `2,000 × ~3 ms` = ~6 s, and the allocation service's ~20 connections all wait on it, so **every other SKU's** allocations reach ~5.5 s p99. A pick on the hot bins waits behind at most ~20 holders, ~62 ms p99. One lock order (availability row first, then bins by `location_id`) prevents deadlocks. With the lane: one ~20 ms transaction per second, ~3 ms for everyone else. Solution §5.1.
- A lane holds ~500k ÷ 16 ≈ 31k SKUs. Lanes are threads in the cell's allocation service; a lane's SKUs move to another instance on failover, and because each batch is one transaction, a crash mid-batch leaves nothing half done.
- Heartbeats: because the topic is keyed by `sku_id`, each FC writes its 5 s heartbeat to all 64 partitions (`64 × 100 FCs ÷ 5 s ≈ 1.3k` tiny records a second network-wide), and a consumer judges staleness per (partition, FC).
- Kafka: a flash-sale SKU stocked in 10 FCs puts all 10 FCs' events on one partition of `wms.stock-events`. At ~1k events/s × 300 B = 300 KB/s, that partition is far under its limit, so keying by `sku_id` (which gives commerce all pools of a SKU in order on one consumer) costs nothing.
- The cell itself is the shard. The busiest cell is ~7% of one primary at its 300 scans/s design load (solution §10.3); a 10x FC would split into two cells by floor (solution §10.11).

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Two trees to stay under 15 nodes. Matches solution §8.

```mermaid
%% D11 tree 1: the floor and the cell. The WAN link is red: it is the likeliest of these to fail on a given night, and its loss cuts a whole building off from its cell.
flowchart TD
    ROOT[Floor and cell] --> HHW[Handheld or Wi-Fi AP]
    ROOT --> WAN[Building WAN link]
    ROOT --> PRI[Cell DB primary or AZ]
    ROOT --> REG[Region]
    HHW -->|"dead zone, flat battery"| HHWB[One worker, minutes]
    HHWB -->|"mitigate"| HHWM[Local steps, stream seq queue,<br/>silent steps held 20 min]
    WAN -->|"both carriers and LTE down"| WANB[One building cut off<br/>from its cell]
    WANB -->|"mitigate"| WANM[Edge survival mode ~40 min,<br/>lease clocks stopped,<br/>floor_contact_age, capacity 0]
    PRI -->|"host or AZ lost"| PRIB[One FC, ~30 s of<br/>slow decision scans]
    PRIB -->|"mitigate"| PRIM[More advanced standby promoted,<br/>new epoch, resend by seq]
    REG -->|"region lost"| REGB[Every cell, ~30 min]
    REGB -->|"mitigate"| REGM[DR replicas, clock epoch,<br/>barrier until journals replay]

    class ROOT,HHW,PRI,REG service
    class WAN critical
    class HHWB,WANB,PRIB,REGB decision
    class HHWM,WANM,PRIM,REGM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

```mermaid
%% D11 tree 2: the stock feed and our own releases. A bad allocation release has the biggest blast radius: guards stop negative stock, but a night's orders can be stranded.
flowchart TD
    ROOT[Feed and releases] --> RL[CDC relay of one cell]
    ROOT --> KF[Regional Kafka]
    ROOT --> CC[Commerce consumer bug]
    ROOT --> REL[Bad allocation release]
    RL -->|"stalls"| RLB[One FC's feed stops,<br/>WAL grows ~0.4 GB an hour]
    RLB -->|"mitigate"| RLM[Page at 30 s lag,<br/>restart from the slot,<br/>versions absorb replays]
    KF -->|"down"| KFB[Every FC's feed stops,<br/>floors keep working]
    KFB -->|"mitigate"| KFM[Outboxes hold ~1M rows an hour,<br/>holds keep commerce safe]
    CC -->|"skips or misapplies"| CCB[Drift on some SKUs]
    CCB -->|"mitigate"| CCM[Reconciler at commerce version,<br/>RESYNC at a new version]
    REL -->|"wrong bin choice"| RELB[A night's orders stranded<br/>in one cell]
    RELB -->|"mitigate"| RELM[Cell by cell, smallest first,<br/>no deploys 20:00 to 03:00,<br/>dawn on-truck rate gate]

    class ROOT,RL,KF,CC,REL service
    class RLB,KFB,CCB,RELB decision
    class RLM,KFM,CCM,RELM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a vendor WMS to cells, one FC at a time. The vendor emits movement events first, so the new ledger is proven in shadow before any building moves (the path Picnic describes, survey row 4a, secondary). Rollback for a cut-over FC is an export of the cell's balances back into the vendor WMS, made auditable by the `MIGRATION` movements, plus pointing the order topic back.

```mermaid
%% D12: vendor WMS to FC cells. Shadow ledger first, shadow feed second, one pilot FC, then waves, never in the weeks before a big sale.
gantt
    title Vendor WMS to FC cells
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Shadow
    Vendor emits movements, shadow ledger          :a1, 2027-01-04, 21d
    Balances match per bin for 14 days             :a2, after a1, 14d
    Rollback point, drop the shadow cell           :milestone, m1, after a2, 0d
    section Shadow feed
    Shadow stock events compared by commerce       :b1, after a2, 14d
    section Pilot
    Cut over the smallest FC on a quiet afternoon  :c1, after b1, 1d
    Watch for 7 days, balance export ready         :c2, after c1, 7d
    Rollback point, export balances to vendor      :milestone, m2, after c2, 0d
    section Waves
    5 FCs                                          :d1, after c2, 14d
    About 20 FCs a month                           :d2, after d1, 120d
    Freeze before the big sale                     :d3, after d2, 28d
    Remaining FCs                                  :d4, after d3, 21d
    section Retire
    Vendor WMS read-only for audit                 :e1, after d4, 60d
```

Gates between waves: zero reconciler drift at version for the moved FCs, the dawn on-truck rate within 0.2 points of the same FC's last month on the vendor WMS, decision-scan p99 under 300 ms, and exception rates (shorts, over-picks, count variances) within 10% of baseline.
