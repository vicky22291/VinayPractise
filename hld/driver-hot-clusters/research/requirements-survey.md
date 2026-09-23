# Research: requirements survey for "hot clusters in a city"

Raw notes from a web search on 2026-09-23. Input to [`../README.md`](../README.md) and [`../solution.md`](../solution.md), not study material. Each claim is marked **verified** (primary source fetched and checked), **reported** (secondary source, not checked), or **inference**.

## 1. Candidate reports

| Source | What it says | Status |
|---|---|---|
| [Blind, Uber L6 Staff round](https://www.teamblind.com/post/uber-l6-staff-engineer-system-design-round-8euje85r) | "Every driver app is sending their location in real time, plot a heat-map showing the number of drivers in particular location in last 20 minutes, consider 1 minute bucket." Second part: "make the data available for analytics after 24 hours (should be durable)". Comment thread: probes on sampling, storage, retrievals, latency, TTL. Respondent proposed Redis for real time, Cassandra for durable, partition by lat/lon | verified (page fetched) |
| [Glassdoor, "Design uber heatmap"](https://www.glassdoor.com/Interview/Design-uber-heatmap-QTN_3387503.htm) | Listed as a senior system design question | reported |
| [Hello Interview community, driver heatmap backend](https://www.hellointerview.com/community/questions/driver-heatmap-backend/cmatifpty00whad086tfsq0nz) | Real-time driver density heatmap. No 20 minute or 1 km² constraint in the listing | reported |

Takeaway: the 20-minute window, 1-minute buckets and a durable 24 h+ analytics store are consistent across reports. The "institutions hourly" and "not counted multiple times" parts appear only in this user's version.

## 2. Grid

- H3 average hexagon area: res 7 = 5.161293360 km², res 8 = 0.737327598 km², res 9 = 0.105332513 km². [h3geo.org resolution table](https://h3geo.org/docs/core-library/restable/). **verified**
- Uber open-sourced H3 in 2018 and uses it for marketplace analysis and pricing. [Uber blog, H3](https://www.uber.com/blog/h3/). **reported**
- No H3 resolution is exactly 1 km². A square grid in a city-local projected coordinate system is. **inference**

## 3. Uber's real-time stack

- "Real-time Data Infrastructure at Uber", SIGMOD 2021, [arXiv 2104.00087](https://arxiv.org/abs/2104.00087). Abstract: PBs collected continuously, decisions in seconds, built on open source with customisations. **verified** (abstract). The body describes Kafka, Flink, Pinot and Presto. **reported**
- The agent claimed Flink 2-minute checkpoints and 1-minute tumbling windows at Uber, from an ads exactly-once blog. Different use case. **Not used.**

## 4. Data sharing with institutions

- Uber Movement shared aggregated, anonymised travel-time data with cities; no per-trip data. [PRI / The World, 2017](https://theworld.org/stories/2017/01/20/uber-making-ride-sharing-data-publicly-available-privacy-pandora-box). **reported**
- The [Mobility Data Specification](https://github.com/openmobilityfoundation/mobility-data-specification) (Open Mobility Foundation) is the standard US cities use to require data from mobility operators. **reported**

## 5. Scale numbers

- "9.9 M active drivers globally" and "80k NYC drivers" came from statistics aggregator sites. These count people who drove at least once in a period, not drivers online at the same moment. **Not used as concurrency.**
- Solution assumes 1.5 M concurrent online drivers globally at peak and 50k in the largest city. **inference, stated as an assumption.**
- "4 to 5 s ping on trip, 30 to 60 s idle" came from an unverified blog. **unsourced.** The problem says 10 s; keep it.

## 6. Pitfalls interviewers probe

- Flink sliding windows assign each element to size/slide windows. 20 min / 10 s = 120 copies. [Flink window docs](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/#sliding-windows). **reported**
- Idle source partitions stall the watermark; use `withIdleness`. [Flink watermark docs](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/). **reported**
- Late GPS pings (tunnels, offline buffering), phone clock skew, boundary jitter, HLL vs exact sets. All standard; see the solution for numbers. **inference**
