# Credit Karma score-change alerts for 100M+ members

> One-line answer: spread the work **before** it becomes a herd. Each member is hashed into a refresh slot across the week, so bureau pulls and their results arrive as a steady ~165 a second per bureau (~330 in all) instead of 100 M at once. Each new report is diffed against the member's last **snapshot** into typed change events (score delta, new account, new hard inquiry, new delinquency). An alert decider keeps only material changes that the member wants, applies dedup and frequency caps, and writes each alert with a dedup key. A **delivery scheduler** releases alerts by priority (possible-fraud alerts in seconds, score changes into the member's local morning) under a global rate that starts low and ramps on the app read path's measured headroom, and it warms the member's score page in cache before the push goes out, because the real herd is not the pushes, it is millions of app opens 2 minutes later. A batch-level quality gate holds alerting and display (not ingestion) when a bureau batch looks wrong (for example 30% of members dropping 50 points), so one bad file cannot scare 100 M people.

Tier 3, problem #53 in [`hld/README.md`](../README.md). From the user's Intuit Principal / Staff practice list (2026-10). Not a reported candidate prompt. Related: [`../news-aggregator/`](../news-aggregator/) (fan-out and polling), [`../streaming-ingestion/`](../streaming-ingestion/), [`../distributed-job-scheduler/`](../distributed-job-scheduler/). Sources: [`research/`](research/).

## Problem statement (as asked)

Credit Karma score-change alerts for 100M+ members. Crux: change detection plus fan-out without a thundering herd on the bureau refresh.

Follow-ups that always come: the bureau delivers 100 M updates at 2 AM, so what happens at 2:05; what counts as a change worth an alert; a bad bureau batch; an alert sent twice or never; the member taps the push and sees the old score; fraud alerts vs score alerts.

## Functional requirements

Core:
- **Refresh.** Pull or receive each member's credit report and score from each bureau (TransUnion, Equifax) on a schedule, and accept bureau monitoring triggers (new inquiry, new account) as they arrive.
- **Detect changes.** Compare the new report with the last one and emit typed, versioned change events.
- **Decide and alert.** Turn material changes into alerts by the member's preferences, quiet hours and frequency caps, with priorities, and deliver by push, email or in-app.
- **Show it.** When the member opens the app from an alert, they see the new score and the reason for the change.

Below the line: computing the score (the bureau's VantageScore model does that), recommendations and offers, disputes, identity monitoring on the dark web, the bureaus' own systems.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | Credit Karma says "more than 140 million members"; design for ~100 M with a bureau file refreshed weekly [estimate], ~40 M monthly active. One report per member per bureau per week: ~200 M reports/week, avg ~330/s. Diffs produce ~25 M material alerts/week [estimate] |
| Herd budget | App read path sized for ~30k req/s. Alert release must keep app-open traffic under that, with 30% headroom |
| Alert latency | Possible-fraud alerts (new account, new hard inquiry): under 5 min from the bureau event, p95. Score changes: in the member's next local morning window |
| Correctness | No alert for a change that did not happen. At most one alert per (member, bureau record); the same event seen at both bureaus is linked for display, not merged for dedup. A crash never loses a material fraud alert |
| Read-your-alert | The app shows a score at least as new as the alert that opened it |
| Availability | Ingestion and diff 99.9% (they can catch up). App reads 99.95% |
| Compliance | FCRA (Fair Credit Reporting Act) data. Encrypted, access logged, retention per policy. Alerts carry no full account numbers |

## What interviewers probe (the ladder)

1. The bureau delivers 100 M updated reports at 2 AM. What happens at 2:05? Where is the herd, exactly?
2. How do you decide a change is worth an alert? A 1-point move, a new account, a balance change?
3. A bad bureau batch drops everyone's score by 80 points. How do you stop it before the pushes go out?
4. The alert worker crashes after sending a push but before recording it. Twice or never?
5. The member taps the push. The app shows last week's score from a cache. How do you prevent that?
6. New-account alerts are possible identity theft. Score changes are not urgent. How do priorities work?
7. What does it cost to keep weekly snapshots for 100 M members for 7 years, and do you need them?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/bureau-ingestion-and-refresh-scheduling.md`](deep-dives/bureau-ingestion-and-refresh-scheduling.md) | Pull vs push from bureaus, hashing members into refresh slots, batch files, monitoring triggers |
| [`deep-dives/change-detection-and-materiality.md`](deep-dives/change-detection-and-materiality.md) | Snapshots, the diff, typed change events, materiality rules, versioning |
| [`deep-dives/fan-out-and-herd-control.md`](deep-dives/fan-out-and-herd-control.md) | Delivery scheduler, priority lanes, adaptive release rate, cache warming, local-time windows |
| [`deep-dives/bad-batch-circuit-breaker.md`](deep-dives/bad-batch-circuit-breaker.md) | Batch-level quality gates, distribution checks, holding and replaying a batch |
| [`deep-dives/preferences-dedup-and-delivery.md`](deep-dives/preferences-dedup-and-delivery.md) | Preferences, caps, quiet hours, dedup keys, APNs and FCM limits, read-your-alert |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `credit-score-alerts.excalidraw` | My drawing. Missing until I draw it |
