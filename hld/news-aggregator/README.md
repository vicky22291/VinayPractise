# News aggregator / personalized news feed (Feedly, Google News, "Personalized Google Feed")

> One-line answer: ~10,000 publishers each expose a "latest 25" endpoint, so an adaptive poller asks each one often enough that 25 items always overlap the last poll (`interval ≤ 25 / (2 × publish rate)`), with conditional GETs, a per-host rate budget and a circuit breaker per publisher, and adds WebSub push where a publisher offers it. Ingest dedups at five levels (the last poll's ids, publisher guid, canonical URL, 64-bit SimHash for verbatim syndicated copies, story clustering for rewrites of the same event) and assigns a time-ordered 64-bit article id. The feed is **fan-out on read**: the whole recent corpus (72 h, ~900k cards, ~0.9 GB) and the per-source recent lists (~25 MB) are replicated into every feed server from the article stream, so a request is an in-memory merge of the user's ~25 sources plus interest, trending and breaking lanes, then ranking, one card per story. A ranked page is frozen in a 20-minute feed session so infinite scroll never repeats or skips, and new stories go to a "N new" pill, not into the middle. At 100 M DAU that is ~120k feed reads/s at a breaking-news peak against ~35 new articles/s at a news peak: ~3,300:1, like for like. The red node is the fetcher at the publisher boundary, because a publisher's rate limit is the one resource money cannot buy.

Tier 3, problem #44 in [`hld/README.md`](../README.md). The most reported Rippling system design prompt (7 candidate posts, 2022 to 2026). Reusable blocks: [`../../concepts/fan-out-fan-in.md`](../../concepts/fan-out-fan-in.md) (why every publisher is a "celebrity"), [`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md) (token buckets toward publishers, shedding to a cached feed), [`../../concepts/caching-patterns.md`](../../concepts/caching-patterns.md), [`../../concepts/bloom-filter.md`](../../concepts/bloom-filter.md), [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md) (click velocity), [`../../concepts/realtime-client-server-communication.md`](../../concepts/realtime-client-server-communication.md) (the "N new" pill), [`../distributed-job-scheduler/`](../distributed-job-scheduler/) (the poll scheduler is a small one).

## Problem statement (as given)

Verbatim from Rippling candidate posts, all re-fetched on 2026-09-30:

- "Design a Google news sort of service where we scrape from multiple news sites. Assume they provide endpoint to get latest 25 news from each publisher. There can be thousands of publishers." Then: "write down table schema for all like publisher, user, category_subscription, publisher_subscription, articles etc and handle deduplication in article scraping service", and "user's should be able to subscribe to certain categories like Education or publishers say ndtv." ([SDE 2, 2024](https://leetcode.com/discuss/interview-experience/5590877))
- "News aggregator system like Google News. Fetch news articles from multiple news publishers. Generate custom news feed for Users based on their interests and the publishers they follow." ([Senior, screening HLD round, Aug 2024, offer](https://leetcode.com/discuss/interview-experience/5698133))
- "Newsfeed system design for systems like feedly." "All design choices are questioned." ([L7 down-levelled to L6, 2022](https://leetcode.com/discuss/interview-experience/2118542))
- "Design something like Personalized Google Feed." ([L6, 2022](https://leetcode.com/discuss/interview-experience/1979218))
- "Design News Aggregator and feed system." Lean Hire, down-levelled. ([Senior, Jan 2024](https://leetcode.com/discuss/interview-experience/4496620/Senior-Software-Engineer-or-Rippling/)). "Design a News Aggregator" as the L7 tech screen ([L7, 2024, offer](https://leetcode.com/discuss/interview-experience/5094495)).

The Hello Interview "News Aggregator" breakdown (Google News) is the public reference. Its public outline: 3 FRs (aggregated feed from thousands of publishers, infinite scroll, click through to the publisher), availability over consistency, and deep dives on pagination consistency, feeds under 200 ms, articles within 30 minutes of publication, media, and breaking-news spikes ([Hello Interview](https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-news)).

## What the web research changed

Sources checked on 2026-09-30. Notes and spot-check corrections in [`research/`](research/).

| Change | Requirement | Evidence |
|---|---|---|
| ADD | **Publishers give only the latest 25.** Completeness is a scheduling problem: poll before 25 new items pile up, and detect the gap when they do | Rippling SDE 2 prompt, above |
| ADD | **Subscriptions to publishers and categories**, plus implicit interests, with a schema written out | Rippling SDE 2 and Senior 2024 prompts |
| ADD | **Dedup is asked by name.** Re-fetched items, the same article under two URLs, edits, and syndicated copies of one wire story are four different problems | Rippling SDE 2 prompt. PracHub (Rippling tag): "An article may arrive more than once from syndicated sources" ([page](https://prachub.com/interview-questions/design-a-personalized-news-feed-aggregator)) |
| ADD | **Deterministic pagination while articles keep arriving** | Same PracHub page. Hello Interview deep dive 1 |
| ADD | **Breaking news for everyone "without permanently overriding personalization"**, and a way to take a false "breaking" label back | Same PracHub page and its follow-ups |
| ADD | **Publishers are unreliable third parties:** slow, down, rate limited, silently stop publishing | PracHub publisher-APIs page (Rippling, Backend Engineer, onsite) ([page](https://prachub.com/interview-questions/design-a-news-aggregator-that-builds-personalized-feeds-from-publisher-apis)) |
| UPDATE | "Fan-out on write vs read, pick a hybrid" becomes: **every publisher is a celebrity** (100 M users over 10k sources), so the hybrid is read-time merge for sources and precompute only for per-user profiles | §2 math: fan-out on write would be ~694k timeline inserts/s to serve ~3.5 articles/s |
| UPDATE | Freshness: Hello Interview says 30 minutes. We keep 30 min for every publisher and add **p95 5 min for the top ~500** that carry breaking news | PracHub pages ask for 3 min p95 and < 5 s; both assume push or heavy polling that a "latest 25" API cannot give |
| KEEP | < 200 ms feed, availability over consistency, users read the article on the publisher's site (we store metadata only) | Hello Interview outline; PracHub publisher-APIs page |
| DELETE | Hosting article bodies, full-text search, comments, social sharing | Out of scope in both references |

## Final requirements

Functional:
1. Ingest new articles from ~10,000 publishers through their "latest 25" endpoints (RSS, Atom, JSON, or WebSub push where offered), deduplicated, metadata only.
2. Let a user subscribe to publishers and categories.
3. Show a personalized feed: subscribed sources plus recommended stories, ranked, one card per story with "N more sources".
4. Scroll "infinitely": no duplicates, no skips, while new articles keep arriving.
5. Click a card to open the article on the publisher's site. The click is recorded.

Non-functional: 100 M DAU. ~12k feed reads/s average, ~35k daily peak, **~120k at a breaking-news spike**. Feed p99 < 200 ms at the server. Freshness from publish to feed: p95 5 min for the top ~500 publishers, 30 min for all. No article silently lost from a publisher we poll inside its window. Feed availability 99.99% (a degraded, non-personalized feed counts). Consistency: eventual for content, read-your-writes for your own subscriptions, a consistent snapshot within one scroll session.

## What interviewers probe

Ranked by how many sources ask it. The PracHub follow-ups are verbatim from Rippling-tagged pages:
1. Fan-out on write or on read? Do the math. What about a user following thousands of sources?
2. A publisher returns only the latest 25. How often do you poll, and how do you know you missed something?
3. The same AP story arrives from 300 papers. "How would you avoid showing five syndicated copies of the same event?"
4. The user is on page 3 and 40 new articles arrive. What does page 4 contain?
5. A publisher rate limits you, goes down, or "silently stopped returning new articles". How do you tell a parser break from a news lull?
6. "A publisher changes an article's title after publication. How does the correction reach users' feeds?"
7. Breaking news: 10x readers in two minutes, and "a breaking story reported by 200 publishers within 90 seconds".
8. A new user with no subscriptions. A new article with no clicks.
9. Write the schema. Why SQL, not NoSQL (or the reverse)? "All design choices are questioned."
10. What changes if a publisher offers webhooks instead of an API you poll?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one diagram built one requirement at a time, deep dives that change the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/publisher-polling-and-rate-limits.md`](deep-dives/publisher-polling-and-rate-limits.md) | The red node: poll scheduler, the latest-25 window math, gap detection, conditional GET, 429 and AIMD, circuit breakers, WebSub, silent-publisher detection, runnable Python |
| [`deep-dives/dedup-and-story-clustering.md`](deep-dives/dedup-and-story-clustering.md) | Five dedup levels, URL canonicalization, edits vs republish spam, SimHash with runnable Python, story clusters and the lead article |
| [`deep-dives/feed-read-path-and-fan-out.md`](deep-dives/feed-read-path-and-fan-out.md) | Fan-out on write vs read with the math, the replicated in-memory corpus, bootstrap and lag, k-way merge, users with thousands of sources |
| [`deep-dives/ranking-and-cold-start.md`](deep-dives/ranking-and-cold-start.md) | Candidate lanes, the v1 scoring formula, recency decay, diversity, profiles from clicks, bandits for new users and new articles |
| [`deep-dives/pagination-and-feed-sessions.md`](deep-dives/pagination-and-feed-sessions.md) | Offset vs keyset vs snapshot, cursor encoding, the "N new" pill, session loss, runnable Python |
| [`deep-dives/breaking-news-and-load-shedding.md`](deep-dives/breaking-news-and-load-shedding.md) | Detecting breaking stories, the breaking lane and its expiry, the 10x read spike, shedding to a CDN-cached feed, the push seam |
| [`research/`](research/) | Three web surveys (real-world systems, mechanisms, interview framing), each with a spot-check corrections table |
| `news-aggregator.excalidraw` | My drawing. Missing until I draw it |
