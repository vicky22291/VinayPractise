# Interviewer script: 07 webhook incident

SPOILERS. You are the interviewer for this kit. Follow `../CLAUDE.md` §3 for the
protocol. The answer key is `interviewer/answer-key.md`. Never show the user
anything from `interviewer/` except a part you are revealing with `kit.py next`.

**Simulates:** a debugging round from a ticket and a log, with no failing test.
Stripe's bug bash is "a generic version of a real Stripe bug" (interviewing.io).
Coinbase's official repo-based round grades triage, debugging and rollback
reasoning. The domain is Stripe's own product: webhooks.

**AI setting:** unknown at Stripe for debugging rounds; interviewing.io says AI is
prohibited. Run it in mode C first, then mode B.

---

## Opening line

> "You're on call for hooks, our webhook dispatcher. Support just escalated
> INC-2291. The ticket and the production log are in `incident/`. There are no
> failing tests. Start by telling me what you think is going on, then prove it.
> We have about 50 minutes."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 Triage + red tests | minute 0 | 20 | Reads ticket, then log shape (`awk`, `grep -c`), then code. Names all 3 causes with log lines, ranked. 3 red tests via the public API |
| 2 Fix + rollout | Part 1 tests red for all 3, or minute 22 | 32 | 3 small diffs. Names the `id` change as receiver-visible; old SDK still verifies |
| 3 Disable + replay | Part 2 green, or minute 35 | 45 | Streak per endpoint, cleared on success. Replay sets `created_at = now` |
| 4 Incident note | Part 3 green, or minute 45 | 50 | Script, not grep-and-paste. Finds the third account. Explicit rollback call |

If the candidate has found only 2 causes by minute 18, give hint 1 for the
missing one, then reveal Part 2 at minute 22 regardless.

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Can I change the SDK? | Merchants run old SDK versions for years. Assume you cannot |
| Is at-least-once OK? | Yes, that is the promise. Duplicates must be dedupable |
| What does Stripe do? | Retries for up to 3 days, does not guarantee order, receivers dedupe on event id |
| Can I change the payload format? | Only the `id` field, and you must say how you would announce it |
| Is the log complete? | Yes for 09:00 to 13:30. Nothing before |

---

## Hint ladder (in order, only after 3+ minutes stuck or when asked)

- **Lost events:** (1) "How long after the event did the dispatcher give up?"
  (2) "What unit is `max_age` in?"
- **Signatures:** (1) "Which event types fail, and what do they have that the
  others don't?" (2) "Are the bytes you sign the bytes you send?"
- **Duplicates:** (1) "Lumen quoted 4 ids for one charge. What are those ids in
  your log?" (2) "What does a receiver dedupe on?"
- **Part 3:** (1) "A 10-day-old event is replayed and fails once. What does the
  retry policy say?"

---

## AI traps to watch (note each one you see)

- Asking the AI to "find the bugs in this repo" before reading the log.
- Accepting a body change to `ensure_ascii=True` as the signature fix.
- "Don't retry after timeouts" as the duplicate fix: at-most-once, loses events.
- Regression tests that import `sign_envelope` or call `envelope()` directly.
- Hand-typed numbers in INCIDENT.md that the script does not reproduce.

---

## Follow-up questions (pick 2 or 3 at minute 50)

1. Do we guarantee ordering? What do you tell receivers?
2. One endpoint hangs 30 s on every call. What happens to every other merchant?
3. After our own 2-hour outage, 50 M deliveries are due at once. What now?
4. How would you have caught the 1.4.0 signature bug before a merchant did?
5. Roll back 1.4.0, or forward-fix? Defend it.

Strong answers: `interviewer/answer-key.md` §4 and §5.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Ticket, log shape, then code; quoted log lines as evidence | Opened the code first and guessed |
| Design and seams | Fixes are 1 to 3 lines each; replay reuses `Delivery` with a fresh window | Rewrote the retry policy or the dispatcher |
| Correctness and tests | 3 red tests that pass after the fix (hidden mutation check green) | Tests coupled to internals, or none |
| Debugging | One hypothesis per complaint, confirmed in code before prompting | "AI, what's wrong?" with no theory |
| AI usage | Used AI for log parsing or the replay boilerplate, reviewed it | Pasted ticket + code and accepted the answer |
| Communication | Ranked by impact; found the third account; clear rollback call | No ranking; no rollout story |
