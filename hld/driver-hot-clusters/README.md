# Driver hot clusters in a city (driver density heatmap)

> One-line answer: turn every 10 s GPS ping into a `(driver, cell, minute)` presence fact, keep one exact "last seen minute" per driver per 1 km² cell in a stream processor keyed by cell, so the 20-minute count is a sum of 20 minute-buckets with every driver counted once no matter how many pings it sent; push the per-cell counts to Redis every 10 s for the ops heatmap, land raw pings in the lake, and build the hourly institution files with the same code in batch mode after a 15-minute late-data cutoff, aggregated and k-anonymised. Nothing here is big (60k pings/s, a few hundred MB of state). The hard parts are the definition of "counted once", time (late pings, lying phone clocks, watermarks), and making the real-time and hourly numbers agree.

Tier 4, problem #42 in [`hld/README.md`](../README.md). Reported as an Uber L6 (Staff) round. Reusable blocks: [`../../concepts/geospatial-index.md`](../../concepts/geospatial-index.md) (cells, H3), [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md) (event time, watermarks, checkpoints), [`../../concepts/stream-sketches.md`](../../concepts/stream-sketches.md) (HyperLogLog, and why we do not need it), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md), [`../streaming-ingestion/`](../streaming-ingestion/) (how raw pings land in the lake), [`../uber-ride-hailing/`](../uber-ride-hailing/) (the location ingest this reuses).

## Problem statement (as given)

Hot clusters in a city.
- Drivers send location information every 10 s.
- The land is broken into cells of 1 km².
- The operations team wants to see this information for the past 20 minutes and take decisions on it.
- The information should be near real time.
- The same information has to be shared with multiple institutions on an hourly scale.
- A driver must not be counted multiple times.

## What the web research changed

Sources checked on 2026-09-23. Research notes in [`research/requirements-survey.md`](research/requirements-survey.md).

| Change | Requirement | Evidence |
|---|---|---|
| ADD | Count in **1-minute buckets**. The 20-minute view is a sliding window that moves every minute (every 10 s at the edge) | Uber L6 report on [Blind](https://www.teamblind.com/post/uber-l6-staff-engineer-system-design-round-8euje85r): "heat-map showing the number of drivers in particular location in last 20 minutes, consider 1 minute bucket" |
| ADD | **Durable history.** Per-minute counts queryable for analytics after 24 h and kept for months | Same Blind report: "make the data available for analytics after 24 hours (should be durable)". Follow-ups on sampling, storage, TTL |
| ADD | **Hot cluster** = a group of adjacent cells above a threshold, not just a single cell | Inference from the word "clusters" in the prompt. Ask the interviewer |
| ADD | **Privacy.** Institutions get aggregates only. No driver id, no trajectory, small counts suppressed | Uber Movement shared only aggregated, anonymised data with cities ([PRI, 2017](https://theworld.org/stories/2017/01/20/uber-making-ride-sharing-data-publicly-available-privacy-pandora-box)). City data-sharing standards like the [Mobility Data Specification](https://github.com/openmobilityfoundation/mobility-data-specification) exist because regulators ask for this |
| ADD | **Late and out-of-order pings, wrong phone clocks** must not corrupt counts | Standard probe for this question. Covered in [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md) |
| UPDATE | "Near real time" becomes a number: ping to heatmap **p99 under 30 s**, refresh every 10 s | Pings arrive every 10 s, so a refresh faster than 10 s shows nothing new. Some prep sites say 2 to 5 s; push back on that |
| UPDATE | "Not counted multiple times" becomes precise: a driver counts **once per cell per window** however many pings it sent, retries and duplicates change nothing, and a city total is distinct across cells, never a sum of cells | The prompt's wording is ambiguous. Make the definition explicit before designing |
| UPDATE | "Hourly to institutions" becomes: hour H is **published by H+30 min**, final, reproducible, and restated once at D+1 if late data changed it | Inference. Regulators want stable numbers more than fast ones |
| KEEP | 1 km² cells. Use a square grid in a city-local projection. H3 resolution 8 (average 0.737 km²) is the Uber-native alternative if "about 1 km²" is fine | [H3 resolution table](https://h3geo.org/docs/core-library/restable/): res 7 = 5.161 km², res 8 = 0.737 km², res 9 = 0.105 km² |
| KEEP | 10 s ping interval. Real apps vary the rate (faster on trip, slower when idle); the design does not care because it dedups to one fact per driver per minute | Rate figures online (4 to 5 s on trip) come from unverified blogs, so treat them as unsourced |
| DELETE | Nothing deleted. One thing is **rejected as a requirement**: approximate counting (HyperLogLog). At city scale exact sets are a few MB, so exactness costs nothing | See [`deep-dives/windowed-distinct-count.md`](deep-dives/windowed-distinct-count.md) |

## Final requirements

Functional:
1. Ingest a ping from every online driver every 10 s and map it to a 1 km² land cell.
2. For every cell, count distinct drivers seen in the last 20 minutes, in 1-minute buckets. Each driver counts once per cell.
3. Ops dashboard: city heatmap plus hot clusters (adjacent hot cells), refreshed every 10 s, with a 20-minute trend per cell.
4. Hourly, deliver the same per-cell numbers to multiple institutions, aggregated and anonymised, each under its own contract.
5. Keep per-minute cell counts durable for analytics after 24 h (90 days hot, longer cold).

Non-functional: p99 ping-to-screen under 30 s. Exactly-once effect on counts. Dashboard 99.9% of minutes fresh. Hourly file by H+30 min at 99.5%. Scale to 500 cities and 1.5 M concurrent online drivers.

## What interviewers probe

1. What does "counted once" mean when a driver drives through 5 cells in 20 minutes? What is the city total?
2. Why not a Flink sliding window of 20 minutes sliding every 10 s? (Each event gets copied into 120 windows.)
3. Do you need HyperLogLog? Do the memory math.
4. A phone's clock is 1 hour ahead. What happens to your watermark and every count in the city?
5. A driver parks on a cell boundary and GPS jitter flips the cell every ping. Double counted?
6. The ops number for 14:00 to 14:20 and the institution file disagree. Which is right, and why are they different?
7. The Flink job restarts. What does ops see, and is anything double counted after replay?
8. An institution asks for per-driver data, or for 100 m cells. What do you say?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one diagram built one requirement at a time, deep dives that change the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/windowed-distinct-count.md`](deep-dives/windowed-distinct-count.md) | The red node: 20-minute distinct count per cell, minute buckets, why not sliding windows, why not HLL, runnable Python |
| [`deep-dives/time-watermarks-and-late-pings.md`](deep-dives/time-watermarks-and-late-pings.md) | Event time vs server time, clamping phone clocks, watermarks, idle partitions, catch-up after restart |
| [`deep-dives/grid-cells-and-clusters.md`](deep-dives/grid-cells-and-clusters.md) | Square grid in a local projection vs H3, land mask, boundary hysteresis, hot-cluster detection |
| [`deep-dives/hourly-institution-export.md`](deep-dives/hourly-institution-export.md) | Batch recompute, completeness gate, k-anonymity, delivery contract, restatements |
| [`research/requirements-survey.md`](research/requirements-survey.md) | Web research notes with source links. Input to the files above |
| `driver-hot-clusters.excalidraw` | My drawing. Missing until I draw it |
