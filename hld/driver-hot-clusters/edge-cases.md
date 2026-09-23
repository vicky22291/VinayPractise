# Edge cases: Driver hot clusters in a city

Every entry answerable in under 60 seconds out loud. Categories: failure, consistency, scale, data, operations, security. Design reference: [`solution.md`](solution.md).

---

## Failure

## Edge case: the stream job dies mid-minute
- **Trigger:** TaskManager lost, OOM, deploy.
- **Symptom:** ops map stops updating. `as_of` stops moving.
- **Answer:**
  - Restore from the last checkpoint (30 s interval), seek Kafka to the checkpoint's offsets, replay at ~10x.
  - Replayed presence facts either re-set the same last-seen pointer or are no-ops. Redis gets `SET` of absolute counts. No double count.
  - Eviction follows event time, so counts are right during catch-up.
  - UI shows a stale banner once `as_of` is older than 60 s. Institutions unaffected: the hourly job reads raw pings.
- **Diagram:** `solution.md` §6 Flow 3.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: Redis is lost with no replica
- **Trigger:** primary and replica both gone, or a flush by mistake.
- **Symptom:** heatmap API returns empty cities.
- **Answer:**
  - The API treats a missing `heat:{city}` as "no data", not zero, and shows the banner.
  - Stage 2 re-emits every cell once a minute (not only changed cells), so Redis is full again within 60 s.
  - The 2-hour trend is refilled from `cell_minute_counts` (provisional rows) by a small backfill on start.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the lake is behind when hour H must be published
- **Trigger:** ingestion lag, S3 incident.
- **Symptom:** completeness gate fails at H+15.
- **Answer:**
  - Wait, do not publish partial. Retry every 5 min, alert at H+30, page at H+45.
  - Contract says hours are late, never incomplete. A late hour is a notification; a wrong hour is a restatement and an apology.
- **Diagram:** [`diagrams.md` D5](diagrams.md#d5-hourly-completeness-gate-fails).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the whole region is down
- **Trigger:** region outage.
- **Symptom:** cities in that region have no map. Dispatch there is also down.
- **Answer:**
  - A city lives in one region with the location stack. When dispatch fails over, this job starts in the other region from the replicated lake and the Kafka mirror, with an empty 20-minute state that fills in 20 minutes.
  - Show "warming up, window partial" until 20 minutes of data exist.
  - Hourly jobs re-run from the lake replica.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Consistency

## Edge case: a driver drives through 5 cells in 20 minutes
- **Trigger:** a normal moving driver.
- **Symptom:** the sum of cells is bigger than the number of drivers.
- **Answer:**
  - By definition the driver counts once in each of the 5 cells: each cell answers "how many distinct drivers were here recently".
  - City total is a separate distinct count keyed by city. The UI never labels a sum of cells as "drivers".
  - If ops wants a number that adds up, show average drivers (driver-minutes / 20). A driver who spent 4 minutes in each of 5 cells adds 0.2 to each, 1.0 in total.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a driver parks on the boundary of two cells
- **Trigger:** GPS jitter of 10 to 30 m flips the raw cell every ping.
- **Symptom:** without a fix, the driver counts in both cells.
- **Answer:**
  - Hysteresis in stage 1: switch cell only when the ping is 50 m inside the new cell, or 2 pings in a row are there. Pings with accuracy worse than 100 m never switch.
  - A driver who really crosses still switches within 1 or 2 pings (10 to 20 s).
- **Diagram:** [`diagrams.md` D6](diagrams.md#d6-stage-1-cell-assignment-with-hysteresis).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: the same ping arrives twice
- **Trigger:** mobile retry, producer retry, Kafka redelivery after restart.
- **Symptom:** none.
- **Answer:**
  - Stage 1 drops a `seq` it has seen. Even if a duplicate got through, stage 2 is set semantics: the last-seen pointer does not move twice.
  - The naive design (`INCR` per ping) is exactly where this breaks.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: ops number and institution number disagree
- **Trigger:** late pings arrived after the live window but before the H+15 cutoff.
- **Symptom:** "Airport 212" on the dashboard, "214" in the regulator's file.
- **Answer:**
  - Final is right. Both are the same code; final saw more data.
  - The reconciliation metric shows the gap per city-hour. p99 under 1% is normal; over 2% pages, because it means the stream is losing or double counting.
  - Analysts see `version = final` for anything older than about H+15 min, so they agree with institutions.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a driver goes offline for 19 minutes, then pings from the same cell
- **Trigger:** app backgrounded, phone off.
- **Symptom:** none worth fixing.
- **Answer:**
  - They were seen 19 minutes ago, so they are still in the 20-minute window. The new ping moves their last-seen pointer to now. Count stays 1.
  - If ops wants "online now" rather than "seen recently", use `drivers_in_minute` for the current minute, or filter by status. Different question, same state.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Scale

## Edge case: a stadium empties and 3,000 drivers crowd one cell
- **Trigger:** event ends.
- **Symptom:** one very hot cell.
- **Answer:**
  - 3,000 drivers × one fact per minute = 50 presence/s to one key. Trivial.
  - Kafka is keyed by driver, so there is no hot partition. Re-keying by cell happens after the 5x reduction.
  - The map shows a cluster: the stadium cell plus neighbours above threshold, found by BFS on read.
- **Diagram:** [`diagrams.md` D10](diagrams.md#d10-scaling--partitioning).
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: 10x drivers tomorrow
- **Trigger:** a new market, or pings every 1 s.
- **Symptom:** 1.5 M pings/s.
- **Answer:**
  - Kafka to ~128 partitions, stage 1 to ~160 cores. State ~5 GB. Same design.
  - Better: this use case needs one fact per driver per minute. Sample at the gateway or read from a topic dispatch already downsampled.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: "can we have 100 m cells?"
- **Trigger:** ops or an institution wants finer detail.
- **Symptom:** 100x cells, most counts under 5.
- **Answer:**
  - Compute cost is fine (state is per distinct (driver, cell), which barely grows).
  - Privacy is not: at 100 m most cells fall under k = 5, so the institution file is mostly `<5`, and ops can nearly track one driver. Offer 100 m to ops only, keep 1 km² for institutions.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Data

## Edge case: a phone clock is 1 hour ahead
- **Trigger:** manual time setting, broken NTP.
- **Symptom:** without a fix, the watermark jumps 1 hour, every bucket is evicted, the city reads 0.
- **Answer:**
  - Gateway sets `event_ts = min(device_ts, server_ts)`. Future clocks become server time. The watermark can never pass the wall clock.
  - Skew histogram per app version on the dashboard, so a buggy release is visible.
- **Diagram:** `solution.md` §5.2.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a phone in a tunnel sends 5 minutes of pings at once
- **Trigger:** no signal, then reconnect.
- **Symptom:** 30 pings with old timestamps arrive together.
- **Answer:**
  - Device time (clamped) puts them in the right minutes and the right cells.
  - Anything inside the 20-minute window moves last-seen pointers normally. Late up to 20 minutes is free.
  - Older than the window: live view ignores, hourly batch includes.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a ping lands in a water cell or outside the city
- **Trigger:** bridges, ferries, GPS error, airports outside city limits.
- **Symptom:** a cell that "is not on land".
- **Answer:**
  - The land mask is per city and editable. Bridges and airport land are included on purpose.
  - Pings outside every service area are dropped from counts and counted in a metric.
  - Ask the interviewer whether "on the land" is a filter or just a description of the grid.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: GDPR delete request from a driver
- **Trigger:** driver asks to be forgotten.
- **Symptom:** raw pings contain their location.
- **Answer:**
  - Delete their rows from `raw_pings` (30-day TTL already bounds exposure). Flink state holds them for at most 20 minutes.
  - Aggregates with counts of 5 or more are not personal data; they stay. Re-running an old hour after the delete could change a count by 1: acceptable and documented.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Operations

## Edge case: what pages at 3am
- **Trigger:** n/a.
- **Answer:**
  - `as_of` older than 3 min for 5 min in a tier-1 city.
  - Hour H not published by H+45.
  - Reconciliation diff over 2% in any city-hour.
  - Not pages: clock-skew rate, checkpoint duration, single-city small gaps.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: a stage 2 bug ships
- **Trigger:** new release double counts under some condition.
- **Symptom:** provisional numbers jump.
- **Answer:**
  - Shadow job compares for a day before the flip, so most bugs never ship.
  - If one does, reconciliation catches it within an hour, because the hourly batch pins the previous code version for a day.
  - Roll back the stream by config. Institutions never saw the bug.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

---

## Security / abuse

## Edge case: drivers spoof GPS to appear in a hot area
- **Trigger:** fake-location apps.
- **Symptom:** a cell looks hotter than it is.
- **Answer:**
  - Stage 1 drops pings that imply over 200 km/h and flags repeated teleports.
  - Proper spoof detection belongs to the fraud team. We consume their flag and exclude flagged drivers from counts.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident

## Edge case: an institution tries to track one driver
- **Trigger:** subtracting overlapping windows, or asking for small areas.
- **Symptom:** a count that changes by 1 reveals one driver's movement.
- **Answer:**
  - Only tumbling 20-minute windows, no overlap to subtract. Values under 5 suppressed.
  - No per-driver data, no cells under 1 km², contract lists cities. Credentials scoped to one prefix, downloads audited.
- **Confidence:** [ ] shaky  [ ] ok  [ ] confident
