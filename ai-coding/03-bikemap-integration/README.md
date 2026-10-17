# 03 BikeMap integration

> Simulates Stripe's **Integration round**, BikeMap family: read a recorded bike ride, call a documented map-rendering API you have never seen, and save the images. Most of the work is reading docs and getting the contract exactly right.

| | |
|---|---|
| Round type | Integrate an unfamiliar, documented HTTP API into a small existing app |
| Stripe evidence | 3 candidate reports and 4 PracHub question pages (Dec 2025 to Oct 2026). The Oct 1, 2026 report matches this kit's first three parts. See [research/stripe-rounds.md](../research/stripe-rounds.md) §3 |
| Time | 60 min: about 50 coding, 10 follow-up questions |
| Starter | `ridemap`: 6 small modules (about 100 lines), a 495-point GeoJSON ride, a 290-line API reference, and a local fake of the API (`tools/mapdraw_server.py`) |
| Parts | 5. Reports say most candidates finish about three |
| Stripe AI setting | Unknown for this round, and one guide says not allowed. Practise **mode C (no AI) first**, then mode B |

## Run it

```
$ python3 ai-coding/kit.py start 03-bikemap-integration    # prints the run dir and Part 1
$ cd ~/ai-coding-runs/03-bikemap-integration-<stamp>
$ python3 tools/mapdraw_server.py                          # leave running in its own terminal
$ python3 ai-coding/kit.py check ~/ai-coding-runs/03-...    # when you think a part is done
$ python3 ai-coding/kit.py next  ~/ai-coding-runs/03-...    # reveal the next part
```

Or start `claude` inside `ai-coding/03-bikemap-integration/` and say "interview me".

**Do not open `CLAUDE.md` or `interviewer/` before your first run.**

## What to practise here

- Skim the whole API doc before writing a request. Note auth, limits, error format and what a success response actually is.
- Run the starter against the fake early. Read every error message the API sends back.
- Write binary output as binary. Check the image by opening it.
- Say how you would verify the integration against the real vendor, not only the fake.
- A real candidate lost 15 minutes to a broken local debugger. Know how you debug without one: `print`, `python3 -m pdb`, `curl`.
