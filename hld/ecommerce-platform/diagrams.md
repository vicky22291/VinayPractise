# Diagrams: E-commerce marketplace (catalog, cart, checkout, no overselling)

> One-line answer: twelve views of one design. A read side (CDN and gateway, browse fleet, a read model and search index fed by CDC and stock transition events) serves ~60k requests a second and may be 1 to 3 s stale. A money side (order saga, inventory service on 16 shards keyed by `sku_id`, payment service with attempt rows and a resolver) changes stock only by conditional updates in one local transaction with the reservation row. A deal gate carves a flash sale into 40 single-owner buckets so the hot SKU's stock row sees ~55 writes a second instead of 100k. The WMS (problem 62) is the truth for physical stock and talks to us through versioned events. The flash-sale SKU's stock row is the one red box.

The D1 to D12 set from `hld/CLAUDE.md` §4, each with a one-line caption. A diagram already in [`solution.md`](solution.md) gets a heading, a caption and a link, never a second copy. Acronyms: SKU (stock keeping unit), FC (fulfillment center), WMS (warehouse management system), PSP (payment service provider), CDC (change data capture), CDN (content delivery network), TTL (time to live), KV (key-value store), AZ (availability zone), RF (replication factor), 3DS (3-D Secure).

| # | Diagram | Where it lives |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow | below |
| D3 | Component architecture (final design) | [solution §6](solution.md#6-final-design-and-the-six-core-flows). Zoom-in for order status and cancel: below |
| D4 | Happy path per FR | FR1 product page: [solution §4.1](solution.md#41-buyers-search-and-open-a-product-page-with-offers-price-and-availability). FR2 seller count and WMS snapshot: [solution §4.2](solution.md#42-sellers-register-listings-and-stock-and-warehouse-events-adjust-platform-held-stock). FR3 cart on two devices: [solution §4.3](solution.md#43-buyers-add-update-and-remove-cart-items-and-see-current-price-and-availability). FR4 normal order: [solution §4.4](solution.md#44-placing-an-order-reserves-stock-prices-it-authorizes-payment-and-confirms-it-safe-to-retry). FR4 flash deal setup with capacity holds, and a flash claim to a confirmed order: below. FR5 cancel: [solution §4.5](solution.md#45-buyers-see-order-status-and-history-and-cancel-before-shipment). FR5 short pick and re-source: below |
| D5 | Failure paths | PSP timeout and a second tap: [solution §5.2](solution.md#52-the-payment-call-times-out-and-the-buyer-taps-again-how-do-you-avoid-a-double-charge-a-double-order-or-stock-stuck-in-a-reservation). Inventory shard failover: [solution §10.4](solution.md#104-failure-timeline). Out-of-order WMS events, gate node crash, late authorization, PSP brownout: below |
| D6 | Decision flows | Truth at reserve: [solution §5.4](solution.md#54-search-shows-in-stock-but-checkout-says-sold-out-how-fresh-is-availability-and-where-is-the-truth-checked). What the buyer pays: [solution §5.5](solution.md#55-the-price-or-a-coupon-changes-between-the-cart-and-checkout-what-does-the-buyer-see-and-pay). Pool pick, gate claim, sweeper, PSP call path: below |
| D7 | Entity relationship | [solution §3.3](solution.md#33-data-model) |
| D8 | State machines | Order, reservation then WMS hold, payment attempt: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below. The flash-sale path: [solution §5.1](solution.md#51-flash-sale-10k-units-1m-buyers-at-100000-how-do-you-avoid-both-overselling-and-melting-the-database-on-one-hot-row) |
| D11 | Failure mode map | below, two trees |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

The marketplace as one box: buyers and sellers in, the warehouse and the payment providers out. The WMS and the PSPs are outside our trust boundary.

```mermaid
%% D1: the system as one box with every external actor. PSPs and WMS cells are outside our trust boundary and answer on their own schedule.
flowchart LR
    BU[Buyers<br/>~10M a day, app and web] -->|"search, pages, cart, orders,<br/>deal claims, ~60k req per s"| SYS[Marketplace platform<br/>catalog, cart, checkout,<br/>inventory, orders]
    SYS -->|"pages, order status, push"| BU
    SE[Sellers<br/>portal, API, ERP feeds] -->|"listings, prices, stock counts,<br/>ship and cancel"| SYS
    SYS -->|"new orders, deficit tasks"| SE
    SYS -->|"order_confirmed per fulfillment,<br/>cancel requests, capacity holds"| WMS[WMS<br/>one cell per FC]
    WMS -->|"stock, allocations, shorts, packed,<br/>shipped, capacity and hold results,<br/>heartbeats"| SYS
    SYS -->|"authorize, capture, void,<br/>status queries"| PSP[PSPs and Korean PGs]
    PSP -->|"results, settlement reports"| SYS
    SYS -->|"risk check at authorize"| RISK[Risk decisioning<br/>problem 52]
    CDN[CDN] -->|"images, static assets"| BU

    class BU,SE,CDN client
    class SYS,RISK service
    class WMS,PSP external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D2. Data flow (DFD)

Inputs to outputs with format, size and rate at peak, from solution §2. Stores are cylinders, processes are rounded.

```mermaid
%% D2: data flow. Rates are peak unless marked avg. The read side and the money side share only Kafka.
flowchart LR
    BU[Buyers] -->|"page and search requests,<br/>JSON 20 to 30 KB, 60k per s"| BR(Browse and cart fleet)
    BR -->|"doc reads ~5 KB,<br/>~18k per s past local cache"| RM[(Read model, Redis,<br/>search index)]
    SE[Sellers] -->|"listing and price changes,<br/>~2 KB, 580 per s avg, 10k bursts"| LDB[(Listing DB)]
    SE -->|"stock ops ~200 B,<br/>290 per s avg, 5k bursts"| INV(Inventory service)
    BU -->|"orders ~1 KB, 350 per s;<br/>claims 100k per s for 0.5 s"| CK(Checkout and deal gate)
    CK -->|"reserves ~200 B, 1.24k per s;<br/>deal batches for 0.12 s"| IDB[(Inventory DB)]
    INV -->|"movements and rows,<br/>~9k writes per s in all"| IDB
    CK -->|"orders ~3 KB, 9 GB a day"| ODB[(Order DB)]
    CK -->|"authorize ~1 KB, 350 per s"| PSP[PSPs]
    LDB -->|"CDC rows ~2 KB"| KQ[[Kafka topics]]
    IDB -->|"availability transitions ~200 B"| KQ
    ODB -->|"order_confirmed ~1 KB, 35 per s avg"| KQ
    WMS[WMS cells] -->|"stock events ~300 B, 1k per s"| KQ
    KQ -->|"order_confirmed, cancels,<br/>capacity holds"| WMS
    KQ -->|"versioned stock events"| INV
    KQ -->|"changes"| BLD(Builder and indexer)
    BLD -->|"upserts, bulk index every 100 ms"| RM

    class BU,SE client
    class BR,INV,CK,BLD service
    class RM,LDB,IDB,ODB store
    class KQ queue
    class PSP,WMS external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

## D3. Component architecture

The final design, 15 nodes, the inventory DB in red for its hot SKU row: [solution §6](solution.md#6-final-design-and-the-six-core-flows). The cart is two boxes (a service and a KV store) and is drawn in [solution §4.3](solution.md#43-buyers-add-update-and-remove-cart-items-and-see-current-price-and-availability). Below, the order status and cancel path (FR5) that the final design folds into single boxes: status comes from the owners of the physical units, and so does released stock.

```mermaid
%% D3 zoom-in, orders: status and cancel. Status comes from the owners of the physical units, and so does released stock.
flowchart LR
    B[Buyers] -->|"history, cancel"| ORD[Order service]
    ORD -->|"own orders, state"| ODB[(Order DB<br/>by buyer_id)]
    ODB -->|"CDC outbox"| KO[[orders.fc-A]]
    KO -->|"order_cancel_requested"| WMS[WMS, per FC]
    WMS -->|"allocated, short, packed, shipped,<br/>cancel result: cancelled or too_late"| KW[[wms.stock-events,<br/>wms.order-status]]
    KW -->|"status, cancel result"| ORD
    S[Sellers] -->|"ship, seller cancel"| ORD
    ORD -->|"void, or capture<br/>at the first shipment"| PAY[Payment service]
    ODB -->|"CDC"| SV[(Seller order view<br/>by seller_id)]

    class B,S client
    class ORD,PAY service
    class ODB,SV store
    class KO,KW queue
    class WMS external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```


## D4. Happy paths, one per FR

**FR1, product page:** [solution §4.1](solution.md#41-buyers-search-and-open-a-product-page-with-offers-price-and-availability).

**FR2, seller count and WMS snapshot:** [solution §4.2](solution.md#42-sellers-register-listings-and-stock-and-warehouse-events-adjust-platform-held-stock).

**FR3, cart on two devices:** [solution §4.3](solution.md#43-buyers-add-update-and-remove-cart-items-and-see-current-price-and-availability).

**FR4, normal order:** [solution §4.4](solution.md#44-placing-an-order-reserves-stock-prices-it-authorizes-payment-and-confirms-it-safe-to-retry).

**FR4, flash deal setup (Flow 2, steps 1 and 6).** Capacity is booked with each FC before a unit is carved, so a deal never sells more than its FCs can ship that night. At close only capacity no claim can still use goes back; the rest follows when the last claim resolves.

```mermaid
%% D4 FR4 deal setup: capacity_hold per FC first, carve at most the granted units, then buckets and leases. Unused capacity goes back in two releases: at close, and when the last claim resolves.
sequenceDiagram
    autonumber
    participant M as Merchandising
    participant DS as Deal service
    participant W as WMS, FC A and FC B
    participant I as Inventory, shard 7
    participant G as Gate nodes
    M->>DS: deal D, sku_77, 10,000 units, 10:00 to 10:30
    DS->>W: capacity_hold D, FC A, tonight, dawn cut-off, 6,000
    DS->>W: capacity_hold D, FC B, tonight, dawn cut-off, 4,000
    W-->>DS: capacity_hold_result D, granted 6,000 at FC A and 4,000 at FC B
    DS->>I: carved + 6,000 on fc A and + 4,000 on fc B, where sellable allows
    DS->>DS: 40 bucket rows of 250 across 16 shards
    G->>DS: 09:55, each node leases 2 buckets, epoch 1
    Note over DS,G: 10:00 to 10:30, claims and converts as below
    DS->>I: 10:30, return units never issued and released claims
    DS->>W: 10:30, capacity_release D, granted minus drawn minus open claims
    Note over DS,W: claims behind unknown payments stay carved and booked
    DS->>W: by 11:00, last claim resolved, final capacity_release D
```

**FR4, a flash-sale claim to a confirmed order (Flow 2).** The claim is the reservation; the rest is the normal saga with the deal price bound to the token.

```mermaid
%% D4 FR4 flash: one winner's path. The gate issues the unit from memory and commits it in a 5 ms batch. The saga uses the token as the line's reservation, writes the hold in the convert, and confirms with the DEAL_PURCHASE row.
sequenceDiagram
    autonumber
    participant B as Buyer
    participant G as API gateway
    participant N as Gate node 7
    participant D as Bucket row and ledger
    participant O as Order service
    participant I as Stock row, shard 7
    B->>G: POST /deals/D/claim at 10:00:00.040
    G->>N: deal OPEN, routed by buyer_id
    N->>N: no claim for this buyer yet, bucket 13 has 41 left, take 1
    N->>D: batch of 12, issued + 12 where epoch is 1
    D-->>N: committed
    N-->>B: token t1, expires 10:05:00
    B->>O: POST /checkouts with t1, then POST /orders
    O->>N: verify t1 belongs to this buyer and is HELD
    O->>O: quote at deal price 9,900, authorize
    O->>N: convert t1, ledger row CONVERTED
    O->>I: carved minus 1, sold plus 1, hold ord_9-1, one transaction
    O->>O: CONFIRMED, DEAL_PURCHASE row, outbox with deal_id
    O-->>B: 201, arrives tomorrow by 7 am
```

**FR5, cancel before shipment:** [solution §4.5](solution.md#45-buyers-see-order-status-and-history-and-cancel-before-shipment).

**FR5, a short pick and a re-source (Flow 6).** The WMS reports the short; commerce decides.

```mermaid
%% D4 FR5 short pick: FC A has no unit left in any bin. The short carries the stock version of the snapshot written just before it, commerce re-sources the line to FC B as a new fulfillment and tells the buyer the new promise.
sequenceDiagram
    autonumber
    participant W as WMS FC A
    participant I as Inventory
    participant O as Order service
    participant W2 as WMS FC B
    participant B as Buyer
    W->>W: 01:40, bin empty, no other bin in FC A
    W->>I: stock_changed FC A, corrected count, version 91
    W->>I: order_line_short ord_5-1, sku_31, 1, no_stock, version 91
    I->>I: drop hold ord_5-1 once version 91 is applied
    I->>O: line 1 of ord_5 is short
    O->>O: re-source keyed on ord_5-1 line 1, only if not CANCEL_REQUESTED
    O->>I: reserve sku_31 in FC B and convert at once
    I-->>O: FC B has stock and outbound capacity
    O->>W2: order_confirmed as fulfillment ord_5-2, on orders.fc-B
    O-->>B: one item now arrives this afternoon, cancel it if you prefer
```

## D5. Failure paths

**PSP timeout and a second tap:** [solution §5.2](solution.md#52-the-payment-call-times-out-and-the-buyer-taps-again-how-do-you-avoid-a-double-charge-a-double-order-or-stock-stuck-in-a-reservation). **Inventory shard primary dies:** [solution §10.4](solution.md#104-failure-timeline).

**WMS events: the normal order, a replay, a duplicate.** The WMS writes `stock_changed vN` and `order_allocated vN` in one transaction, stock first. A hold leaves `sold` only once a snapshot at or after its allocation version is applied, so even a reversed pair could not over-count (solution §5.3).

```mermaid
%% D5 WMS events: stock first, then the allocation, then a replay and a duplicate. Sellable is never above 118. It is 2 under for the milliseconds between the first two events.
sequenceDiagram
    autonumber
    participant W as WMS FC A
    participant K as wms.stock-events, sku_77 partition
    participant I as Inventory consumer
    participant D as Row sku_77 fc A
    Note over D: on_hand 120 at v41, sold 2 for ord_1-1, sellable 118
    W->>K: one transaction, stock_changed 118 v42, then order_allocated v42
    K->>I: stock_changed v42
    I->>D: on_hand 118 at v42, hold still in sold, sellable 116
    K->>I: order_allocated ord_1-1, 2 units, v42
    I->>D: row already at v42, drop hold, sold 0, sellable 118
    K->>I: replayed stock_changed v41 after a restart
    I->>D: ignored, older than v42
    K->>I: duplicate order_allocated v42
    I->>D: no hold left, no-op
    Note over W,D: had order_allocated come first, the hold would wait for v42
```

**A gate node dies mid-sale.** Its buckets pause for the 2 s lease plus a 1 s margin. Nothing it had not committed was ever issued, and nothing it committed is lost: the successor rebuilds the winners and hands back their tokens.

```mermaid
%% D5 gate crash: node 7 dies right after a batch commits, before answering. Node 9 takes its buckets and its buyer range with a higher epoch, rebuilds the winners from HELD rows, and answers resumed claims with their existing tokens.
sequenceDiagram
    autonumber
    participant G7 as Gate node 7
    participant D as Bucket rows 13 and 14
    participant G9 as Gate node 9
    participant GW as Gateways
    Note over G7: 10:00:00.06, owns 13 and 14, epoch 1
    G7->>D: batch of 9 commits, issued 180 of 250
    G7->>G7: process dies before answering, more claims in memory
    GW->>G7: claims for its buyers fail, clients wait to retry
    Note over D: lease expires at 10:00:02
    G9->>D: 10:00:03, take the lease, epoch 2
    D-->>G9: issued 180, 70 units left
    G9->>G9: take node 7 buyer range, rebuild winners and timers from HELD rows
    GW->>G9: resumed claims, forwarded even past SOLD_OUT
    G9-->>GW: the 9 winners get their existing tokens
    G9->>D: new batches carry epoch 2
    Note over G7,D: claims only in memory were never issued, so no oversell
```

**A late authorization after the stock was released.** The 30-minute ceiling releases the stock; after it the resolver only reads by reference, and a later "yes" is voided (two-step card) or cancelled and refunded (one-step PG), never confirmed.

```mermaid
%% D5 late success: a PSP outage outlasts the 30 minute ceiling. The stock is released, and the authorization that turns up later is voided.
sequenceDiagram
    autonumber
    participant P as Payment service
    participant X as PSP
    participant O as Order service
    participant I as Inventory
    participant B as Buyer
    Note over P,X: 10:00, attempt ord_8-p1 UNKNOWN, PSP outage
    P->>X: resolver every 5 min, no answer
    O->>I: 10:30, ceiling reached, release rsv_8
    O->>O: ord_8 PAYMENT_UNRESOLVED
    O-->>B: not confirmed, any hold on your card will drop
    X-->>P: 11:10, the hourly read-only lookup says AUTHORIZED
    P->>O: late authorization for ord_8
    O->>O: not confirmable, the stock is gone
    P->>X: void, key void-ord_8-p1, or cancel and refund on a one-step PG
```

**The PSP slows to 10 s for 15 minutes.** Calls are cut at 3 s and become unknown, the breaker moves new orders, the resolver drains the unknowns at a capped rate.

```mermaid
%% D5 PSP brownout. Each call is cut at 3 s and becomes UNKNOWN, the breaker opens in ~20 s, new orders move to the second PSP, the resolver drains the unknowns at a capped rate.
sequenceDiagram
    autonumber
    participant O as Order service
    participant P as Payment service
    participant X1 as PSP 1
    participant X2 as PSP 2
    participant OC as On-call
    Note over X1: 20:00, p50 rises to 10 s
    P->>X1: authorize calls, each cut at 3 s
    P->>P: attempts UNKNOWN, stock held up to 30 min
    P->>P: 20:00:20, over 50% timeouts, breaker OPEN
    P->>OC: page, PSP 1 breaker open
    O->>P: new orders
    P->>X2: new attempts only
    P->>X1: resolver, 200 per s, same keys
    X1-->>P: saved results, mostly AUTHORIZED
    Note over P,X1: 20:15, PSP 1 recovers, half-open probes, breaker CLOSED
```


## D6. Activity / decision flow

**Truth at reserve:** [solution §5.4](solution.md#54-search-shows-in-stock-but-checkout-says-sold-out-how-fresh-is-availability-and-where-is-the-truth-checked). **What the buyer pays:** [solution §5.5](solution.md#55-the-price-or-a-coupon-changes-between-the-cart-and-checkout-what-does-the-buyer-see-and-pay).

**Pool pick at reserve.** Commerce picks the FC at reservation, per the shared contract. Capacity admission is a soft counter: each reservation takes a capacity token by a conditional, idempotent decrement on one of 8 tally shards for that FC and cut-off, keyed by its reservation id, and returns it with the reservation; a recount from live reservation and hold rows every 60 s repairs any crash drift. The worst overshoot is the reserves that race inside one decrement, tens of units, far under the FC's ~2% planning reserve. It skips an FC whose feed has been silent for over 30 s, or whose `fc_capacity` for the cut-off that meets the promise (dawn or next day), minus its open holds that carry no `deal_id` and its live reservations at that FC and cut-off, is under a 2% margin. Holds alone are not enough: in a 1,000-night simulation 151 nights missed the truck, because ~1.7k units sit in reservations at 12.5 units a second; with live reservations subtracted, none did. A hold's units keep counting until a capacity report at or above its `capacity_version` is applied; deal holds are covered by the deal's capacity hold. Capacity silent for 2 minutes in the last hour before a cut-off counts as 0, and a building whose heartbeat reports `floor_contact_age` over 2 minutes gets no dawn promises.

```mermaid
%% D6 pool pick: seller pool or FC pools in promise order, skipping FCs without capacity, one conditional update per try, all on the SKU's shard.
flowchart TD
    R[Reserve one line,<br/>sku_77, qty 1, address] --> C{Offer fulfilled<br/>by an FC?}
    C -->|"no"| SP[Seller pool row]
    C -->|"yes"| L[Next FC by promise<br/>for this address]
    L --> CAP{Feed and floor fresh, and a<br/>capacity token for this cut-off?}
    CAP -->|"no"| L
    CAP -->|"yes"| U[Insert reservation, then<br/>reserved + q where sellable at least q]
    SP --> U
    U --> OK{1 row changed?}
    OK -->|"yes"| H[HELD, expires in 10 min]
    OK -->|"no, FCs left"| L
    OK -->|"no, none left"| F[OUT_OF_STOCK, with other<br/>offers and notify me]

    class R,SP,L,U service
    class C,CAP,OK decision
    class H store
    class F client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

**A claim inside one gate node.** Claims are taken in memory, flushed every 5 ms as one fenced transaction, and answered only after it commits.

```mermaid
%% D6 gate claim, inside one gate node: claims for a bucket are taken in memory, flushed every 5 ms as one fenced transaction, and answered only after it commits.
flowchart LR
    C[Claims for bucket 7<br/>~2.5k per s] -->|"keyed by deal and buyer,<br/>repeat gets same token"| A[Bucket actor<br/>remaining in memory]
    A --> Q{Units left?}
    Q -->|"no"| NO[Answer SOLD_OUT<br/>from memory]
    Q -->|"yes"| PB[Pending batch<br/>flush at 5 ms or 100]
    PB -->|"issued + n where epoch = e<br/>and issued + n within units"| DB[(Bucket row + ledger rows<br/>one transaction)]
    DB -->|"committed"| OK[Answer n buyers<br/>with tokens]
    DB -->|"0 rows, lease lost"| STOP[Stop, answer try again]
    TW[Timer wheel<br/>skips extend_until] -->|"per row HELD to RELEASED,<br/>issued minus rows changed"| DB
    TW -->|"units back"| A

    class C client
    class A,PB,OK,NO,STOP,TW service
    class Q decision
    class DB store

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```


**The reservation sweeper.** Releases expired holds and loses races to confirm gracefully. A payment extension rewrites the indexed `expires_at`, so the sweeper never pages through extended rows; the alert is on the oldest overdue `HELD` row.

```mermaid
%% D6 sweeper: one pass per shard per second over rows whose indexed expires_at has passed. Extended rows have a later expires_at, so they are not read at all. Release and convert race on state = HELD and exactly one wins.
flowchart TD
    S[Pass every 1 s per shard] --> Q[Read up to 500 HELD rows<br/>by index on expires_at]
    Q --> O{Oldest overdue row<br/>older than 60 s?}
    O -->|"yes"| PG[Page, the sweeper is behind]
    O -->|"no"| REL
    PG --> REL[Release where state is HELD,<br/>reserved minus q]
    REL --> W{1 row changed?}
    W -->|"no"| LOST[Confirm won the race,<br/>nothing to do]
    W -->|"yes"| EV{Sellable crossed zero?}
    EV -->|"yes"| AV[Outbox availability IN_STOCK]
    EV -->|"no"| FIN[Done]

    class S,Q,REL,LOST,FIN service
    class O,W,EV decision
    class AV queue
    class PG client

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

**The PSP call path (solution §5.6).** Browse reads only the read side. Checkout's PSP calls go through a capped pool with a breaker. The pool is red: it is what a slow PSP fills first, and its cap keeps it from filling anything else.

```mermaid
%% D6 PSP call path, the bulkheads of solution 5.6. Browse reads only the read side. Checkout's PSP calls go through a capped pool with a breaker. The PSP call pool is red: it is what a slow PSP fills first, and the cap is what keeps it from filling anything else.
flowchart LR
    B[Buyers] -->|"pages, search"| BR[Browse fleet<br/>product page, search]
    BR -->|"stale-if-error"| RD[(Read model, Redis,<br/>search index)]
    B -->|"place order"| CK[Checkout fleet<br/>order saga]
    CK -->|"reserve, under 100 ms"| INV[(Inventory DB<br/>semi-sync)]
    CK -->|"authorize"| POOL[PSP call pool<br/>cap 1,200, timeout 3 s]
    POOL --> BRK{Breaker open?}
    BRK -->|"no"| PSP1[PSP 1]
    BRK -->|"yes, new attempts only"| PSP2[PSP 2]
    POOL -->|"timeout"| RES[Resolver<br/>200 per s per PSP]
    RES -->|"same key, or query by order"| PSP1

    class B client
    class BR,CK,RES service
    class RD,INV store
    class POOL critical
    class BRK decision
    class PSP1,PSP2 external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```


## D7. Entity relationship

Money-path entities with keys and TTLs, and the catalog and checkout entities around them: [solution §3.3](solution.md#33-data-model).

## D8. State machines

**Order.** The checkout states are one composite. After `CONFIRMED`, cancellation and shipment state are tracked per line and per fulfillment (an order can have one line packed at FC A while a re-sourced line is allocated at FC B), and the physical owner's events move them. The order is `CANCELLED` only when every line is; otherwise `PARTIALLY_CANCELLED`, and the first capture is smaller.

```mermaid
%% D8 order lifecycle. Checkout is the saga. After CONFIRMED, states are per line and fulfillment, moved by WMS or seller events. CANCELLED needs every line cancelled. A cancel is a request that the owner of the unit can refuse.
stateDiagram-v2
    direction LR
    [*] --> Checkout : POST /orders
    state Checkout {
        direction LR
        RESERVING --> PRICING : lines held
        PRICING --> AWAITING_BUYER : total went up
        AWAITING_BUYER --> PRICING : buyer accepts
        PRICING --> PAYING : coupon held
        PAYING --> PAYING : declined, new card
    }
    Checkout --> CONFIRMED : authorized, converted
    Checkout --> FAILED : stock, decline, expiry
    CONFIRMED --> ALLOCATED : order_allocated
    ALLOCATED --> PACKED : order_packed
    PACKED --> SHIPPED : order_shipped
    SHIPPED --> DELIVERED : carrier scan
    CONFIRMED --> CANCEL_REQUESTED : buyer cancels
    ALLOCATED --> CANCEL_REQUESTED : buyer cancels
    CANCEL_REQUESTED --> CANCELLED : every line, voided
    CANCEL_REQUESTED --> PARTIALLY_CANCELLED : some lines cancelled
    PARTIALLY_CANCELLED --> SHIPPED : rest ships, less captured
    CANCEL_REQUESTED --> PACKED : too_late, packed
    CANCEL_REQUESTED --> SHIPPED : too_late, shipped
    DELIVERED --> [*]
    CANCELLED --> [*]
    FAILED --> [*]
```

**Reservation, then WMS hold.** A reservation lives at most 10 minutes (5 for deals) unless a payment is unknown. A converted FC line becomes a hold per fulfillment, SKU and FC, counted in `sold` until the WMS's snapshot covers it.

```mermaid
%% D8 reservation and WMS hold as one chain. HELD is extended only while a payment is unknown, up to 30 minutes. A hold drops only once the snapshot at or after its allocation version is applied.
stateDiagram-v2
    direction LR
    [*] --> HELD : reserve, TTL 10 min
    HELD --> HELD : payment unknown, extend
    HELD --> RELEASED : fail, cancel or expiry
    HELD --> CONVERTED : order confirmed
    CONVERTED --> [*] : seller pool line
    CONVERTED --> OPEN : FC line, hold created
    OPEN --> ALLOCATED : order_allocated vN
    ALLOCATED --> DROPPED : snapshot vN applied
    OPEN --> DROPPED : short at vN, or cancel
    RELEASED --> [*]
    DROPPED --> [*]
```

**Payment attempt.** `UNKNOWN` is a real state with an owner (the resolver), not a failure.

```mermaid
%% D8 payment attempt: the row exists before the PSP call. UNKNOWN is resolved by asking again; after the ceiling the resolver only reads, and a late yes is voided or refunded. Capture happens once, at the first shipment.
stateDiagram-v2
    direction LR
    [*] --> CREATED : row before the call
    CREATED --> AUTHORIZED : PSP ok
    CREATED --> DECLINED : PSP declines
    CREATED --> REQUIRES_ACTION : 3DS needed
    REQUIRES_ACTION --> AUTHORIZED : buyer passes 3DS
    REQUIRES_ACTION --> DECLINED : fails or abandons
    CREATED --> UNKNOWN : timeout or 5xx
    UNKNOWN --> AUTHORIZED : resolver finds yes
    UNKNOWN --> DECLINED : resolver finds no
    UNKNOWN --> UNRESOLVED : 30 min ceiling
    UNRESOLVED --> VOIDED : late yes, void or refund
    AUTHORIZED --> CAPTURED : first shipment
    CAPTURED --> CAPTURED : later short, refund
    AUTHORIZED --> VOIDED : cancel or no order
    CAPTURED --> [*]
    VOIDED --> [*]
    DECLINED --> [*]
```

## D9. Deployment / topology

One region, three AZs. Each inventory and order shard has its primary in one AZ and semi-synchronous replicas in the other two; primaries are spread so one AZ holds about a third. FCs run their own WMS cells on site and reach Kafka over private links.

```mermaid
%% D9: one region, 3 AZs. Every fleet runs in every AZ. Shard primaries are spread, each with a semi-sync replica in another AZ. Shard 7's primary is red: it holds the flash-sale SKU's row.
flowchart LR
    subgraph AZA[AZ a]
        GA[Gateways, browse, checkout,<br/>gate nodes, a third each]
        IA[(Inventory shards 0 to 5<br/>primaries)]
        KA[[Kafka, 2 brokers]]
    end
    subgraph AZB[AZ b]
        GB[Same fleets]
        IB[(Inventory shards 6, 8 to 10<br/>primaries)]
        H7[(Shard 7 primary<br/>flash SKU row)]
        KB[[Kafka, 2 brokers]]
    end
    subgraph AZC[AZ c]
        GC[Same fleets]
        IC[(Inventory shards 11 to 15<br/>primaries)]
        KC[[Kafka, 2 brokers]]
    end
    CDN[CDN and edge] -->|"requests, any AZ"| GA
    H7 -->|"semi-sync, AFTER_SYNC"| IC
    IA -->|"semi-sync replicas"| IB
    KA <-->|"RF 3, acks all"| KB
    KB <-->|"RF 3"| KC
    FC[WMS cells, on site<br/>one per FC] -->|"outbox over private links"| KB
    GC -->|"authorize, capture"| PSP[PSPs]

    class CDN client
    class GA,GB,GC service
    class IA,IB,IC store
    class H7 critical
    class KA,KB,KC queue
    class FC,PSP external

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

What crosses an AZ boundary: semi-sync replication (about one in-region round trip inside every commit, which is part of the ~1 ms lock window), Kafka replication, and requests to a shard primary in another AZ. Order DB shards, the read model, Redis and the search cluster are spread the same way and left out to stay under 15 nodes. Losing one AZ promotes a replica for about a third of the shards (~10 to 30 s each) and leaves two thirds of every fleet, which is sized N+1 per AZ.

## D10. Scaling / partitioning

16 inventory shards by `hash(sku_id)`, ~31M stock rows each, ~560 writes a second each at peak. The problem is one row, not one shard: a deal SKU without the gate asks one row for 100x to 300x what it can do.

```mermaid
%% D10: sku_id picks one of 16 shards. A deal SKU without the gate makes one row on shard 7 hot. With the gate, claims go to 40 bucket rows spread over all shards, and shard 7's row sees one convert per confirmed order, ~55 a second.
flowchart LR
    R[Reserve or claim<br/>for sku_id] -->|"hash sku_id mod 16"| H{Live deal<br/>for this SKU?}
    H -->|"no, almost every SKU"| S0[Shard 0<br/>~31M rows, ~560 writes per s]
    H -->|"no"| S15[Shard 15<br/>~31M rows, ~560 writes per s]
    H -->|"no gate configured"| S7[Shard 7, row sku_77<br/>100k per s wanted,<br/>~300 to 1,000 per s possible]
    H -->|"yes, claims"| GT[Gate, 20 nodes<br/>routed by buyer_id]
    GT -->|"hash deal and bucket mod 16"| BK[40 bucket rows<br/>2 or 3 per shard,<br/>up to 200 batches per s each]
    BK -->|"each confirmed claim converts<br/>on the stock row"| S7G[Shard 7, row sku_77<br/>~55 updates per s]

    class R,GT service
    class H decision
    class S0,S15,BK,S7G store
    class S7 critical

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- Without the gate: `100k ÷ 300 to 1,000 = 100x to 300x` over on one row, and the shard's connection pool (64 per inventory node) fills with waiters, so a sixteenth of the catalog fails with it; the same-SKU batching guard (5 ms batches, at most 16 connections for one SKU) keeps the rest of shard 7 alive. With the gate: 40 bucket rows, each written by one owner at most 200 times a second.
- Why not shard finer to fix it: more shards spread SKUs, not one SKU. A single row is the unit of contention whatever the shard count.

## D11. Failure mode map

Component, what fails, blast radius, mitigation. Two trees to stay under 15 nodes. Matches solution §8.

```mermaid
%% D11 tree 1: the money path. The hot SKU row is red: it is what breaks first if the gate is bypassed.
flowchart TD
    ROOT[Money path] --> ROW[Flash SKU stock row]
    ROOT --> SH[Inventory shard primary]
    ROOT --> GN[Deal gate node]
    ROOT --> KF[Kafka or an outbox relay]
    ROW -->|"gate bypassed"| ROWB[Lock queue, pool exhausted,<br/>1/16 of SKUs fail]
    ROWB -->|"mitigate"| ROWM[Same-SKU batching, 16 connections<br/>per SKU, lock wait 1 s]
    SH -->|"dies"| SHB[Reserves fail for 1/16<br/>of SKUs for 10 to 30 s]
    SHB -->|"mitigate"| SHM[Semi-sync replica promoted,<br/>deterministic reservation ids]
    GN -->|"dies mid-sale"| GNB[500 units paused ~3 s]
    GNB -->|"mitigate"| GNM[2 s lease takeover, epoch fencing,<br/>winners rebuilt, resume claims]
    KF -->|"down"| KFB[WMS gets orders late,<br/>FC stock frozen, pages stale]
    KFB -->|"mitigate"| KFM[Outboxes keep everything,<br/>replay in commit order]

    class ROOT,SH,GN,KF service
    class ROW critical
    class ROWB,SHB,GNB,KFB decision
    class ROWM,SHM,GNM,KFM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

```mermaid
%% D11 tree 2: dependencies and our own deploys. The bad inventory deploy has the biggest blast radius: every SKU can oversell at once.
flowchart TD
    ROOT[Dependencies and change] --> PSP[PSP]
    ROOT --> WMS[WMS cell or its feed]
    ROOT --> SRCH[Search cluster]
    ROOT --> DEP[Inventory deploy]
    PSP -->|"10 s calls"| PSPB[Checkouts pending,<br/>browse untouched]
    PSPB -->|"mitigate"| PSPM[3 s timeout, UNKNOWN,<br/>breaker, second PSP]
    WMS -->|"no heartbeat for 30 s"| WMSB[FC stock frozen,<br/>short picks could rise]
    WMSB -->|"mitigate"| WMSM[Pool sells only beyond a margin,<br/>holds keep sold units out,<br/>reconcile per SKU and FC]
    SRCH -->|"degraded"| SRCHB[Search slow or partial,<br/>pages and checkout fine]
    SRCHB -->|"mitigate"| SRCHM[Result cache, category<br/>pages from the read model]
    DEP -->|"sellable computed wrong"| DEPB[Every SKU can oversell]
    DEPB -->|"mitigate"| DEPM[Canary by SKU hash,<br/>invariant checks, auto rollback]

    class ROOT,PSP,WMS,SRCH,DEP service
    class PSPB,WMSB,SRCHB,DEPB decision
    class PSPM,WMSM,SRCHM,DEPM store

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## D12. Rollout / migration

From a monolith whose order transaction decrements `products.stock`, calls the PG inline and feeds search from a nightly batch. Each SKU has an owner flag with an `effective_from` a minute ahead, so every reservation has exactly one owner. Rollback at any inventory step is the flag; the movement ledger rebuilds the old column.

```mermaid
%% D12: migration phases with a rollback point after each. The read side moves first because it cannot oversell anything.
gantt
    title Monolith stock column to inventory service, saga and deal gate
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Read side
    CDC into read model and search index           :a1, 2026-12-01, 21d
    Rollback point, pages back to the monolith     :milestone, m1, after a1, 0d
    section Inventory
    Inventory service in shadow, compare per minute :a2, after a1, 14d
    Owner flag on 1 percent of SKUs                :a3, after a2, 4d
    10 percent                                     :a4, after a3, 4d
    50 percent                                     :a5, after a4, 5d
    100 percent                                    :a6, after a5, 5d
    Rollback point per step, flag and ledger       :milestone, m2, after a6, 0d
    section Checkout
    Saga, attempts and keys for new orders only    :a7, after a6, 14d
    Rollback point, new orders to the old path     :milestone, m3, after a7, 0d
    section Deals and WMS
    Deal gate for new deals only                   :a8, after a7, 10d
    WMS contract, reconciliation, drop the column  :a9, after a8, 21d
```

Gates between steps: the shadow comparison shows zero sellable mismatches per SKU for 3 days, the invariant checker is clean, the reserve error rate is within 0.1 points of the monolith's, and no deal is scheduled during a switch.
