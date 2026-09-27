# Staff Design Method

**One rule:** a number, NFR or failure that doesn't change a decision is noise. Say the thing, then what it forces.

**Clock:** 10 requirements · 15 HLD · 20 announced deep dive · 5 wrap.
Infra problems (S3, queue, rate limiter): shrink HLD to ~8, the deep dive *is* the round.

---

## 1. Requirements — 10 min

**Functional:** 2–3 operations, each with its hard constraint. Name the crux. Park the rest with a hook.
> "Assign one driver per ride *and* one ride per driver — that's the crux. Payments, ratings out; I'll leave a seam."

**Non-functional:** only the 2–3 that shape this problem.
- **Consistency — per operation.** Contention? Stale outcome permanent or self-healing? Cost of being wrong? Permanent → strong.
- **Availability.** What does downtime cost *on this path*? Say where it's fine to be down.
- **Latency.** p99 = what the user perceives − network. Budget the remainder.
- **Scale.** How big *and* how spiky (peak ÷ avg).

**Input numbers:** users, QPS, read:write, peak:avg. Givens only.

## 2. HLD — 15 min

Stand up a working skeleton, then one **scale pass**:
- Trace a request forward; label each edge **1:1 / 1:N / N:1**.
- Hot edge = **fan-out × rate**, firehose, convergence (N:1 on state), or skew.
- Annotate only hot edges: **number → what it forces.**

## 3. Deep dive — 20 min

Announce it: *"I'm going deep on X."* Pick the convergence point — scale, consistency and failure usually meet there.

**Failure pass on that component:**
- **Infra:** node · AZ · network partition/delay · GC pause (alive but frozen)
- **Logical:** duplicate · race · poison message · backpressure
- **Recovery:** catch-up · split-brain while healing
