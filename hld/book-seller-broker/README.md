# Book seller broker

> One-line answer: fan out quote requests with bounded concurrency, collect valid offers until a deadline, and return the cheapest observed offer with explicit seller coverage.

```mermaid
%% The broker owns a deadline, not the sellers' availability
flowchart LR
    C[Buyer] -->|ISBN and delivery context| B[Quote broker]
    B -->|Concurrent quote requests| S[Independent sellers]
    S -->|Offers or errors| B
    B -->|Best observed offer and coverage| C
    class C client
    class B service
    class S external
    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

Tier 1, problem #1 in the [practice index](../README.md). The index attributes this question to Databricks. Its report count is inherited repository context, not independently verified by this research.

## Problem statement

A buyer supplies a book identifier. Query N independent sellers asynchronously and return the best price. Sellers can be slow, unavailable, rate limited, or return after the buyer has stopped waiting. Explain how the broker behaves when N grows from 100 to 100,000 and when it crashes mid-request.

“Asynchronous” initially means concurrent, nonblocking seller calls behind one HTTP response. A seller that accepts work and later calls our webhook is a separate extension. Clarify this distinction early.

## Requirements and assumptions

- Query eligible sellers for the same ISBN, edition, condition, quantity, currency, and delivery context.
- Return the cheapest valid, comparable quote observed by the cutoff, plus coverage and failure counts.
- Finish when every selected seller has a terminal outcome or the deadline expires; support cancellation and bounded retries.
- Worked scale: 1 million daily users, 10 searches/user/day, approximately 1,200 peak searches/s, up to 100 selected sellers/search.
- Worked targets: p99 API duration under 2 seconds, 99.9% timely valid responses, bounded memory, and per-seller traffic isolation. These are design assumptions, not published interview requirements.
- Purchasing, payment, inventory reservations, general book discovery, and guaranteed globally cheapest price are outside the core design.

## Five probes to practice

1. Ten sellers time out. What exactly does “best” mean, and what does the client see?
2. A cheaper quote races the deadline. Which event wins, and can a finished answer change?
3. One seller is slow or allows only 100 requests/s. How do we isolate it across broker replicas?
4. There are 100,000 sellers. What requirement must change before this can be economical?
5. The broker crashes after dispatch or after producing the answer. Does the retry resume, restart, or replay?

## Reading order

| File | Purpose |
|---|---|
| [solution.md](solution.md) | Full design, estimates, API, trade-offs, and operational detail |
| [diagrams.md](diagrams.md) | D1 to D12 diagram index and additional views |
| [edge-cases.md](edge-cases.md) | Short answers to interview follow-ups |
| [Deadline and aggregation deep dive](deep-dives/deadlines-and-aggregation.md) | Exact cutoff, duplicate, cancellation, and quote-validity rules |
| [Quota and scale deep dive](deep-dives/seller-limits-and-scale.md) | Global limits, slow sellers, hot books, and 100,000 sellers |
| [Crash recovery deep dive](deep-dives/crash-recovery.md) | Optional durable requests and callbacks |
| [Research and sources](research/sources.md) | Verified references, their implications, and evidence limits |

Status: `studied` means reference material exists. Confidence is left unmarked. `my-attempt.md` and the hand-drawn Excalidraw remain user-owned exercises.
