# Interviewer script: 08 settlement report performance

SPOILERS. You are the interviewer for this kit. Follow `../CLAUDE.md` §3 for the
protocol. The answer key is `interviewer/answer-key.md`. Never show the user
anything from `interviewer/` except a part you are revealing with `kit.py next`.

**Simulates:** an "optimize existing code without changing its output" phase.
Meta's AI-native round ends with an optimize phase; Google's pilot is "read,
debug, and optimize". The domain is Stripe-like: balance transactions, FX and
payouts, where a one-cent change is a real bug.

**AI setting:** Stripe unknown for this format. Run mode B (an agent is good at
rewriting loops, and that is the danger here), then mode A.

---

## Opening line

> "This is the settlement report finance pays merchants from. It's correct, but
> a big day takes over half an hour of database time. Run the CLI and the
> tests, then tell me how you'll prove your version prints exactly the same
> bytes. Then make it fast. About 50 minutes."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 Fast, same bytes | minute 0 | 20 | Says "keep the old function as an oracle, diff on seeded data" before coding. 4 round trips. Keeps per-row rounding, and says why |
| 2 Streaming | Part 1 green, or minute 22 | 32 | Swaps to `iter_transactions`; nothing else needs to change if the fold was right |
| 3 Incremental | Part 2 green, or minute 34 | 45 | JSON checkpoint with seq + accumulator; copies input; explains why per-row rounding makes it additive |
| 4 Defend | Part 3 green, or minute 45 | 50 | N, M, C complexity; Postgres rounding mode; shadow run |

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Can I change the output format? | No. Finance diffs it byte for byte |
| Can I add a method to the store? | No, it is the database. Use what is there |
| Are rows of merchants missing from the table possible? | Yes, deleted merchants. Same behaviour as today |
| Why is rounding per row? | "That is how the ledger booked it." Reward them for asking |
| CSV quoting looks broken | Agreed. File it. Not in this PR |

---

## Hint ladder (in order, only after 3+ minutes stuck or when asked)

- **Part 1:** (1) "Count the round trips by method." (2) "Which store methods
  return many rows at once?" (3) If the golden test fails by cents: "Where
  exactly does the original round?"
- **Part 2:** (1) "What holds every row in memory right now?"
- **Part 3:** (1) "What would you need to remember to add 50 rows to
  yesterday's numbers?" (2) "Is your accumulator additive?"

---

## AI traps to watch (note each one you see)

- The AI rewrites with sum-then-round, or with `csv.writer`, and the candidate
  accepts it without diffing against the original.
- The AI deletes or edits the visible tests to match new output.
- The AI adds a method to `payouts/store.py`.
- `list(store.iter_transactions(day))` in Part 2.
- Checkpoint with tuple keys or Decimal values (not JSON).

---

## Follow-up questions (pick 2 or 3 at minute 50)

1. How do you prove a perf change did not change money in production?
2. What do you alert on for this job?
3. A merchant changes payout currency mid-day. What does each version do?
4. A late row arrives for a day whose report was already sent. Now what?
5. When is it worth parallelising, and how do you merge?

Strong answers: `interviewer/answer-key.md` §4.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Ran CLI and tests, counted calls by method, read `_line_for` closely | Asked the AI to "optimize this" in minute one |
| Design and seams | Fold + render split made Parts 2 and 3 small diffs | Rewrote from scratch each part |
| Correctness and tests | Oracle diff test on seeded data; hidden golden green | Trusted the 5 visible tests |
| Debugging | Golden off by cents: found the rounding order from the diff | Tweaked rounding modes until green |
| AI usage | Used AI for the rewrite, then diffed bytes and rejected the rounding change | Accepted a rewrite that changed money |
| Communication | Named the rounding, orphan and CSV traps aloud; numbers in PERF.md | "It's faster now" with no numbers |
