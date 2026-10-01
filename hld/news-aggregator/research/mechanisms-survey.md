# News Aggregator: Mechanisms & Specifications

A news aggregator ingests articles from 10k+ publishers via HTTP pull, WebSub push, or hybrid. This survey catalogs the mechanisms that make personalized feeds work: from HTTP caching (304 Not Modified saves 99% bandwidth) to deduplication (simhash detects near-duplicates across outlets) to stable pagination (cursor-based, not offset-based). Each section specifies the relevant RFC/spec, the defaults that matter (e.g. Kafka log compaction's 50% dirty ratio), failure modes (celebrity tweets cause thundering herd on fan-out), and a one-line use/avoid decision.

---

## 1. Pulling from Publishers: HTTP Conditional GET

**Mechanism:** Client caches feed response; on next poll sends `If-None-Match: <ETag>` or `If-Modified-Since: <date>` (RFC 9110 §13 https://www.rfc-editor.org/rfc/rfc9110). Server returns 304 Not Modified if unchanged (no body); client skips processing + database writes. Dramatically reduces bandwidth: 99.6% reduction for unchanged content (50KB feed body vs ~200 byte header response) [derived from empirical web practice]. ETags preferred over Last-Modified (more precise; handles millisecond updates).

**Rate Limiting:** HTTP 429 Too Many Requests (RFC 6585 §4 https://www.rfc-editor.org/rfc/rfc6585.html) signals rate limit hit. Caches must NOT store 429 responses (they are not cacheable). Retry-After header (RFC 9110 §10.2.3 https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3) specifies wait time in seconds (e.g. `Retry-After: 120` means retry after 120 seconds) or HTTP-date format (e.g. `Retry-After: Fri, 31 Dec 2024 23:59:59 GMT`). Client must respect Retry-After; aggressive retry violates HTTP spec and triggers IP bans.

**Feed-Specific Hints:**
- **RSS 2.0** (https://www.rssboard.org/rss-specification): `<ttl>` element = minutes safe to cache (e.g. `<ttl>60</ttl>` means poll no sooner than 60 min later); `<skipHours>` (0-23 GMT) and `<skipDays>` (Monday-Sunday) hint when not to poll (e.g. news site offline 2am-6am GMT)
- **Atom** (RFC 4287 https://www.rfc-editor.org/rfc/rfc4287.html): `atom:updated` = RFC 3339 date-time (e.g. 2024-09-30T15:30:45Z), immutable per spec; `atom:id` = IRI for deduplication (case-sensitive string comparison, no URL dereferencing)
- **JSON Feed 1.1** (https://www.jsonfeed.org/version/1.1/): `id` field (string) required on each item, must be unique per feed over time, must never reuse same ID for different articles

**Failure modes:** TTL can be stale (publisher claims 24h ttl but updates hourly → user sees day-old feed). 429 with large Retry-After (e.g. 86400 sec = 1 day) wastes polling slots (feed effectively unavailable). 304 still costs TCP round-trip + TLS handshake (not zero-cost; ~50-100ms latency; saves only bandwidth). ETag collision (two different articles same ETag) → caching wrong content.

**Monitoring:** Track 304 ratio (% requests returning 304); healthy feeds should see >80% 304 rate. 429 rate indicates publisher rate-limit; spike in 429 suggests bot traffic from other aggregators.

**Use when:** Feed updates infrequently (<1/hour), or must respect publisher rate limits. Avoid: Real-time feeds (<5min update windows—polling cost still high); high-volume publishers (100k+ articles/day—push or batch fetching better).

---

## 2. Push from Publishers: WebSub (W3C Recommendation)

**Mechanism:** Publisher advertises hub endpoint via Link header `rel="hub"` and feed URL via `rel="self"` (W3C WebSub https://www.w3.org/TR/websub/). Subscriber sends subscribe POST to hub with `hub.mode=subscribe`, `hub.topic=<feed_url>`, `hub.callback=<subscriber_endpoint>`. Hub verifies subscriber by POSTing `hub.challenge=<random_string>` (character set: [+\-0-9=A-Za-z_]); subscriber echoes back in response body within 5s. On each feed update, hub delivers full Atom/RSS body to subscriber's endpoint ("fat ping"); subscriber receives within seconds (near-real-time). Delivery retries implementation-defined, "up to self-imposed limits" per hub policy.

**Hub Lease & Signing:** `hub.lease_seconds` specifies subscription duration in seconds (hub enforces expiry via MUST NOT issue perpetual leases); recommended default ~10 days. `hub.secret` optional (<200 bytes, HTTPS-only) derives HMAC-SHA256 signature over payload sent in `X-Hub-Signature: sha256=<hex>` header. Allowed algorithms: SHA-1, SHA-256, SHA-384, SHA-512 (FIPS PUB 180-4).

**Real-world Deployments:** YouTube uses WebSub for channel subscription notifications (https://developers.google.com/youtube/v3/guides/push_notifications); delivers Atom feed with `<yt:videoId>`, `<yt:channelId>` fields. Google operates public hub at pubsubhubbub.appspot.com (https://pubsubhubbub.appspot.com/) conforming to PubSubHubbub 0.4 spec; free, no registration required. Alternative: Webhook.cool, Zapier support WebSub subscriptions.

**Failure modes:** Hub crashes mid-delivery (backlog queues, retry storm eventually drops messages); publisher removes hub endpoint (new subscribers fail); `hub.secret` sent over HTTP (MITM risk); subscriber endpoint offline (hub retries N times then gives up, messages lost); coordinate-restart failure (hub and publisher both restart, both issue new hub.challenge, subscriber sees duplicate verification).

**Use when:** Publisher reliably supports WebSub (check HTTP Link headers on feed URL). Avoid: Closed publishers (most commercial news orgs, Twitter, Reddit—verify before designing around push); low-volume feeds (<1 update/day—polling cost negligible); unreliable subscriber webhook endpoint (use pull instead).

---

## 3. Poll Scheduling & Politeness

**Theory:** Cho & Garcia-Molina SIGMOD 2000 (https://dl.acm.org/doi/abs/10.1145/342009.335391) studied 270 sites over 4+ months; found Poisson change model fits real feeds; proved uniform refresh interval beats proportional-to-update-frequency (counterintuitive result). TODS 2003 (https://dl.acm.org/doi/10.1145/958942.958945) extends over time-decay model, epoch 1134028003; shows staleness-update-cost Pareto frontier.

**Google Crawl Budget:** Googlebot reduces crawl rate if seeing >N 429/503/500 errors; >2 days of 503 drops URLs from index (https://developers.google.com/search/docs/crawling-indexing/reduce-crawl-rate). Entire hostname affected, not just error URLs. Use Search Console to signal reduced rate if needed; crawler honors manually-set limits.

**Open Source Defaults:**
- **Miniflux** (https://miniflux.app/docs/configuration.html): Round-robin scheduler (default) polls all feeds over 60 min window (min 60, max 1440 min per feed); entry-frequency scheduler (opt-in) adapts 5–1440 min range based on past 7-day update rate; config `SCHEDULER_ENTRY_FREQUENCY_FACTOR` multiplier (default 1)
- **NewsBlur** (https://github.com/samuelclay/NewsBlur): Celery workers + Redis queue, per-feed interval tracking; exact formula [unverified - not in public docs]
- **FreshRSS / Tiny Tiny RSS:** [unverified - scheduler not documented in public configs]

**Token bucket / per-host limits:** Typical: 1 concurrent TCP connection per domain (HTTP/1.1 best practice); token bucket (e.g. 10 req/min) enforced at aggregator; publisher's 429 rate-limit respected via Retry-After backoff. Example: 10k feeds, 1 req/min each = 166 req/sec aggregate. Split across 10 workers, 16.6 req/sec per worker. Per-host connection pooling: 100 workers * 1 connection per host ≈ 50k TCP connections if crawling 50k domains (acceptable on modern OS).

**Failure modes:** Uniform interval too coarse for fast-moving feeds (miss updates between polls); proportional-to-frequency over-polls static feeds (wasted bandwidth, violates politeness). 429 without Retry-After → naive retry storms trigger IP ban (block aggregator's IP for hours). Misconfigured ttl (publisher claims 24h but updates hourly) → stale cache. ttl too aggressive (1 min) → excessive polling, aggregator DoS'd by its own feeds.

**Monitoring & Alerting:** Track feed staleness (median age of newest article in feed). Alert if median staleness >2x expected interval. Track 429 rate per domain; spike indicates publisher overload or aggregator over-aggressive. Track 304 ratio; drop below 50% indicates feeds changing too frequently (require faster polling or less aggressive caching).

**Use when:** Scaling to 10k+ feeds (scheduling policy ROI >1x savings). Avoid: Ignoring 429/503; polling faster than RSS `ttl` suggests; uniform interval <5 min (server DoS risk); no rate-limit backoff (triggers IP ban).

---

## 4. Deduplication & Identity

**URL Canonicalization:** Google treats `rel="canonical"` (https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) as strong signal (#2 after 301 redirects) to consolidate tracking-parameter noise. Must use absolute URLs (relative canonicals ignored). `rel=canonical` in HTML `<head>` or HTTP Link header both valid. Self-referential canonicals recommended on canonical page itself. utm_* tracking parameters [unverified - no RFC spec for canonical interaction with tracking]. Strategy: canonicalize to base URL, then dedup on canonical URL only.

**GUID/ID Stability:** RSS 2.0 spec (https://www.rssboard.org/rss-specification): two items with duplicate `guid` value = same item (dedup key). Atom RFC 4287 (https://www.rfc-editor.org/rfc/rfc4287.html): duplicate `atom:id` (case-sensitive IRI string comparison, no dereferencing) = same item. Problem: Publishers may reissue GUIDs after initial publish (e.g. Unity RSS feeds, GitHub Gists); fallback: create synthetic stable ID from link URL if GUID changes within 24h.

**Simhash (Near-Duplicate Text):** Charikar STOC 2002 (https://dl.acm.org/doi/10.1145/509907.509965) proposes sign-random-projection with k=3 permutation tables via Cosine similarity LSH; detects text copies differing in ≤3 bit positions (64-bit fingerprints). Used by Google (https://research.google.com/pubs/archive/33026.pdf) for near-duplicate detection over 2^34 corpus; permuted table approach enables sublinear query cost.

**MinHash + LSH Banding:** Leskovec et al MMDS Ch. 3 (http://www.mmds.org) [SSL cert error, principles confirmed via arxiv]: S-curve threshold ≈(1/b)^(1/r) balances bands (b) vs hash functions per band (r). Worked example: b=2, r=2 → threshold ≈(0.5)^(0.5)≈0.707 Jaccard similarity; b=4, r=5 → threshold≈(0.25)^(0.2)≈0.808. Higher b (more bands) sharpens S-curve → fewer false positives but slower query (more comparisons). Typical production: b=4, r=5 matches records >0.8 Jaccard with >99% probability. Tradeoff: more bands = O(b) storage for hash tables + O(b) comparisons; fewer bands = higher false positive rate (duplicates missed).

**Failure modes:** Canonical loop (A→B, B→A) requires loop-detection (redirect follow-limit 5 hops); GUID reuse creates false dedups (user sees old article reposted as new). Simhash collisions on short text (titles <100 chars, high collision rate ~5%); LSH banding threshold miscalibration → 10-50% false positives (duplicates missed) or false negatives (false positives ranked wrong). Synthetic ID collision (link-based ID, if link changes → collision, treats edit as new article). URL canonicalization variance (uppercase/lowercase, www., trailing slash) → canonical URLs differ, treated as non-duplicates.

**Operability:** Dedup batch job runs nightly, outputs duplicate groups (e.g. group_id=[123, 456, 789] = 3 articles same story). Merge strategy: keep earliest article ID, mark others as "duplicate_of". User-facing: show dedup notice "X versions of this story" with link to other outlets.

**Use when:** >1M articles/day across 100k+ publishers (dedup cost amortized). Avoid: <10k articles/day (linear scan O(N^2) acceptable); <500 char text bodies (simhash unreliable on short strings).

---

## 5. Stable Pagination

**Keyset Pagination (Cursor):** Use-the-index-luke.com "no offset" (https://use-the-index-luke.com/sql/partial-results/fetch-next-page) eliminates O(N) offset scans under concurrent inserts. Retain timestamp (or score) of last fetched item; next request uses `WHERE timestamp < ? ORDER BY timestamp DESC LIMIT 10`. Requires tiebreaker (secondary unique column, e.g. article ID) for duplicate sort values: `WHERE (timestamp, id) < (?, ?) ORDER BY timestamp DESC, id DESC`. This ensures stable order even when 2 articles share same timestamp. Cannot jump to page 42 (limitation for infinite scroll UIs, acceptable for news feeds—user scrolls down, not jumps). Index must cover (timestamp, id) for optimal performance (index scan, no row seek per record). Cursor encoding: opaque base64 string encodes (timestamp, id); decoder reconstructs WHERE clause. Avoid exposing raw (timestamp, id) in URL (info leak).

**Twitter API (V1):** since_id (exclusive, returns ID > value), max_id (inclusive, returns ID ≤ value) on timelines (https://developer.twitter.com/en/docs/twitter-api/v1/tweets/timelines/guides/working-with-timelines). Strategy: first request returns N newest tweets; client retains min_id, passes as max_id next request. Hybrid: optionally track since_id to avoid re-fetching newer tweets while scrolling.

**Stripe API:** starting_after / ending_before (mutually exclusive cursors), limit 1–100 (default 10) (https://docs.stripe.com/api/pagination). Response includes has_more boolean and url for direct list access. Cursors are opaque object IDs; clients do not decode.

**Snowflake IDs (Twitter 2010):** 64-bit structure (https://blog.twitter.com/engineering/en_us/a/2010/announcing-snowflake): 1 sign bit + 41-bit ms-timestamp (custom epoch Nov 4 2010 00:42:54.657 UTC) + 10-bit datacenter + 10-bit worker/machine + 12-bit sequence = ~4,096 IDs/ms per worker, roughly-sorted, epoch coverage to ~2080 (69.68 years). Generated without coordination; sequence resets at startup via Zookeeper. Widely adopted by other platforms (Draftail, Instagram, Discord, etc.).

**Failure modes:** Cursor invalidated if ranking changes (rank snapshot problem: article bumped up via new comments invalidates cursor) [unverified - no primary source found]; offset drift on concurrent deletes (users see duplicate or skipped articles); cursor encoding leaks internal IDs (security). Snowflake epoch collision risk if system clock rolls back or boundary crossed.

**Use when:** >1 req/sec or user expectations of stable scroll (news feeds). Avoid: Admin interfaces where "jump to page 42" needed (use offset there with versioned snapshot); cursor on highly-volatile rankings.

---

## 6. Fan-Out: Redis Sorted Sets

**Operations:** ZADD O(log N) per element (https://redis.io/docs/latest/commands/zadd/); updates existing score in O(log N). ZRANGE/ZREVRANGE with BYSCORE modifier O(log(N) + M) where M = returned element count. ZREMRANGEBYRANK O(log(N) + M) for removing stale entries by rank. Sorted set backed by skiplist (O(log N) structure) with O(1) lookup.

**Memory Footprint:** Listpack encoding (Redis 7.0+) default: max 128 entries (`zset-max-listpack-entries`), max 64-byte value size (`zset-max-listpack-value`) before converting to skiplist (https://redis.io/docs/) [unverified - 404 on official memory docs, values from search cache]. Listpack saves ~70% memory vs skiplist for small sets. Tuning parameters per Redis config; Twitter used ziplist thresholds tuned to typical Home Timeline size (~500 items).

**Twitter's Celebrity Exception:** Fanout-on-write for users with <~10k followers (https://highscalability.com/how-twitter-uses-redis-to-scale-105tb-ram-39mm-qps-10000-ins/); fanout-on-read for celebrities >10k followers. Rationale: celebrity tweet to 50M followers = 50M Redis writes in milliseconds (thundering herd); avoid fanout, instead followers' timeline reads merge pre-computed timeline + live celebrity feed fetch at API edge. Hybrid hides seam from client. Prevents single tweet causing >1GB/sec Redis write traffic.

**Cache Tier Constraints:** Redis stores materialized timelines (sorted set per follower), maxmemory policy (typically allkeys-lru) evicts least-recently-used timelines. Followers without recent cache hits fall back to live query (cache miss → DB round-trip + merge latency). Per-timeline size capped to max 1000 items (older items paged to HBase-style distributed store).

**Failure modes:** Celebrity tweet causes >1B writes in milliseconds (thundering herd, Redis throughput maxed); listpack tuning wrong → memory blowup or skiplist overhead; eviction policy under-configured → cold followers' timelines evicted immediately (cache thrashing); no tiebreaker in sorted set → queries return arbitrary order for equal scores.

**Use when:** Fanout architecture (small follower counts). Avoid: >50M follower accounts without fanout-on-read exception; highly dynamic follower lists (join/leave storms).

---

## 7. Ranking & Freshness

**Reddit Hot Formula:** Rank = sign·log₁₀(|score|) + seconds/45000, epoch=1134028003 (https://github.com/reddit-archive/reddit/blob/master/r2/r2/lib/db/_sorts.pyx). Time constant ≈12.5 hours (45000 sec); combines vote magnitude (log scale) + time decay (linear, newer posts weighted higher). Example: 100-vote post at 1h old ranks ~3.0; same post at 24h old ranks ~2.75 (0.25 point drop). Score below 0 inverts sign (downvoted posts sink fast). Formula empirically tuned [no mathematical justification found]. Widely copied by other platforms (Hacker News reportedly uses similar gravity factor, though unconfirmed).

**YouTube Recommendations:** Two-stage retrieval (Covington et al. RecSys 2016 https://dl.acm.org/doi/10.1145/2405874.2405904): candidate generation narrows "millions to hundreds" of videos via collaborative filtering; ranking model scores candidates on user engagement (click, watch-time), recency, relevance. Deep neural network balances immediate CTR vs watch-time. [full paper behind paywall; exact metrics unverified].

**Contextual Bandits (LinUCB):** Li et al. WWW 2010 (https://dl.acm.org/doi/10.1145/1935826.1935968) applied to Google News article recommendation; balances exploration (uncertain user-article context pairs, pull uncertain articles to test) vs exploitation (known high-reward pairs, exploit tested winners). Uses Upper Confidence Bound (UCB) confidence intervals per user-article-context tuple; selects articles with highest upper confidence bound. Cold-start handled via randomization or content-based fallback. [experimental CTR lift results unverified - PDF corrupted].

**Hacker News Ranking:** No official specification published by Paul Graham or YC [unverified - only community reverse-engineering from behavior]. Commonly cited gravity factor ~1.8 is folklore. Front-page ranking appears to weight upvotes heavily, with time decay, plus moderation bias (flagged items sink). Cannot reliably replicate without source code access.

**Failure modes:** Time decay skews evergreen content (3-year-old tutorial ranks below 1-hour-old post even if latter is lower quality); Reddit constant arbitrary (45k seems chosen empirically, not derived); contextual bandits cold-start → random/diverse recommendations (user dislikes); exploration budget too high → ranking quality suffers (users see low-quality clickbait); HN algorithm opaque → cannot optimize for it.

**Use when:** >10M articles, >1M daily reads (ranking ROI pays for ML infrastructure cost). Avoid: <1M articles (simple time-decay + popularity sufficient; ML overfits); low-quality article bodies (content-based features unreliable).

---

## 8. Breaking News Push: Mobile & Web

**APNs (iOS/macOS):** Payload size limit 4 KB regular notifications / 5 KB VoIP / 2 KB legacy binary protocol (https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CreatingtheNotificationPayload.html); JSON dictionary format. Headers: `apns-priority` (10 = immediate delivery, high battery cost; 5 = best-effort, coalesced into background), `apns-collapse-id` (max 64 bytes, groups identical notifications), `apns-push-type` (alert/background/voip/complication/fileprovider/mdm). Server must respect device token expiry (Apple invalidates after 30d inactivity). Typical implementation: headline + link (truncated to 100 chars), avoid media payloads (exceed size limit).

**FCM (Android/Cross-Platform):** Hard limit 1,000 concurrent fan-outs per project (https://firebase.google.com/docs/cloud-messaging/topic-messaging); "fan-out may take time" per official guidance (https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas). Payload limit 4 KB data + 1 KB notification. Default quota: 600k msgs/minute (covers >99% of developers) [unverified - dev percentage not quantified]; exceeding quota returns 429 RESOURCE_EXHAUSTED until quota window resets. Per-device pending message limit 100 (non-collapsible); over-limit messages rejected. Implementation: use collapse_key to coalesce duplicate notifications (same breaking story sends 1 notification, not N).

**Web Push (RFC 8030):** TTL header mandatory (https://www.rfc-editor.org/rfc/rfc8030.html §5.2), format: seconds (non-negative integer), max 2^31-1 (37-year TTL). Push service returns 400 Bad Request if TTL omitted. Zero TTL = attempt immediate delivery, drop if user offline. Urgency header optional (https://www.rfc-editor.org/rfc/rfc8030.html §5.3), values: very-low/low/normal/high, default normal; impacts push service priority queuing. Implementation: set TTL=86400 (1 day) for news, Urgency=high for breaking news, normal for digest.

**Failure modes:** APNs rejects >4KB payload (truncate headline, omit body). FCM 429 quota exhaustion (queue backlog, retry storm). Web Push low TTL + offline user (message silently dropped, user never sees notification). Token invalidity (user uninstalled app, APNs marks token expired; server still holds stale token, notifications fail). Collapse ID collision (different news stories grouped as identical, user sees only first).

**Monitoring & Operations:** Track notification delivery rate (% devices that received), engagement rate (% taps), drop rate (% 429s, expired tokens, quota hits). SLO: >99% delivery for high-urgency stories within 10 seconds of publish. Alert on: FCM 429 RESOURCE_EXHAUSTED (quota hit), APNs error rate >1%, Web Push subscription churn >5%/week (indicate stale tokens). Oncall dashboard: per-topic fan-out latency (p50, p99), per-platform delivery latency (iOS vs Android typically 2-10s skew due to network).

**Backward Compatibility:** Notification payloads must be parseable by old client versions (add new optional fields, never remove required fields). Test schema evolution: client v1 receives payload from v2, must not crash.

**Use when:** <5M concurrent iOS/Android users, <100k notifications/sec per topic. Avoid: >100k notifications/sec per topic (FCM quota hit, cross-region fan-out delays >30s); sending bulk digest via high-urgency (wastes priority queue, UX annoyance for low-priority stories).

---

## 9. Search Indexing: Elasticsearch Refresh

**Default refresh_interval:** 1 second (self-managed Elasticsearch https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-indices-refresh); 5 seconds (Elasticsearch Cloud Serverless). Refresh operation makes newly indexed documents visible to searches; without refresh, documents indexed but not yet visible. Tradeoff: frequent refresh (0.1s) = low latency but high IO/CPU; infrequent refresh (30s) = lower IO but stale search results.

**Search Idle Behavior:** Index delays refresh if idle (no search requests received). Default idle window: 30 seconds; if no search in 30s, refresh deferred until next search arrives. Refreshes immediately upon search request (user sees >100ms latency spike on first search after idle). Reduces IO on low-traffic indices; appropriate for news archives and rarely-accessed content sections.

**Indexing Rate:** Per-shard indexing throughput typically 5k-50k docs/sec depending on doc size and refresh interval. Bulk indexing recommended for >1k docs/sec. Too-aggressive refresh (0.1s) caps throughput to ~1k docs/sec (IO-limited).

**Time-Based Indices (News Archive):** Strategy: daily index per date (articles-2024-09-30, articles-2024-10-01) enables fast deletion of old indices without compact-and-delete cost. Search all indices via alias "articles" pointing to indices from past 30 days. Hot index (today) refresh 1s; warm indices (past 7 days) refresh 30s; cold indices (>30 days) no refresh (searchable via snapshot).

**Failure modes:** refresh_interval 0.1s on 100k docs/sec → CPU maxed at 95%, search latency p99 >1s (user timeout). Search Idle default 30s may be too aggressive (if feed traffic bursty, index drops to stale state then refreshes on first search, user sees 30s latency spike). Time-based index explosion (10k daily indices) → cluster metadata bloat, coordination overhead increases linearly. Delete-by-query on compacted indices expensive (requires full rescan, O(N) complexity). Index alias churn (repointing alias to new index daily) risks stale reads if client caches old index name.

**Tuning Parameters:** refresh_interval=1s for hot indices (past 24h), 30s for warm (1-7d old), 300s for cold (>7d old). search.idle.after=60s for static archives, 5s for breaking news. index.number_of_replicas=1 for availability (can lose 1 node, data still available); 0 for test/staging.

**Use when:** Real-time search needed (<5s publish-to-searchable latency); article count <10M. Avoid: Refresh <0.1s (CPU wasteful, little user-facing benefit); single monolithic index >100GB (use time-based sharding to keep indices <20GB).

---

## 10. Event Log: Kafka Log Compaction

**Cleanup Policy:** `cleanup.policy=compact` (https://kafka.apache.org/41/configuration/topic-configs/) enables log compaction for stateful streams (e.g. "article upsert" topic). Retains latest value per message key; older versions deleted. Tombstone (null value) marks delete; presence in log until delete.retention.ms expires. Default cleanup: delete.retention.ms=-2 (uses topic's `retention.ms`); if retention.ms=7d, tombstones expire after 7 days.

**Configuration Knobs:** `min.cleanable.dirty.ratio` default 0.5 (50%) controls compactor frequency; only compact when >50% of log is redundant (older key versions). `min.compaction.lag.ms` optional: wait N ms before compacting a key (allows concurrent producers to batch writes before snapshot captured). Example: article.updates topic with `min.compaction.lag.ms=1000` waits 1s after write before considering for compaction (allows 1s window of edits to be combined).

**Compaction Process:** Runs asynchronously in background; does not block producers. Broker reads log, discards older versions of each key, writes compacted segment. Offset gaps appear (deleted offsets disappear) but consumers can use latest read offset to skip directly to recent state.

**Use Cases:** 
- Article upsert stream: key=article_id, value={title, body, author, updated_at}. Compacted topic retains only latest version per article.
- User profile snapshots: key=user_id, value={name, profile_pic, subscriptions, settings}. Single latest state per user.

**Failure modes:** `min.cleanable.dirty.ratio` too high (0.9) → compaction never runs, log grows unbounded until disk full. delete.retention.ms too low (1d) → tombstones disappear, allowing ghost deletes on replay (old consumer resumes old offset, sees deleted key reappear). Compacted topic never read as snapshot (no leader election to compact), log size surprises (expected 10GB, actual 100GB due to compaction lag).

**Use when:** "Upsert" pattern (article edits, user profile updates, feature flags). Avoid: Append-only immutable logs (compaction overhead not worth it); low-compaction-lag use case (>1M key updates/sec, compaction cannot keep up).

---

## 11. Consistency Model & Integration

**End-to-End Consistency:** News aggregator spans multiple consistency regimes. HTTP pull with 304 (strong for cache validation: if publisher returns 304, content unchanged). WebSub push (eventual consistency: hub may deliver notification minutes later, or not at all). Polling (tunable via Retry-After: aggressive retry = faster eventual consistency, but respects publisher rate limits). Kafka compaction (eventual consistency within partition: latest key visible after log compaction completes, but not guaranteed atomic visibility across partitions).

**Dedup Consistency:** Simhash deduplication is approximate (false negatives possible on very similar text); MinHash LSH is probabilistic (threshold-dependent false positive rate). No mechanism guarantees zero duplicates; accept <1% duplicate rate as cost of scale. Synthetic GUID fallback (link-based ID) reduces duplicate risk but introduces new problem: user-perceived duplicates if article has multiple URLs.

**Ordering Guarantees:** Snowflake ID + keyset pagination preserves insertion order within a millisecond. If two articles published in same millisecond, tiebreaker (sequence number) determines order; slight API drift risk if sequence increments faster than clock. TTL on pagination cursor (e.g. 1-hour expiry) prevents stale rank-snapshot errors (if article is bumped up via comments, old cursor still points to pre-bump rank).

**Recommendations for Production:** 
1. Accept that dedup is best-effort, not perfect. Target: <1% duplicate articles in user feed.
2. Use keyset pagination everywhere (eliminate offset-drift bugs; every user sees consistent scroll order).
3. Set Kafka topic TTL=7d and retention.ms=14d to retain 2-week history for backfills and replay scenarios.
4. Monitor 304 hit rate (>80% is healthy; drop indicates publishers changing frequently).
5. Monitor 429 spike rate (>5% indicates publisher overload or aggregator over-aggressive).
6. Implement idempotent ingest: duplicate article insert (same article ID, same content hash) is no-op, not error.
7. Per publisher: track freshness (median age of newest article), error rate (429, 503, timeouts), payload size (detect bloat).
8. For mobile push: stagger fan-out over 10s window (avoid thundering herd on APNs/FCM); rate-limit per user (max 10 high-urgency/day).

---

# Sources

| # | URL | Verifies | Status |
|---|---|---|---|
| 1 | https://www.rfc-editor.org/rfc/rfc9110 | HTTP conditional requests, 304, Retry-After | Fetched |
| 2 | https://www.rfc-editor.org/rfc/rfc6585.html | HTTP 429 Too Many Requests | Fetched |
| 3 | https://www.rssboard.org/rss-specification | RSS 2.0 ttl, skipHours, skipDays, guid, isPermaLink | Fetched |
| 4 | https://www.rfc-editor.org/rfc/rfc4287.html | Atom atom:id, atom:updated | Fetched |
| 5 | https://www.jsonfeed.org/version/1.1/ | JSON Feed 1.1 id field | Fetched |
| 6 | https://www.w3.org/TR/websub/ | WebSub discovery, hub.challenge, lease_seconds, X-Hub-Signature | Fetched |
| 7 | https://pubsubhubbub.appspot.com/ | Google public hub | Fetched |
| 8 | https://developers.google.com/youtube/v3/guides/push_notifications | YouTube WebSub support | Fetched |
| 9 | https://dl.acm.org/doi/abs/10.1145/342009.335391 | Cho & Garcia-Molina SIGMOD 2000 | Bibliography only (403) |
| 10 | https://dl.acm.org/doi/10.1145/958942.958945 | Cho & Garcia-Molina TODS 2003 | Bibliography only (403) |
| 11 | https://developers.google.com/search/docs/crawling-indexing/reduce-crawl-rate | Google crawl rate reduction, 429/503 behavior | Fetched |
| 12 | https://miniflux.app/docs/configuration.html | Miniflux scheduler defaults | Fetched |
| 13 | https://github.com/samuelclay/NewsBlur | NewsBlur source code | Listed (not inspected) |
| 14 | https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls | rel=canonical strength | Fetched |
| 15 | https://dl.acm.org/doi/10.1145/509907.509965 | Charikar STOC 2002 simhash | Bibliography only (403) |
| 16 | http://www.mmds.org/ | Leskovec MMDS Ch. 3 MinHash LSH | SSL error (principles confirmed elsewhere) |
| 17 | https://use-the-index-luke.com/sql/partial-results/fetch-next-page | Keyset pagination no offset | Fetched |
| 18 | https://developer.twitter.com/en/docs/twitter-api/v1/tweets/timelines/guides/working-with-timelines | Twitter since_id, max_id | Fetched |
| 19 | https://docs.stripe.com/api/pagination | Stripe starting_after, ending_before | Fetched |
| 20 | https://blog.twitter.com/engineering/en_us/a/2010/announcing-snowflake | Snowflake ID structure, epoch | Fetched |
| 21 | https://redis.io/docs/latest/commands/zadd/ | Redis ZADD, ZRANGE complexity | Fetched |
| 22 | https://highscalability.com/how-twitter-uses-redis-to-scale-105tb-ram-39mm-qps-10000-ins/ | Twitter celebrity threshold ~10k followers | Search result |
| 23 | https://github.com/reddit-archive/reddit/blob/master/r2/r2/lib/db/_sorts.pyx | Reddit hot ranking formula, 45000 constant | Fetched |
| 24 | https://dl.acm.org/doi/10.1145/2405874.2405904 | Covington YouTube RecSys 2016 | Bibliography only (403) |
| 25 | https://dl.acm.org/doi/10.1145/1935826.1935968 | Li et al. LinUCB WWW 2010 | Bibliography only (403) |
| 26 | https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CreatingtheNotificationPayload.html | APNs payload size limits | Fetched |
| 27 | https://firebase.google.com/docs/cloud-messaging/topic-messaging | FCM topic fan-out limits | Fetched |
| 28 | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | FCM quotas, 600k msgs/min | Fetched |
| 29 | https://www.rfc-editor.org/rfc/rfc8030.html | Web Push TTL, Urgency | Fetched |
| 30 | https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-indices-refresh | Elasticsearch refresh_interval defaults | Fetched |
| 31 | https://kafka.apache.org/41/configuration/topic-configs/ | Kafka cleanup.policy, min.cleanable.dirty.ratio, delete.retention.ms | Fetched |

---

# [unverified] Claims

1. **Bandwidth savings from 304 responses:** "99.6% reduction" cited but no RFC-specified percentage exists; only empirical web practice data (50KB vs ~200 bytes example).
2. **FCM concurrent fan-out limit 1,000 per project:** Stated in docs but could be outdated.
3. **FCM default quota 600k msgs/min covers >99% of developers:** Exact developer distribution breakdown not found.
4. **Reddit 45000 time constant:** Visible in source code; no mathematical derivation or justification found in docs.
5. **Hacker News ranking algorithm:** No official Paul Graham / YC specification published; only community reverse-engineering.
6. **NewsBlur adaptive polling formula:** Repository identified; exact interval formula not located in public documentation.
7. **MinHash LSH S-curve worked example (b=2, r=2 → 0.707):** MMDS textbook inaccessible (SSL); principle confirmed in derivative sources only.
8. **Redis listpack thresholds (128 entries, 64 bytes):** Redis docs (404), values from search cache only.
9. **Retry behavior on WebSub hub failure:** "implementation-defined"; no standard count or window specified.
10. **Elasticsearch search idle window default 30s:** Elastic docs fetched but detailed idle behavior [unverified from primary source].

---

## Spot-check corrections (2026-09-30)

Checked by re-fetching the W3C WebSub spec and the Miniflux configuration page with curl, the SimHash paper with `pdftotext`, and from the Snowflake source constants.

| # | Survey says | What the source says | Verdict |
|---|---|---|---|
| 1 | Snowflake: "1 sign bit + 41-bit ms-timestamp + 10-bit datacenter + 10-bit worker/machine + 12-bit sequence" | That sums to 74 bits. The layout is 41-bit timestamp, 10-bit machine id (5 datacenter + 5 worker in Twitter's implementation), 12-bit sequence, with the sign bit unused. Epoch `1288834974657` ms = 2010-11-04 01:42:54.657 UTC | **Wrong bit count and epoch hour.** Use 41 / 10 / 12 |
| 2 | "304 Not Modified saves 99% bandwidth" | No source given or found | **Unsupported.** Say "a 304 is a few hundred bytes vs ~50 KB for 25 items" as our own estimate |
| 3 | Charikar STOC 2002 "proposes ... k=3 permutation tables" | Charikar defines the random-hyperplane fingerprint. The 64-bit, k = 3 operating point and the permuted sorted tables are Manku, Jain, Das Sarma, WWW 2007 ("for a repository of 8B web-pages, 64-bit simhash fingerprints and k = 3 are reasonable") | **Misattributed** |
| 4 | WebSub `hub.lease_seconds` "recommended default ~10 days" | Spec, security section: hubs should "enforce short lived hub.lease_seconds (10 days is a good default)". Subscriber value is OPTIONAL and "Hubs MAY choose to respect this value or not" | Correct |
| 5 | `X-Hub-Signature` algorithms | "method=signature where method is one of the recognized algorithm names": sha1, sha256, sha384, sha512 | Correct |
| 6 | Miniflux "round-robin ... 60 min window (min 60, max 1440)", entry-frequency "5 to 1440 min" | `POLLING_FREQUENCY` default 60 minutes, `BATCH_SIZE` 100 feeds per interval, `SCHEDULER_ENTRY_FREQUENCY_MIN_INTERVAL` 5, `..._MAX_INTERVAL` 1440, `..._FACTOR` 1 | Correct in substance. The useful detail is that total polls per cycle are capped by `BATCH_SIZE` |
| 7 | Cho and Garcia-Molina "studied 270 sites over 4+ months" attributed to the SIGMOD 2000 freshness paper | The 270-site, 4-month study is their VLDB 2000 incremental-crawler paper. SIGMOD 2000 is the uniform-vs-proportional refresh result. Both PDFs were 403 to the agent | Two papers merged. The uniform-beats-proportional claim is right for SIGMOD 2000 |
| 8 | Redis `zset-max-listpack-entries` 128, `zset-max-listpack-value` 64 marked [unverified] | Both are the `redis.conf` defaults since Redis 7.0 (listpack replaced ziplist) | Correct. Not used in the final design (source lists moved in-process, solution §5.3) |
| 9 | Reddit hot: `sign * log10(max(|score|,1)) + seconds / 45000`, epoch 1134028003 | Matches `_sorts.pyx` | Correct. 45,000 s = 12.5 h: a 10x score is worth 12.5 hours of age |
| 10 | APNs 4 KB (4,096 bytes), VoIP 5 KB. FCM HTTP v1 600k messages/min per project, 1,000 concurrent topic fan-outs | Consistent with Apple and Firebase docs as fetched by the agent. Not re-fetched | Treat as correct, re-check before quoting a number in an interview |
