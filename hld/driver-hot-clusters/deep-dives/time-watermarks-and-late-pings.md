# Deep dive: time, watermarks, and late pings

> One-line answer: bucket by device time clamped to server time (`min(device_ts, server_ts)`), so tunnel pings land in the right minute and a future-dated clock can never push the watermark past the wall clock; let the watermark drive only eviction, never emission, so freshness is ~23 s regardless of lateness; lateness up to the 20-minute window is free because a late fact just moves a last-seen pointer; anything later is picked up by the hourly batch.

Related: [`../../../concepts/stream-processing.md`](../../../concepts/stream-processing.md), [`../../../concepts/leases-fencing-clocks.md`](../../../concepts/leases-fencing-clocks.md) (never trust wall clocks).

---

## 1. Three clocks

| Clock | Who sets it | Good for | Bad because |
|---|---|---|---|
| Device time | The phone | When the driver was really there, including buffered pings | Phones can be minutes or hours off |
| Server time | The gateway on receipt | Trustworthy, monotonic-ish | Buffered pings land in the wrong minute and wrong cell history |
| Processing time | Flink when it handles the fact | Timers for emission | During replay it is far ahead of the data |

Choice: **event time = min(device, server)**. Device time when it is plausible, server time as a ceiling. A ping older than 2 hours goes to the lake only.

```mermaid
%% How the gateway picks the event time for one ping.
flowchart TD
    P[ping: device_ts, server_ts] --> F{device_ts after<br/>server_ts?}
    F -->|"yes, clock ahead"| S[event_ts = server_ts<br/>count skew metric]
    F -->|"no"| O{older than 2 h?}
    O -->|"yes"| L[lake only,<br/>not in live stream]
    O -->|"no"| D[event_ts = device_ts]
    S --> K[Kafka]
    D --> K

    class P,S,D service
    class F,O decision
    class L external
    class K queue

    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

A clock that is behind is not clamped. It makes pings look late. The worst case is a phone 30 minutes behind: its pings fall outside the window and that driver is missing from the live view. The skew histogram per app version makes this visible; fixing the phone is not our job.

## 2. The watermark and what it controls

- Generated in the Kafka source per partition: max `event_ts` seen minus 10 s. The operator watermark is the minimum over its input partitions.
- `withIdleness(1 min)`: a partition with no data for a minute stops holding the watermark back. With `driver_id` partitioning every partition carries every city, so it rarely triggers. It matters if someone partitions by city and a small city sleeps at night.
- **The watermark only decides eviction.** Emission is a processing-time timer every 10 s that reports the window `[wm_minute - 19, wm_minute]` including the open minute.

```mermaid
%% Freshness budget. The watermark is off the path from ping to screen.
sequenceDiagram
    autonumber
    participant P as Phone
    participant S as Stage 2
    participant R as Redis
    participant U as Ops UI
    P->>S: ping at 14:07:03, arrives 14:07:05
    S->>S: bucket 14:07 updated immediately
    S->>R: emit timer at 14:07:10
    U->>R: poll at 14:07:18
    Note over P,U: ping to screen 15 s. Worst case about 2 + 1 + 10 + 10 = 23 s
    S->>S: watermark passes 14:08:10, evict minute 13:48
```

## 3. Lateness, by how late

| How late | Live view | Hourly final |
|---|---|---|
| Under 10 s | Normal | Included |
| 10 s to 20 min | Included. It moves the driver's last-seen pointer if newer | Included |
| 20 min to cutoff (H+15) | Dropped from live, the window already moved on | Included |
| After cutoff | Dropped | Included in the D+1 restatement |
| Over 2 h (at the gateway) | Lake only | Included if within D+1 |

Push back on the textbook: most answers say "watermark plus allowed lateness of N minutes". With last-seen state there is no window to keep open. Allowed lateness is simply the window length, for free.

## 4. Replay and catch-up

After a 30-minute outage, Flink replays Kafka at ~10x.
- Event-time eviction means buckets are evicted as the data's time moves, not the wall clock. Counts are right at every step.
- `as_of` reports the watermark, which lags the wall clock during catch-up. The UI banner stays on until it is within 60 s.
- If eviction used processing time, every driver would be evicted before their backlog pings were processed, and counts would sit near zero for the whole catch-up.

## 5. What to measure

- `clock_skew_seconds` histogram (device minus server), by app version and OS.
- Share of pings clamped, share lake-only.
- Lateness histogram at stage 2 (watermark minus event time of each fact).
- Watermark lag vs wall clock per job. This is `as_of` age.
