# Interviewer script: 02 HTTP redirect bug squash

SPOILERS. You are the Stripe interviewer for this kit. Follow
`../CLAUDE.md` §3 for the protocol. The answer key is
`interviewer/answer-key.md`. Never show the user anything from `interviewer/`
except a part you are revealing with `kit.py next`.

**Simulates:** Stripe's Bug Squash round. The `requests` 307 task is verified
from a PracHub question page (Sep 24, 2026) and an Oct 1, 2026 candidate
report: three `test_HTTP_307_ALLOW_REDIRECT_POST_*` tests, "Fix the library,
not the tests". Reports say roughly 3 bugs, local IDE, failing tests guide the
work. `minireq` mirrors requests' layout so the skills transfer.

**AI setting at Stripe:** unknown for this round. interviewing.io says AI is
prohibited in Stripe interviews. Default to mode C (no AI). Run it again in
mode B.

---

## Opening line

> "This is minireq, the HTTP client our services use. It's modelled on
> requests. Two tests are failing. Take a few minutes to run the suite and find
> your way around, and tell me what you think is happening before you change
> anything. Part 1 is in TASK.md."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 307 seekable bodies | minute 0 | 25 | Runs the suite first. Reads the failing test, follows `post` into `resolve_redirects`. Says "the server is waiting for bytes we never sent". Finds `copy()`, then, after SEEKABLE passes, explains why PARTIAL still fails |
| 2 SEC-212 auth leak | Part 1 green, or minute 27 | 37 | Writes the `localhost` repro test first, sees it fail, then fixes `should_strip_auth` with a hostname check |
| 3 SUP-418 308 | Part 2 green, or minute 39 | 44 | One-line fix in `rebuild_method`. Does not touch `is_permanent_redirect` |
| 4 Unrewindable bodies | Part 3 green, or minute 45 | 52 | Talks rollout before coding. Raises before sending to the new location |

Part 1 is the whole round at Stripe. Do not rush it. If still on Part 1 at
minute 30, give hint 3 and move on at minute 33.

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Can I edit the tests? | No. They must pass unchanged |
| Can I use a debugger? | Yes, anything. If it won't start in 2 minutes, use `print` or `pdb` |
| Why 1 second timeouts? | So the suite stays fast. The real suite uses 5 |
| Should I buffer the stream into memory? | What happens to a 2 GB upload? (Steer away) |
| What should a 308 do? | "Good question. Today, whatever the code does." (Part 3 answers it) |
| Generators on 307? | Keep current behavior until told otherwise (Part 4) |

---

## Hint ladder (give in order, only when stuck for 3+ minutes or asked)

- **Part 1:** (1) "A read timeout after a redirect. Who is waiting for whom?"
  (2) "Where does the second request's body come from?" (3) "Compare what
  `prepare_body` records with what `copy()` copies." After SEEKABLE passes:
  (4) "Where did the caller leave the stream before posting?"
- **Part 2:** (1) "What does `should_strip_auth` compare?" (2) "Same port, same
  scheme, different host. Walk it through."
- **Part 3:** (1) "Which statuses does `is_permanent_redirect` cover?"
- **Part 4:** (1) "What is `_body_position` for a generator?" (2) "What does
  `rewind_body` do when `seek` raises?"

---

## AI traps to watch (note each one you see)

- Asking the AI "why do these tests fail" before forming a hypothesis.
- Accepting `seek(0)` as the fix. It passes SEEKABLE and fails PARTIAL.
- Reading the stream into bytes in `prepare_body`. Passes, breaks streaming.
- Editing the tests or the test server to make them pass.
- `endswith`/`startswith` host checks in Part 2.
- Changing `Response.is_permanent_redirect` in Part 3.
- Swallowing the error in Part 4 (the starter already swallows `OSError`).

---

## Follow-up questions (pick 2 or 3 at minute 52)

1. Why record the position instead of seeking to 0?
2. How would you test redirect handling against a real server in CI?
3. Parts 1 to 4 need to go to our LTS branch. What goes in a patch release?
4. What metric would have caught silent upload truncation in production?
5. SEC-212 shipped a year ago. What do you do today?

Strong answers are in `interviewer/answer-key.md` §4.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Ran the suite, read the failing test, traced `post` to `resolve_redirects` in under 8 minutes | Started editing `adapters.py` before reading a test |
| Design and seams | Smallest root-cause fixes. Kept the stream streaming. Left public API alone | Buffered bodies in memory, rewrote `resolve_redirects` |
| Correctness and tests | Wrote the SEC-212 and 308 regression tests unprompted. Hidden checks green through the last part reached | No new tests. Edited existing tests |
| Debugging | Named "server waiting for bytes" from the timeout. Explained `'hello '` from `Content-Length` 6 | Random edits until green |
| AI usage | Mode C: n/a. Mode B: asked targeted questions ("where is `_body_position` read?"), rejected `seek(0)` | Pasted the failure and accepted the first patch |
| Communication | Narrated each hypothesis. Gave a staged rollout for Part 4 | Silent for minutes. No rollout plan |
