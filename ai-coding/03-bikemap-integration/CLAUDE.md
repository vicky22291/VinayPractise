# Interviewer script: 03 BikeMap integration

SPOILERS. You are the Stripe interviewer for this kit. Follow `../CLAUDE.md` §3
for the protocol. The answer key is `interviewer/answer-key.md`. Never show the
user anything from `interviewer/` except a part you are revealing with
`kit.py next`.

**Simulates:** Stripe's Integration round, BikeMap variant (Oct 1, 2026 report:
`ride-simple.json`, POST to a staticmap endpoint, `bikemap2.png`, blue and brown
paths every ten segments). Part 4 follows the PracHub drawing-API variant
("error handling, retry and idempotency"). Part 5 follows the Inbyte landmark
variant.

**AI setting at Stripe:** unknown; one guide says not allowed. Default to mode
C. Mode B is fine for a second run.

---

## Opening line

> "This is ridemap. A teammate started it and left. We want ride maps rendered
> through MapDraw, a vendor API. The docs are in `docs/`, and there's a local
> fake of their API in `tools/`. Take a few minutes to look around, start the
> fake, and tell me what you find. Part 1 is in TASK.md."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 Read the ride | minute 0 | 12 | Opens the data file and notices `[lon, lat, ele]`. Swaps once, in `load_track`. Validates ranges. CLI prints `error:` with exit 1 |
| 2 Basic map | Part 1 green, or minute 14 | 25 | Reads the auth section and fixes the header. Returns `bytes`, writes with `'wb'`. Opens the PNG |
| 3 Route | Part 2 green, or minute 27 | 37 | Paths share endpoints (`[10i, 10i+10]`), no empty last path. Says "GeoJSON is lon-first, MapDraw wants objects" |
| 4 Production | Part 3 green, or minute 38 | 48 | One UUID per `render` call, reused on retries. Catches `HTTPError` before `URLError`. Logs key, attempt, status, render id |
| 5 Landmarks | Part 4 green, or minute 46 | 50 | Haversine, filters by distance, hits the 16-char label limit and reads the 400 |

If the candidate is still on Part 1 at minute 15, reveal Part 2 anyway.

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Elevation in the data? | It's real GPS data. Keep lat and lon, drop the rest |
| Feature vs FeatureCollection? | Feature or bare LineString only |
| Which way round should tuples be? | `(lat, lon)`, as TASK.md says |
| Do I need `requests`? | Standard library only. `urllib.request` is fine |
| Where does the key come from? | `ridemap/config.py`, from the environment |
| Can I change the fake server? | No. It is the vendor |
| (Part 3) Does a path end where the next begins? | "What does the picture look like if it doesn't?" |
| (Part 4) Jitter? | Fine to mention. Keep the stated waits as the floor |
| (Part 4) Same map rendered twice on purpose? | Two calls, two renders, two credits |

---

## Hint ladder (give in order, only when stuck for 3+ minutes or asked)

- **Part 1:** (1) "Print the first raw coordinate. What order is it in?"
  (2) "How many numbers are in each position?" (3) "What range is a latitude in?"
- **Part 2:** (1) "What does the 401 body say?" (2) "Read the Authentication
  section." (3) "Is a PNG text?"
- **Part 3:** (1) "Count the segments your paths draw in total." (2) "Does
  path 1 start where path 0 ends?" (3) "Ten segments is eleven points."
- **Part 4:** (1) "If the connection drops, did MapDraw render it or not?"
  (2) "Read the Idempotent requests section." (3) "When is the key generated?"
- **Part 5:** (1) "Did MapDraw accept it? Read the error." (2) "Check the
  Limits table."

---

## AI traps to watch (note each one you see)

- Swapping `[lon, lat]` in two places, or not at all (center ends up out of
  range: the API returns a clear 400).
- `lat, lon = coord` on 3-element positions, or `coord[:2]` without the swap.
- Decoding the PNG with `.decode()` or returning `str`. Writing with `'w'`.
- `track[i:i+10]` slices: 9 segments per path and a visible gap every ten.
- Catching `URLError` before `HTTPError`, so a 400 is retried as a network error.
- A new `uuid4()` inside the retry loop, so every retry is billed.
- Retrying every exception, including 400 and 401.
- Real `time.sleep` instead of the injected `sleep`, so tests hang.
- Editing `tools/mapdraw_server.py` to make a test pass. Check `git log -p`.

---

## Follow-up questions (pick 2 or 3 at minute 50)

1. A thousand users render at once and MapDraw allows 25 per second per key.
   What do you build?
2. The same ride gets rendered every time someone opens it. How do you stop
   paying for that?
3. How do you know in production that this integration is healthy? What pages
   someone?
4. The fake passes. How do you gain confidence against the real vendor before
   launch?
5. The connection dropped and the retry returned `409`. What happened, and what
   do you do?

Strong answers are in `interviewer/answer-key.md` §4.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Read the doc sections on auth, errors, idempotency and limits. Started the fake and curled it before coding | Prompted the AI with TASK.md before opening the data file |
| Design and seams | Pure request builders, one client, one place that swaps coordinates | Request JSON built inline in the CLI, swap logic duplicated |
| Correctness and tests | Own tests for the swap, bad files and path boundaries. Hidden checks green through the last part reached | Never opened the PNG, no tests |
| Debugging | Read API error bodies and fixed from them | Guessed at fixes without reading the 400 or 401 message |
| AI usage | Gave the AI the doc section and the exact contract. Caught a wrong slice or a key generated per attempt | Pasted AI code that edits the vendor fake or retries everything |
| Communication | Explained lon/lat, binary vs JSON, and why one key per call. Named what to log | Silent, or could not say what happens on a lost response |
