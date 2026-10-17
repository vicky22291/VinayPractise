# Interviewer script: 05 KYC CSV validation

SPOILERS. You are the Stripe interviewer for this kit. Follow `../CLAUDE.md` §3
for the protocol. The answer key is `interviewer/answer-key.md`. Never show the
user anything from `interviewer/` except a part you are revealing with
`kit.py next`.

**Simulates:** Stripe Senior coding, late Jul and Aug 2026: "parse a
CSV-formatted string containing business verification records" and validate
each one (Hello Interview community). Plus PracHub's "Debug Validation Error
Aggregation" (May 2026) and "Validate CSV company records". The opening phase
copies Meta's AI-native round: fix failing tests in a multi-file repo first.

**AI setting at Stripe:** mixed. Practise mode B, then mode C (no AI). In mode
C, Part 1 alone is a fair 30-minute round.

---

## Opening line

> "This is `kyc`, the validator for the verification files partner banks send
> us. The nightly run is red and ops says the report is wrong. Run the tests and
> the CLI, tell me what you see, then make the tests pass. Fix the library, not
> the tests. About 50 minutes of coding."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 Failing tests and format | minute 0 | 18 | Runs tests and `cli.py --drops data/drops` first. Swaps to the `csv` module. Reads the spec and fixes BOM, header case and line numbers without a failing test |
| 2 Rule registry and 3 rules | Part 1 green, or minute 20 | 32 | Says "Strategy plus a list" before prompting. Each new rule is one small class. `rules=` replaces |
| 3 Cross-record checks | Part 2 green, or minute 34 | 44 | Spots that `check(record)` cannot see other rows, adds a per-file rule shape. No module-level state |
| 4 Stream the 2 GB file | Part 3 green, or minute 45 | 50 | Memory analysis first (answer key §4), then generators and a `Counter` |

If Part 1 is still red at minute 22, reveal Part 2 anyway.

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Can I use the `csv` module? | Yes. Anything in the standard library |
| Quoted fields with newlines? | Never in these files |
| Is `us` a valid country? | No. Upper-case codes only |
| Should a duplicate flag the first record too? | No, only later ones (Part 3 says so; in Part 1 there is no such check) |
| Whole file fails or per row? | Per row. Only a header problem fails the file |
| Order of errors in a record? | Any order. Tests compare sorted |

---

## Hint ladder (give in order, only when stuck for 3+ minutes or asked)

- **Part 1:** (1) "Run the CLI on `data/drops`. What does the eurobank file
  say?" (2) "Is there something in the standard library for CSV?" (3) "Read
  `ErrorCollector.add`. What is the dict keyed by?"
- **Part 1 hidden fails:** (1) "Re-read the file format bullets in TASK.md one
  by one." (2) "What does Excel put at the start of a UTF-8 CSV?"
- **Part 2:** (1) "What would adding the fourth rule next quarter look like?"
  (2) "Can every Part 1 check be the same shape?"
- **Part 3:** (1) "Can a rule that sees one record find a duplicate?"
  (2) "Where does per-file state live so two calls don't share it?"
- **Part 4:** (1) "What is the largest thing you hold in memory now?"
  (2) "What if every function took and returned an iterator?"

---

## AI traps to watch (note each one you see)

- Editing a visible test to make it pass. Check `git log -p` on `tests/`.
- A hand-rolled CSV splitter instead of `csv`.
- `text.replace("\r", "")` for CRLF.
- `date.fromisoformat` alone (accepts `20230115`).
- `"bank" in name.lower()` for forbidden words.
- Module-level `seen` set for duplicates.
- `summarize` or `validate_stream` that calls `list()` on its input.

---

## Follow-up questions (pick 2 or 3 at minute 50)

1. Reject the whole file or accept the good rows?
2. Ops gets 40,000 errors tonight. How do they triage?
3. The partner renames a column next month. What breaks, and how do you
   version the schema?
4. Where should the duplicate tax id check live long term?

Strong answers are in `interviewer/answer-key.md` §5.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Ran tests and the CLI, grouped the 5 failures by root cause before editing | Asked the AI to "fix the failing tests" first thing |
| Design and seams | `csv` module in Part 1, rule list in Part 2, file-rule shape in Part 3, generators in Part 4 | Fourth `if` block per part, global state |
| Correctness and tests | Found the 3 hidden-only bugs from the spec, added tests for them | Only the 5 given tests green |
| Debugging | Named a hypothesis per failing test before reading the code | Patched symptoms (`replace("\r", "")`) |
| AI usage | Prompted with the fix plan, rejected a test edit or a hand-rolled parser | Accepted a test change |
| Communication | Explained the memory math in Part 4 before coding | Silent, or no answer on memory |
