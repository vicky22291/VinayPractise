# Interviewer script: 10 billing legacy refactor

SPOILERS. You are the interviewer for this kit. Follow `../CLAUDE.md` §3 for
the protocol. The answer key is `interviewer/answer-key.md`. Never show the
user anything from `interviewer/` except a part you are revealing with
`kit.py next`.

**Simulates:** a Staff probe of test strategy before changing money code.
Evidence is the weakest in the set: no Stripe report describes this task.
Hello Interview's AI-coding guidance stresses verification, and Staff loops ask
"how would you change this safely". The domain is Stripe Billing: proration,
coupons, trials, tax.

**AI setting:** mode B. The trap is the AI writing tests from an imagined spec
instead of from what the code does.

---

## Opening line

> "This is our billing code. It's old, it has no tests, and finance
> reconciles against it. Product wants changes. Before anyone touches it, I'd
> like you to pin what it does today. There's a known bug in the ticket. Don't
> fix it yet. About 15 minutes."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 Pin behaviour | minute 0 | 15 | Golden snapshot recorded from the current code over all fixtures and many months, including December. A few named rule tests |
| 2 Refactor | Part 1 suite green, or minute 17 | 32 | Extract one piece at a time, suite after each. Names segments as the riskiest step |
| 3 BILL-212 for new periods | Part 2 golden green, or minute 34 | 44 | One function picks 30 or real days from the period start. Talks rollout and finance first |
| 4 Metered usage | Part 3 green, or minute 44 | 50 | Usage never cuts segments. Priced by the plan in force |

Run `kit.py check --summary` at the end of Part 1. If the mutant check fails,
tell them the kill rate only ("your suite noticed 9 of 13 small changes"), then
move on. That is the most useful feedback in this kit.

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Can I change the code to make it testable? | Not in Part 1. Black-box through `generate_invoice` |
| Is the 30-day rule the bug, or is it intended? | It's BILL-212. Finance confirmed it's a bug. Pin it anyway |
| Do other weird things count as bugs? | Not unless finance says so. Pin them |
| Which dates matter? | Every invoice since 2023 can be regenerated |
| Can the golden file be big? | Yes. Readable failures matter more than size |
| Effective date: as_of or period start? | Period start (Part 3 says so) |

---

## Hint ladder (only when stuck 3+ minutes, or asked)

- **Part 1:** (1) "How would you know the output didn't change, without
  knowing what's correct?" (2) "Which inputs exercise each `if` in the
  function?" (3) "Is February enough? What about December?"
- **Part 2:** (1) "What's the smallest extraction you could do first?"
  (2) "Run the suite after each one."
- **Part 3:** (1) "Where is the 30?" (2) "What decides old vs new: the caller
  or the data?"
- **Part 4:** (1) "What does the event loop do with an event kind it doesn't
  know?"

---

## AI traps to watch (note each one you see)

- AI-written tests that assert real-day proration, so they fail on today's code
  and the candidate "fixes" the code to match.
- A snapshot of only the CLI's February: it misses December, trial edges and
  the amount-off cap (about 69% kill rate, below the bar).
- A one-shot AI rewrite in Part 2 that silently drops a quirk (setup fee during
  trial, volume tier floor division).
- A `version` parameter defaulting to the new behaviour in Part 3.
- Usage added to the old event loop, cutting seat segments.
- Editing the snapshot to make a red test green without saying why.

---

## Follow-up questions (pick 2 or 3 at minute 50)

1. How did you choose which inputs to pin?
2. How do you know the refactor is safe beyond your tests?
3. Regenerating October in December must match. What could still break that?
4. Finance wants the revenue effect of BILL-212 over the last year. How?
5. What would you deliberately not refactor?

Strong answers are in `interviewer/answer-key.md` §5.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Read the whole function and the fixtures, ran the CLI for two months before writing tests | Asked the AI for tests at minute 1 |
| Design and seams | Extracted pieces so Parts 3 and 4 were small diffs in one place each | One-shot rewrite, then patches |
| Correctness and tests | Kill rate at least 12 of 13, goldens green through the last part reached | Suite red on today's code, or under 75% kill |
| Debugging | When a golden failed, diffed the field and found the quirk before changing anything | Re-recorded the snapshot to get green |
| AI usage | Used the AI to scaffold the snapshot harness and extractions, checked every value it asserted | Accepted asserted values the code doesn't produce |
| Communication | Named the riskiest step, a rollout plan and what finance hears | No plan for existing invoices |
