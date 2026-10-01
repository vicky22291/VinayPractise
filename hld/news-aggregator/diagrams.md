# Diagrams: news aggregator / personalized news feed

> One-line answer: the D1 to D12 set from `hld/CLAUDE.md` §4, each drawn once. The diagrams already embedded in [`solution.md`](solution.md) are linked here, not repeated. Numbers come from [`solution.md` §2](solution.md#2-back-of-envelope); anything else is marked "est.".

| # | Diagram | Where |
|---|---|---|
| D1 | Context | below |
| D2 | Data flow, ingest half and serving half | below |
| D3 | Component architecture (final design) | [`solution.md` §6](solution.md#6-final-design-and-the-core-flows) |
| D4 | Happy path per FR | FR1 poll: [Flow 1](solution.md#flow-1-a-publisher-posts-a-user-sees-it-fr1). FR2: [Flow 2](solution.md#flow-2-subscribe-then-refresh-fr2). FR3: [Flow 3](solution.md#flow-3-open-for-you-page-1-fr3). FR4: [Flow 4](solution.md#flow-4-page-2-while-40-new-articles-arrive-fr4). FR5: [Flow 5](solution.md#flow-5-click-through-fr5). FR1 via WebSub push: below |
| D5 | Failure paths | Publisher rate limits us: [Flow 6](solution.md#flow-6-a-publisher-rate-limits-us-during-breaking-news-failure). Postgres primary dies: [§10.4](solution.md#104-failure-timeline). Feed server dies mid-request, Redis session shard lost, outbox relay re-publishes: below |
| D6 | Decision flow | One poll: [§5.1](solution.md#51-publishers-return-only-their-latest-25-rate-limit-you-and-go-down-how-do-you-see-every-article-within-5-minutes). One feed request: below |
| D7 | Entity relationship | [`solution.md` §3.3](solution.md#33-data-model) |
| D8 | State machines | Publisher circuit, story lifecycle, article lifecycle: below |
| D9 | Deployment / topology | below |
| D10 | Scaling / partitioning | below |
| D11 | Failure mode map | below |
| D12 | Rollout / migration | below |

## D1. Context (zoom-out)

The whole system is one box. Publishers and hubs push items in, apps pull feeds out, editors own one label, and the CDN carries the bytes.
```mermaid
%% D1: context. Our system is one box. Every external actor and what flows on each edge.
flowchart LR
    SYS["News aggregator<br/>poll, dedup, feed, clicks"]:::service -->|"conditional GET latest 25 ~13/s,<br/>HEAD rechecks ~2/s, host budget"| PUB["Publishers<br/>~10k, latest 25 endpoints"]:::external
    PUB -->|"304, or 200 with 25 items,<br/>article page once per article"| SYS
    PUB -->|"new item ping"| HUB["WebSub hubs"]:::external
    SYS -->|"subscribe with hub.secret,<br/>renew before ~10-day lease ends"| HUB
    HUB -->|"hub.challenge, then<br/>signed deliveries"| SYS
    APP["User apps and web<br/>100 M DAU"]:::client -->|"feeds 120k/s spike, follows,<br/>/r/ clicks, impression batches"| SYS
    SYS -->|"20 cards JSON,<br/>302 to publisher URL"| APP
    APP -->|"reads the article"| PUB
    SYS -->|"breaking candidates"| ED["Editors"]:::client
    ED -->|"confirm or clear label,<br/>per editorial market"| SYS
    SYS -->|"thumbnails, snapshots,<br/>top-feed objects every 30 s"| OBJ[("Object store")]:::store
    OBJ -->|"thumbnails and top feed<br/>on a miss"| CDN["CDN edges"]:::cache
    SYS -->|"purge top feed by key<br/>when a label is cleared"| CDN
    CDN -->|"thumbnails ~7 GB/s spike,<br/>top feed when shed"| APP
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- **Trust boundary:** publishers and hubs sit outside it. Deliveries need a valid HMAC, and every URL they send passes the SSRF rules in [§10.10](solution.md#1010-security-and-abuse). The red fetcher is inside the box on the publisher edge (D2a). The top feed is a pre-built object, so the CDN fallback works with the feed tier down.

## D2a. Data flow, ingest half

Name, format, size and rate on every edge. Ingest moves ~5 items a second, so the bytes are trivial. The hard part is correctness at the red edge.
```mermaid
%% D2a: ingest data flow. Stores and Kafka topics are cylinders, processes are rounded. Rates are averages unless marked peak.
flowchart LR
    PUB["Publishers ~10k"]:::external -->|"latest 25 as RSS, Atom or JSON,<br/>304 ~300 B or 200 ~50 KB, ~13/s,<br/>HEAD rechecks ~2/s"| FET("Fetcher<br/>poll workers"):::critical
    HUB["WebSub hubs"]:::external -->|"signed ping ~1 KB,<br/>at most ~3.5/s"| FET
    SRC[("feed_source<br/>Postgres, 10k rows")]:::store -->|"due rows, up to 20 per claim,<br/>lease_token + 1, ~13 rows/s"| FET
    FET -->|"etag, known_ids + title hashes<br/>~1.2 KB, next_poll_at, ~13 rows/s"| SRC
    FET -->|"new ids + changed hashes, JSON ~2 KB,<br/>~5/s with edits, ~35/s peak"| RAW[("raw-items<br/>Kafka, 12 partitions")]:::queue
    RAW -->|"raw item ~2 KB, ~5/s"| NORM("Normalizer + clusterer<br/>URL, hashes, SimHash, story"):::service
    NORM -->|"article + outbox rows ~2 KB,<br/>~5 upserts/s, ~600 MB/day"| ADB[("Article DB<br/>Postgres, ~220 GB/yr")]:::store
    ADB -->|"article.upserted + label events,<br/>JSON ~1 KB, ~5/s via outbox relay,<br/>+ watermark W per partition"| AEV[("article-events<br/>Kafka, 12 partitions, 7 days")]:::queue
    AEV -->|"new article, ~3.5/s"| IMG("Page worker<br/>inside the host budget"):::service
    PUB -->|"article page + og:image ~200 KB est.,<br/>once per article, ~3.5/s, ~35/s peak"| IMG
    IMG -->|"3 sizes x ~20 KB,<br/>~10 objects/s, ~18 GB/day"| OBJ[("Object store<br/>thumbnails")]:::store
    IMG -->|"article.image_ready,<br/>~100 B, ~3.5/s"| AEV
    IMG -->|"URL update when the same-domain<br/>rel=canonical differs, rare"| ADB
    AEV -->|"every event to every server,<br/>~1 KB, ~5/s x 36 to 60"| FEED("Feed servers, Flink,<br/>top-feed builder, see D2b"):::service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- "~5/s with edits" is 3.5 new articles/s plus ~150k edits a day (~1.7/s). Edits pass the fetcher because `known_ids` keeps an 8-byte title hash per id. HEAD rechecks cover the last 24 h of top-500 articles (~150k a day); a 404 or 410 is a retraction. The page worker's fetch spends the same per-host tokens as polls, so a burst of new articles cannot push a publisher past its limit. 60 servers each reading ~5 KB/s of `article-events` is ~300 KB/s of broker egress. Nothing here needs sharding.

## D2b. Data flow, serving half

Per page the network carries at most one user-state read (~1 KB) and one session op (~2.6 KB). The ~0.9 GB of cards never leaves the server.
```mermaid
%% D2b: serving data flow. Redis, the KV stores, Kafka and the object store are cylinders. Avg rates, spike where it sets the size.
flowchart LR
    APP["User apps"]:::client -->|"feed request ~1 KB,<br/>11.6k/s avg, 120k/s spike"| FEED("Feed servers<br/>72 h corpus in RAM"):::service
    FEED -->|"feed page JSON ~15 KB,<br/>20 cards + breaking field"| APP
    APP -->|"/r/ click 5.8k/s avg, never shed,<br/>new_count ~8k/s est."| FEED
    APP -->|"impression batch every ~60 s,<br/>~17k req/s est."| EC("Events collector"):::service
    APP -->|"follow ~100 B,<br/>~100/s est."| USV("User service"):::service
    USV -->|"row + subs_version + 1"| KV[("Subscription KV<br/>~5 B rows, ~200 GB")]:::store
    USV -->|"delete cached entry"| UC[("User cache<br/>Redis, ~100 GB")]:::cache
    UC -->|"subs + profile ~1 KB,<br/>only when ranking"| FEED
    KV -->|"consistent read on a miss<br/>or an older subs_version"| FEED
    AEV[("article-events")]:::queue -->|"article.upserted ~1 KB,<br/>~5/s to every server"| FEED
    FEED -->|"300 ids ~2.6 KB, 3.5k SET/s,<br/>35k/s spike"| SES[("Feed sessions<br/>Redis, TTL 20 min")]:::cache
    SES -->|"slice, GETRANGE ~200 B,<br/>~85k/s spike"| FEED
    FEED -->|"snapshot + offsets ~1 GB<br/>every 60 s, per region"| OBJ[("Object store")]:::store
    OBJ -->|"snapshot at boot, ~10 s"| FEED
    FEED -->|"click ~60 B, 5.8k/s,<br/>key user_id"| CK[("clicks + impressions<br/>Kafka, 48 partitions")]:::queue
    EC -->|"impression ~60 B,<br/>231k/s avg"| CK
    CK -->|"~237k events/s avg,<br/>~2.3 M/s, ~140 MB/s spike"| FL("Flink"):::service
    AEV -->|"story sizes"| FL
    FL -->|"topic vector, ~10 s"| UC
    FL -->|"profile, durable"| PS[("Profile store")]:::store
    FL -->|"velocity, trending,<br/>breaking candidates"| FEED
    AEV -->|"cards + labels"| TB("Top-feed builder"):::service
    TB -->|"top feed JSON ~15 KB per<br/>region + language, every 30 s"| OBJ
    OBJ -->|"thumbnails + top feed<br/>on a miss"| CDN["CDN edges"]:::cache
    CDN -->|"thumbnails ~15 KB, ~480k/s,<br/>~7 GB/s spike, top feed on 503"| APP
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
```

- **The biggest byte stream is thumbnails** (~7 GB/s at spike, ~1.8 PB a month), not feed JSON (120k x 15 KB = ~1.8 GB/s). That is why images are the cost lever in [§8](solution.md#8-staff-level-notes). 480k thumbnails/s = 120k pages x 8 visible cards x 50% client-cache miss.
- **Impressions are 40x clicks** (231k/s vs 5.8k/s), so they go to their own collector, the first thing shed. Clicks ride `/r/`, which is never shed. A follow returns `204` with the new `subs_version`, and the app sends it on its next feed request.

## D4. FR1 via WebSub push

A push is a hint, not a data path. It makes the source due now, and a normal poll does the fetch, the overlap check and the dedup.
```mermaid
%% D4 (FR1, push): subscribe, verify intent, signed delivery, then the same fetch and normalizer path as a poll.
sequenceDiagram
    autonumber
    participant CB as WebSub callback
    participant H as WebSub hub
    participant P as Publisher
    participant S as feed_source
    participant W as Poll worker
    participant K as raw-items
    participant N as Normalizer
    CB->>H: POST hub.mode=subscribe, hub.topic, hub.callback, hub.secret
    H->>CB: GET callback, hub.mode=subscribe, hub.challenge=abc, hub.lease_seconds
    CB->>S: did we ask for this topic? yes, source 77 pending
    CB-->>H: 200, body abc
    Note over CB,H: active. Hub lease ~10 days, we renew at 80 percent of the granted lease
    P->>H: new article published
    H->>CB: POST body, X-Hub-Signature sha256=HMAC of body with hub.secret
    alt signature valid
        CB-->>H: 2xx within a second
        CB->>S: source 77 next_poll_at = now
    else signature missing or wrong
        CB-->>H: 2xx, body ignored, counted as forged
    end
    W->>S: claim due row, SKIP LOCKED, lease 60 s, lease_token + 1
    W->>P: conditional GET latest 25, host token taken
    P-->>W: 200, 25 items, 24 known and unchanged
    W->>K: 1 new item, key publisher_id
    K->>N: same normalizer path, 5 dedup levels
    Note over W,S: polling never stops. Top ~500 every 3 min, the rest every 30 min
    W->>S: a poll finds an item no push delivered, push_missed + 1
    Note over W,S: 2 push_missed in an hour, the source reverts to plain polling at T_fresh
```

- **Why a hint and not the fat-ping body:** the poll re-uses the ETag, `known_ids`, the overlap check and the host budget. Cost: one extra GET per push, at most ~3.5/s. **Why keep polling:** a push that never arrives looks exactly like a quiet publisher. Push buys the top ~500 freshness, and the rest a 30-min poll instead of 15. A forged delivery gets a 2xx and is ignored, which the WebSub spec allows. An unexpected `hub.challenge` gets a 404, so nobody can subscribe us to a feed we did not ask for.

## D5. A feed server dies mid-request

The load balancer retries once on another server. Any server can serve any cursor, because the corpus is everywhere and the session is in Redis.
```mermaid
%% D5: failure path. F1 dies holding one request. Retry on F2, then a replacement bootstraps before it passes readiness.
sequenceDiagram
    autonumber
    participant A as App
    participant LB as Load balancer
    participant F1 as Feed server 1
    participant F2 as Feed server 2
    participant R as Feed sessions
    participant NS as Replacement
    participant O as Object store
    participant K as article-events
    A->>LB: GET feed, cursor session 7, offset 40
    LB->>F1: forward
    Note over F1: t=0 host dies, its 100 ms click buffer is lost
    LB->>LB: connection reset, no bytes sent yet
    LB->>F2: retry once, a GET is safe to repeat
    F2->>R: GETRANGE session 7, 24 ids
    F2-->>A: the same 20 cards F1 would have sent
    Note over LB,F1: t=6 s, 3 failed health checks 2 s apart, F1 ejected
    Note over NS: orchestrator starts a replacement, boot ~20 s
    NS->>O: load this region's latest snapshot + offsets
    O-->>NS: ~1 GB in ~10 s, corpus and lanes in RAM
    NS->>K: assign all 12 partitions, seek to snapshot offsets
    K-->>NS: ~1 min of events in ~5 s, lag under 20 s, repeats skipped by version
    NS->>LB: warm pools ~30 s, readiness passes ~70 s after start
```

- **Data at risk:** one 100 ms click buffer. 5.8k clicks/s over 36 servers is ~160/s each, so ~16 clicks. A retried `/r/` counts once: Flink dedups on (user_id, session_id, article_id) for 10 min. A retried page 1 may leave an orphan 2.6 KB session that expires in 20 min.
- **Why readiness waits for replay:** the settle cut and `as_of_seq` assume every ready server holds everything older than the cut. So readiness fails at 20 s of consumer lag, not just at boot. A corrupt snapshot falls back to the previous one, then to a rebuild from a Postgres replica with `offsetsForTimes`; a snapshot older than 10 min is a ticket.

## D5. Redis session shard lost while a user is on page 3

The session is gone, so the server answers 409 and the app re-sends the story ids it has rendered. The server re-ranks up to `as_of_seq` (the article id at page 1's settle cut, the same set on every ready server), drops those ids and freezes a new session.
```mermaid
%% D5: failure path. The session read fails, 409, the app sends its rendered ids, the server rebuilds the session as of the original cut.
sequenceDiagram
    autonumber
    participant A as App
    participant F as Feed server
    participant R3 as Session shard 3
    participant R5 as Healthy shard 5
    Note over A,F: pages 1 to 3 rendered. Cursor = session 7, offset 60, as_of_seq, bk, HMAC over user_id
    Note over R3,R5: t=0 shard 3 primary lost, replica not promoted yet
    A->>F: GET feed, cursor for page 4
    F->>F: verify HMAC by key id, cursor user_id is the caller
    F->>R3: GETRANGE 24 ids
    Note over F,R3: timeout, or the promoted replica lacks the key
    F-->>A: 409 session gone
    A->>F: POST /v1/feed/resume, cursor + 60 rendered story ids, 480 B
    F->>F: rank candidates up to as_of_seq, ages as of that cut
    F->>F: drop the 60 rendered ids, freeze the next 300
    F->>R5: SET session 9 with user_id, TTL 20 min
    F-->>A: 20 cards, cursor on session 9, offset 20
    Note over A,F: nothing repeats and nothing unseen is skipped. Cost is one extra round trip
```

- **Blast radius:** 1 shard of 6, so ~1/6 of live sessions take one resume each. In a region failover every scroller in that region loses the session at once, and this becomes the main path for one page.
- **Why not "continue below the last score":** it needs no POST, but the deep dive measured ~4 repeats and ~6 skips per loss. **Why ages as of the cut:** with a 6 h half-life every score drops ~2% per 10 minutes, so "now" ages reorder nothing but shift every score.

## D5. The outbox relay publishes the same event twice

The relay crashes after Kafka acked but before it marked the row sent. The duplicate is harmless because feed servers apply an event only if its version is newer.
```mermaid
%% D5: failure path. Duplicate article.upserted after a relay crash. Dedup key (article_id, version) on the consumer.
sequenceDiagram
    autonumber
    participant N as Normalizer
    participant D as Article DB
    participant RL as Outbox relay
    participant K as article-events
    participant F as Feed server
    N->>D: one txn, article 901 title edit, version 2, outbox row 5501
    RL->>D: read unsent outbox rows, gets 5501, article 901 v2
    RL->>K: publish article.upserted 901 v2, acks=all
    K-->>RL: ack, offset 8812
    Note over RL: crash before marking row 5501 sent
    K->>F: 901 v2
    F->>F: holds v1, 2 > 1, apply, card title updated
    Note over RL,K: restart. New producer id, so Kafka idempotence does not span the crash
    RL->>D: read unsent outbox rows, gets 5501 again
    RL->>K: publish 901 v2 again, offset 8840
    RL->>D: mark 5501 sent
    K->>F: 901 v2, the duplicate
    F->>F: holds v2, 2 is not > 2, ignore, lanes untouched
    Note over F,K: a snapshot replay re-delivers old events the same way, and the same rule ignores them
```

- **Without the version check** a duplicate "new article" event would prepend the id to its lanes twice, and the card would show twice. **A relay that stays down** stops the watermark W, so the settle cut stops advancing instead of letting late rows land below served cursors. It pages when the oldest unpublished outbox row passes 60 s. Key and lifetime per hop: [§10.5](solution.md#105-exactly-once-and-idempotency-end-to-end). Concept: [`exactly-once`](../../concepts/exactly-once.md).

## D6. Decision flow for one For You request

Shedding order is `new_count` first, then page-1 builds, which are also rate limited per user. Page-2+ slices and `/r/` are never shed. The Following tab skips this flow: a keyset on `article_id` (one clock) below the settle cut, min(now - 30 s, W), where W is the relay's lowest per-partition watermark.
```mermaid
%% D6: decision flow inside the feed service for GET /v1/feed?tab=for_you. Only a page-1 build can be shed. Every path ends in a page or the CDN fallback.
flowchart TD
    REQ["GET /v1/feed, For You,<br/>subs_version from the app"]:::client -->|"request"| CUR{"Cursor with<br/>session_id?"}:::decision
    CUR -->|"no, page 1"| OV{"CPU over 75% or<br/>200 in flight?"}:::decision
    OV -->|"yes, shed"| TOP["503, Retry-After 30 to 90 s.<br/>App calls /v1/feed/top: CDN,<br/>pre-built object"]:::cache
    OV -->|"no, build"| UCQ{"Cached subs at the<br/>app's subs_version?"}:::decision
    CUR -->|"yes, never shed"| SESQ{"Session<br/>in Redis?"}:::decision
    SESQ -->|"yes"| P300{"Offset past<br/>300?"}:::decision
    P300 -->|"no"| SLICE["GETRANGE slice, hydrate live,<br/>skip retracted and unfollowed,<br/>extend by one"]:::service
    P300 -->|"yes, continuation"| UCQ
    SESQ -->|"no: 409, app POSTs<br/>rendered ids to resume"| UCQ
    UCQ -->|"yes, 1 round trip"| RANK["Rank candidates, freeze 300 ids.<br/>Page 1: new settle cut.<br/>Resume: ages as of the cut,<br/>minus rendered ids.<br/>Continuation: minus served ids"]:::service
    UCQ -->|"missing or older"| STQ{"Consistent KV<br/>read answers?"}:::decision
    STQ -->|"yes, refill cache"| RANK
    STQ -->|"no, down or slow"| DEF["Regional default mix,<br/>not personalized"]:::service
    RANK -->|"SET session, TTL 20 min"| BRK{"Breaking story in this<br/>market not yet shown?"}:::decision
    SLICE -->|"20 cards"| BRK
    DEF -->|"degraded page"| BRK
    BRK -->|"yes, once per session"| PIN["Put it in the breaking field,<br/>mark it shown, keep it<br/>out of the slice"]:::service
    BRK -->|"no"| OUT["20 cards + signed cursor"]:::service
    PIN -->|"pinned banner"| OUT
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- **A slice needs no user state and no ranking** (~0.3 ms of CPU against ~2 ms for page 1), so page 2 onward survives both a user-cache outage and overload, and nobody's scroll is replaced mid-way. Only page 1, a resume and a continuation rank. Unfollow mid-scroll needs no rebuild: the app sends `subs_version` on every request, and a newer one makes hydration drop that publisher's cards. The jittered Retry-After keeps shed clients from returning in the same second. Concept: [`rate-limiting-and-load-shedding`](../../concepts/rate-limiting-and-load-shedding.md).
- **"Shown" lives in the signed cursor** (the pagination deep dive calls the field `bk`). The lane holds at most 3 stories per market, so the cursor stays small and a slice needs no Redis write.

## D8. Publisher circuit (`feed_source.circuit`)

One circuit per publisher. A failure is a 10 s timeout or a 5xx. A 429 never counts: it releases the row until Retry-After expires and halves the host rate (AIMD). Open means no polls and no worker time, with backoff 1, 2, 4 ... 30 min and 20% jitter.
```mermaid
%% D8: feed_source.circuit. Thresholds as in solution 5.1 and 10.2.
stateDiagram-v2
    direction LR
    [*] --> closed
    closed --> closed: ok, 429, or fails 1 to 4
    closed --> open: 5th straight failure
    open --> half_open: backoff expires
    half_open --> closed: probe succeeds
    half_open --> open: probe fails, backoff x2
```

## D8. Story lifecycle

A story is a cluster of articles and the unit of a card. Machines make candidates (counting tier 1 and 2 publishers only). Only an editor makes "Breaking", as a `story_breaking` row per editorial market (~50), so one story can be Breaking in India and Growing in the US. `merged_into` points at the survivor, and a label follows it.
```mermaid
%% D8: STORY, with the breaking states per (story, market). Breaking ends at story_breaking.breaking_until (default 2 h) or cleared_at.
stateDiagram-v2
    direction LR
    [*] --> New: first article or split
    New --> Growing: 2nd publisher joins
    Growing --> Growing: copy attaches
    Growing --> Candidate: +20 pubs/15 min or z-score
    Candidate --> Breaking: editor confirms, market
    Candidate --> Growing: editor declines
    Breaking --> Growing: breaking_until or cleared
    Breaking --> Merged: editor merge, label moves
    New --> Merged: clusters merge
    Growing --> Merged: clusters merge
    New --> Expired: 72 h old
    Growing --> Expired: newest member 72 h
    Growing --> Retracted: all members retracted
    Merged --> [*]
    Expired --> [*]
    Retracted --> [*]
```

## D8. Article lifecycle

An edit, or a same-publisher re-post within SimHash 3 (an alias, recorded in `article_alias`), changes the card in place and never re-surfaces it. `article_id` and `ingested_at` never change.
```mermaid
%% D8: ARTICLE.status and version. Every transition emits article.upserted with version + 1.
stateDiagram-v2
    direction LR
    [*] --> Live: first upsert
    state "live" as Live {
        direction LR
        [*] --> V1
        V1: version 1
        VN: version n, edited
        V1 --> VN: content_hash changed
        VN --> VN: edit or alias, v + 1
    }
    Live --> Retracted: retraction, version + 1
    Retracted --> [*]
```

- **Retraction signals:** a deleted flag in the publisher's API, a 404 or 410 on the HEAD recheck of the last 24 h of top-500 articles (~2/s), or an editor or legal takedown. Absence from the latest 25 is never one.
- **Edges of "live":** an item whose `published_at` is over 48 h old at first sight is stored but kept out of fresh lanes. After 72 h an article leaves every corpus: Following shows "end of feed", and `/r/` still reads the Postgres replica.

## D9. Deployment / topology

Serving is active-active in 3 regions. Ingest runs in region A with a warm standby in B, because a second active fetcher fleet would double our requests to every publisher.
```mermaid
%% D9: where each component runs, what crosses a region boundary, replication per store. Red: the fetcher, the only thing that talks to publishers.
flowchart LR
    U["Users, GeoDNS<br/>to nearest region"]:::client
    PUB["Publishers ~10k"]:::external
    CDN["CDN edges, global<br/>thumbnails + pre-built top feed"]:::cache
    SUB[("Subscription KV<br/>3 regions, async, LWW per row")]:::store
    subgraph RA["Region A, ingest active + serving"]
        FETA["Fetchers + normalizer<br/>3 workers, active"]:::critical
        PGA[("Postgres primary<br/>+ sync replica, 2 AZs")]:::store
        KA[["Kafka RF 3, min ISR 2<br/>raw-items, article-events"]]:::queue
        FA["Feed servers 12, 20 at spike<br/>+ Redis sessions, user cache<br/>+ snapshotter"]:::service
    end
    subgraph RB["Region B, warm standby ingest + serving"]
        FETB["Fetchers + normalizer<br/>warm standby, not polling"]:::service
        PGB[("Postgres async replica")]:::store
        KB[["article-events mirror<br/>RF 3"]]:::queue
        FB["Feed servers 12, 20 at spike<br/>+ Redis + snapshotter"]:::service
    end
    subgraph RC["Region C, serving"]
        KC[["article-events mirror<br/>RF 3"]]:::queue
        FC["Feed servers 12, 20 at spike<br/>+ Redis + snapshotter"]:::service
    end
    FETA -->|"polls ~13/s,<br/>one region only"| PUB
    FETA -->|"upsert + outbox,<br/>sync commit to 2 AZs"| PGA
    PGA -->|"outbox relay"| KA
    PGA -.->|"async WAL,<br/>seconds behind"| PGB
    KA -->|"MirrorMaker 2,<br/>article-events ~5 KB/s"| KB & KC
    KA -->|"every server,<br/>manual assignment"| FA
    KB -->|"every server"| FB
    KC -->|"every server"| FC
    KB -.->|"failover step 1, replay<br/>mirrored events"| PGB
    FETB -.->|"step 2, promote,<br/>claim rows, poll"| PGB
    U -->|"feed, /r/ clicks"| FA & FB & FC
    FA & FB & FC -->|"subs on cache miss"| SUB
    CDN -->|"thumbnails, top feed"| U
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Crosses a region boundary:** `article-events` (~5 events/s x ~1 KB), Postgres WAL to B, subscription KV replication, and users moved by DNS. **Never crosses:** `raw-items`, sessions, user cache, clicks. Each region runs its own clicks topic and Flink, since trending is per region anyway.
- **Replication:** Kafka RF 3 per cluster, `min.insync.replicas=2`. Postgres 3 copies (primary and sync replica across AZs in A, async in B). Redis 1 replica per shard. Each region runs its own snapshotter, because a mirrored topic's offsets differ from the source cluster's.
- **Capacity:** 12 servers per region, ~36k/s at the 75% shed line, ~48k/s flat out. A one-region spike (12k/s to 96k/s) sheds ~60% there unless it spills to the other regions (~48k/s spare, ~70 ms away). Losing a region leaves 24 servers, ~48k/s at 50% CPU, above the 35k/s daily peak.
- **Region A lost:** B replays the mirrored `article-events` into its Postgres first, so re-polled items dedup against rows that exist instead of getting new ids. Then its fetchers start. ~5 to 10 min, which breaches the 5-min top-500 target: a freshness incident. Users moved from a lost serving region arrive with a cold user cache and no session, so each takes one resume (D5). A request whose `subs_version` is ahead of the local KV replica reads from the user's home region. Concept: [`replication-and-quorums`](../../concepts/replication-and-quorums.md).

## D10. Scaling / partitioning

The corpus is replicated, not partitioned. Everything per-user is partitioned by user. The one hot partition is harmless at our write rate.
```mermaid
%% D10: what is partitioned, by which key, and what is replicated. Red: the raw-items partition holding a wire service in a breaking-news burst.
flowchart LR
    FET["Fetcher, key publisher_id"]:::service -->|"hash mod 12,<br/>~833 publishers each"| PX[["raw-items partitions<br/>~3/s each at peak"]]:::queue
    FET -->|"wire in a burst,<br/>5 items/min"| P7[["partition 7, hot<br/>wire + its neighbours"]]:::critical
    PX -->|"6 partitions each"| NORM["Normalizer x 2<br/>same-publisher alias check,<br/>then 1 clusterer: cross-<br/>publisher SimHash + clustering"]:::service
    P7 -->|"per-publisher order"| NORM
    NORM -->|"article-events, same key,<br/>12 partitions, manual assignment"| FS["Every feed server<br/>whole 72 h corpus ~0.9 GB<br/>replicated, not partitioned"]:::service
    FS -->|"10x: 9 M cards,<br/>~9 GB per server"| SEAM{"Seam: split corpus<br/>by language or region"}:::decision
    REQ["Feed request"]:::client -->|"any server,<br/>no affinity"| FS
    FS -->|"session:id, 16,384 slots"| SES[("Sessions, 6 shards<br/>~18 GB each at spike")]:::cache
    FS -->|"user:id hash slot"| UC[("User cache, 6 shards<br/>~17 GB, ~20k reads/s each")]:::cache
    UC -->|"miss, partition user_id"| KV[("Subscription KV<br/>~5 B rows, ~200 GB")]:::store
    FS -->|"key user_id"| CK[["clicks, 48 partitions<br/>~2.9 MB/s each at spike"]]:::queue
    CK -->|"keyBy story_id,<br/>pre-aggregated"| FL["Flink velocity"]:::service
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Why the hot partition is fine.** A wire in a burst adds 5 items/min, 0.08/s. Even the whole ~35/s peak on one partition is 35 x 2 KB = 70 KB/s, under 1% of the ~10 MB/s one partition handles ([§10.3](solution.md#103-capacity-math-per-component)). It would load the consumer instead. The same-publisher alias check is complete per partition, because one publisher's items share a partition. Cross-publisher SimHash (~2 ms) and clustering (~20 ms) run in one active clusterer with a hot standby whatever the partitioning, ~0.8 core at 35/s. Its story writes carry the leader-lease epoch, checked in Postgres, so a deposed leader cannot write. If the normalizer side bites, process different publishers of one partition in parallel. Per-publisher order holds, and more partitions would not split one hot key anyway.
- **Redis per shard:** sessions 110 GB / 6 = ~18 GB against ~25 GB. User cache 100 GB / 6 = ~17 GB and 120k / 6 = 20k reads/s against ~100k ops/s. **Clicks keyed by user_id, not story_id.** A breaking story draws a large share of all clicks, and keying by story would put them all on one partition. User keying also keeps the (user_id, session_id, article_id) dedup on one partition. Flink pre-aggregates per story before the keyBy.
- **The 10x seam:** 3 M articles a day x 3 days = 9 M cards, ~9 GB per server. Split the corpus by language, one server group per language set, and route a user to the group for their 1 or 2 languages. Every request stays in memory. Dedup hits its limit earlier: brute-force compares grow with the square of scale (2.1 M x 35/s = ~7.4 x 10^7/s today, ~10^9/s for one thread), so Manku's permuted tables arrive at ~4x, before the corpus split. Concept: [`sharding`](../../concepts/sharding.md), [`fan-out-fan-in`](../../concepts/fan-out-fan-in.md).

## D11. Failure mode map

Component on the first edge, what fails in the box, blast radius on the second edge, mitigation in the last box. Matches [§5.7](solution.md#57-what-happens-when-a-component-dies-and-what-changes-at-10x).
```mermaid
%% D11: one tree. Component, what fails, blast radius, mitigation. Red: the fetcher at the publisher boundary.
flowchart TD
    ROOT["News aggregator"]:::service
    ROOT -->|"fetcher, one publisher"| F1["Down, slow, 429,<br/>format change"]:::critical -->|"blast: that publisher's freshness"| M1["Circuit, AIMD, release on 429,<br/>gap_suspected, ticket,<br/>page if top 20"]:::service
    ROOT -->|"poll worker"| F2["Crash mid-poll"]:::decision -->|"blast: ~20 sources, up to 60 s"| M2["Lease expires, lease_token fences<br/>the old worker, upsert dedups<br/>resends, page-back resumes"]:::service
    ROOT -->|"Postgres primary"| F3["Down"]:::decision -->|"blast: polls and ingest pause<br/>~30 s, reads unaffected"| M3["Sync replica promoted ~30 s,<br/>raw-items drains, overdue first,<br/>zero-overlap check"]:::service
    ROOT -->|"Kafka"| F4["Broker lost"]:::decision -->|"blast: none, RF 3,<br/>min ISR 2"| M4["Leader moves. Full outage,<br/>known_ids not advanced"]:::service
    ROOT -->|"feed tier"| F5["A server crashes,<br/>or the tier overloads"]:::decision -->|"blast: in-flight requests,<br/>~16 clicks, page-1 builds"| M5["LB retries once, replacement<br/>~70 s, shed page 1 to the<br/>pre-built CDN top feed"]:::service
    ROOT -->|"Redis"| F6["Session or user-cache<br/>shard lost"]:::decision -->|"blast: scroll glitch<br/>or no personalization"| M6["409, app re-sends rendered ids,<br/>re-rank as of the cut.<br/>KV read by subs_version,<br/>else regional default mix"]:::service
    ROOT -->|"region"| F7["Lost"]:::decision -->|"blast: its users until DNS moves,<br/>top-500 freshness 5 to 10 min if A"| M7["Active-active serving. B replays<br/>the mirror into Postgres,<br/>then its fetchers start"]:::service
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
```

- **Not in the tree, largest blast radius:** a bad ranking or clustering release touches every feed at once, so both ship behind a 1% holdout with CTR and "distinct stories per page" guardrails ([§8](solution.md#8-staff-level-notes)). Postgres promotion is timed in [§10.4](solution.md#104-failure-timeline).

## D12. Rollout / migration

The five steps of [§8](solution.md#8-staff-level-notes) migration, from cron + SQL + offset pagination. Durations are assumptions. Every phase ends with a flag-flip rollback, and nothing is destructive until the SQL path is removed.
```mermaid
%% D12: migration from cron + SQL feed to leased pollers and the replicated corpus. A rollback point closes each phase.
gantt
    title Migration to leased polling, article-events and the in-memory feed
    dateFormat YYYY-MM-DD
    axisFormat %b %Y
    section 1 Leased poll workers
    Tee the old cron responses into feed_source and raw-items :p1, 2026-10-01, 21d
    Compare item counts per publisher for a week             :p1b, after p1, 7d
    Switch which side polls, leased workers now poll         :p1c, after p1b, 3d
    Rollback = the cron polls again                          :milestone, r1, after p1c, 0d
    section 2 Events and corpus
    Outbox, article-events, corpus in a new feed service     :p2, after p1c, 28d
    Serve 1 percent, diff Following item sets against SQL    :p2b, after p2, 14d
    Rollback = route reads back to SQL                       :milestone, r2, after p2b, 0d
    section 3 Ramp reads
    Ramp to 100 percent, SQL fallback behind a flag          :p3, after p2b, 21d
    Rollback = flag to SQL, still kept in sync               :milestone, r3, after p3, 0d
    section 4 Pagination switch
    Keyset cursors, an old offset cursor restarts at the top :p4, after p3, 14d
    Rollback = flag back to offset pagination                :milestone, r4, after p4, 0d
    section 5 Ranked For You
    Ranking and feed sessions behind an experiment           :p5, after p4, 28d
    Rollback = turn the experiment off                       :milestone, r5, after p5, 0d
    Soak with the SQL path idle                              :p6, after p5, 30d
    Remove the SQL path, the one step with no rollback       :milestone, rm, after p6, 0d
```

- **Phase 1 tees, it never double-polls:** polling from both sides would double our request rate against every publisher's limit. **Phase 2 diffs sets, not order,** because the old feed sorts by `published_at` and the new one by `article_id`, our ingest clock. For You has no old equivalent to diff.

## Trade-offs these diagrams make visible

| Decision | Chose | Gave up |
|---|---|---|
| Corpus placement (D10) | Replicated to every server | ~70 s to bring a server up (D5), and a 10x seam |
| Ingest regions (D9) | One active region, warm standby | Minutes of ingest pause on region loss |
| Session loss (D5) | 409, then the app re-sends its rendered ids | One extra round trip and a POST of at most ~4.8 KB (last 600 ids) |
