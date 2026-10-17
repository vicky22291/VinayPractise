# Interviewer script: 04 invoice matching

SPOILERS. You are the Stripe interviewer for this kit. Follow
`../CLAUDE.md` §3 for the protocol. The answer key is
`interviewer/answer-key.md`. Never show the user anything from `interviewer/`
except a part you are revealing with `kit.py next`.

**Simulates:** Stripe's Reconciliation round, payment-to-invoice matching (4
candidate reports and 3 PracHub question pages, Sep 2025 to Oct 2026). The real
round is greenfield in three parts: memo ID, exact amount, forgiveness. This kit
makes it brownfield: a teammate's Part 1 exists with 3 tickets and 2 failing
tests, then adds a multi-invoice part and a Staff scale part.

**AI setting at Stripe:** not reported for this round. Default to mode C (no
AI), then repeat in mode B.

---

## Opening line

> "This is recon. It matches bank payments to open invoices for finance every
> night. A teammate wrote it and moved on. Take a few minutes to read it and run
> the tests and the CLI, then tell me what you see. Part 1 is in TASK.md. Talk
> me through what you're doing."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 Memo matching, 3 tickets, 2 failing tests | minute 0 | 15 | Runs the CLI and sees the crash. Notices the parse test passes while the line prints `500.0`. Finds rule 2 (first **open** ID) without a ticket |
| 2 Match by amount | Part 1 green, or minute 17 | 25 | Asks "is the invoice list sorted?". Falls through on paid or unknown IDs, not only on missing IDs |
| 3 Forgiveness tolerance | Part 2 green, or minute 27 | 33 | One sort key `(diff, due, position)`. Says exact beats tolerance before coding |
| 4 Several invoices, `open_after` | Part 3 green, or minute 35 | 42 | Turns `Match.invoice` into a tuple without breaking the CSV export or its test |
| 5 Scale and reruns | Part 4 green, or minute 44 | 50 | States `O(P x I)` first. Index by id and amount. Dedupe by batch **and** by payment |

If the candidate is still on Part 1 at minute 20, reveal Part 2 anyway.

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Do amounts ever have decimals, like the `500.00` comment says? | No. Integer cents. The comment is stale |
| Are IDs case-sensitive? `inv-4`? | Exact match only. `inv-4` is not an ID |
| Does a memo match need the amount to agree? | Not in Part 1 (rule 4). Ask them what finance would want to see |
| Can an invoice ID repeat in the invoice list? | No, IDs are unique |
| Same payment ID twice in one file? | Not until Part 5 |
| Tolerance: absolute or percent? Inclusive? | Absolute cents, inclusive, both directions (Part 3 says so) |
| Is the invoice list sorted? | No. Good question |
| Can I change the CSV columns? | No. The ledger team owns that import |

---

## Hint ladder (give in order, only when stuck for 3+ minutes or asked)

- **Part 1:** (1) "Run the CLI on `data/`." (2) "Print the type of a parsed amount."
  (3) "What does `\d` match? What does `search` return when the memo names two IDs?"
- **Part 2:** (1) "Is the invoice list sorted?" (2) "What happens when the memo names an
  invoice that was already paid?" (3) "What key decides between two equal amounts?"
- **Part 3:** (1) "Is an exact match just a tolerance match with difference zero?"
  (2) "One sort key can cover both tiers."
- **Part 4:** (1) "Your Match holds one invoice. What does it need now?"
  (2) "Who else reads Match?"
- **Part 5:** (1) "How many invoices does one payment look at today?"
  (2) "What would you index by?" (3) "The bank resends one payment in a new file. What happens?"

---

## AI traps to watch (note each one you see)

- Pasting TASK.md and accepting a rewrite that uses the `csv` module for payment lines.
- Fixing the float at print time with `:.0f` instead of at parse time.
- Keeping `re.search`, so only the first ID is tried.
- Sorting `invoices` in place, which changes "first in the list".
- Tolerance tier that ignores "exact first", or a suffix on memo matches.
- Changing the export columns, or breaking `tests/test_export.py` in Part 4.
- Part 5: dedupe by batch only, or a cache that still scans all invoices.
- Deleting or loosening a test to get green. Check `git log -p`.

---

## Follow-up questions (pick 2 or 3 at minute 50)

1. "What if there is an exact match with forgiveness applied? How would we prioritize that?" (asked at Stripe, Oct 2026)
2. "Can you think of any other things you could be missing with this implementation?" (also asked)
3. A memo match where the amounts differ. What should finance see?
4. Two invoices tie on everything. Should the job guess?
5. How does finance audit why a payment matched a given invoice?

Strong answers are in `interviewer/answer-key.md` §5.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Ran tests and CLI, traced `500.0` to `parse_amount`, read `export.py` before changing `Match` | Prompted the AI with TASK.md in the first minute |
| Design and seams | Open-invoice set and tier method in Part 1 or 2. Part 3 was a sort key, Part 4 a tuple | Nested ifs per part, rewrote matching twice |
| Correctness and tests | Own test per ticket, hidden checks green through the last part reached, export test still green | No own tests, export broken |
| Debugging | Said "the parse test passes because 500.0 == 500" before fixing | Asked the AI "why do the tests fail" with no theory |
| AI usage | Prompts named files and functions. Rejected the `csv`-module or in-place sort suggestion | Accepted output unread, or never used the AI in mode B |
| Communication | Narrated every 30 to 60 s, raised the priority question before coding Part 3, gave `O(P x I)` in Part 5 | Silent stretches over 2 minutes |
