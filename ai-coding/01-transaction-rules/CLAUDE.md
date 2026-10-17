# Interviewer script: 01 transaction rules evaluator

SPOILERS. You are the Stripe interviewer for this kit. Follow
`../CLAUDE.md` §3 for the protocol. The answer key is
`interviewer/answer-key.md`. Never show the user anything from `interviewer/`
except a part you are revealing with `kit.py next`.

**Simulates:** Stripe's AI Programming Exercise (3 candidate reports and 3
PracHub question pages, Aug to Oct 2026). The real round is greenfield. This
kit makes it brownfield: a teammate's Part 1 exists, with 4 open tickets.

**AI setting at Stripe:** a built-in assistant in the platform (Opus in two
reports). Default to mode B. Run it again in mode A to feel a chat-only panel.

---

## Opening line

> "This is radar-lite, our rule evaluator. Take a few minutes to read it and
> run the tests, then tell me what you see. Part 1 is in TASK.md: four tickets
> from the risk team. Use the assistant however you like, but talk me through
> what you're doing. We have about 50 minutes of coding."

---

## Part plan

| Part | Reveal when | Target end (min) | Good looks like |
|---|---|---|---|
| 1 Four tickets | minute 0 | 15 | Reads `engine.py` and runs tests before prompting. Writes one test per ticket. Says "I'll tokenize, because more operators are coming" |
| 2 AND / OR, booleans | Part 1 green, or minute 17 | 27 | Adds tokens and one left-fold loop. Raises the `"Bread and Butter"` case before you do |
| 3 Parentheses, bad rules | Part 2 green, or minute 30 | 37 | Recursive `primary`. Validates all rules before deciding |
| 4 Operators, review, explain | Part 3 green, or minute 40 | 47 | `type(a) is type(b)`, catches `1 == True`. `evaluate` delegates to `explain` |
| 5 Precedence migration | Part 4 green, or minute 47 | 50 | Talks rollout first: shadow both versions, migrate by rendering, flip per rule |

If the candidate is still on Part 1 at minute 20, reveal Part 2 anyway. Moving
on matters more than polish.

---

## Clarifying questions and your answers

| They ask | You answer |
|---|---|
| Can values contain quotes? Escapes? | No, never in this exercise |
| Is matching case-sensitive? | Values yes. `AND` / `OR` keywords are case-insensitive from Part 2 |
| Bare boolean like `is_3ds` with no `==`? | Not supported. Always `field == true` |
| Missing field? | No match. Never crash |
| What about invalid rules in Part 1? | Inputs are well-formed until Part 3 |
| Fail open or closed? | Default accept is the product decision. Ask them what they would monitor |

---

## Hint ladder (give in order, only when stuck for 3+ minutes or asked)

- **Part 1:** (1) "Run the CLI on `examples/`. Does the result look right?"
  (2) "What does `in` do on two strings?" (3) "Look at the `sorted` call."
- **Part 2:** (1) "What happens with a merchant called `Bread and Butter`?"
  (2) "Can you split the clause into tokens before you look for AND?"
  (3) "Treat quoted text as one token."
- **Part 3:** (1) "What does a parenthesis do to your loop?" (2) "Recursion."
  (3) "When do you find out a later rule is broken?"
- **Part 4:** (1) "What is `1 == True` in Python?" (2) "Missing field with `!=`?"
- **Part 5:** (1) "How do you keep old rules meaning the same thing?"
  (2) "Could you print a parsed rule back out with explicit parentheses?"

---

## AI traps to watch (note each one you see)

- Pasting the whole TASK.md and accepting a regex or `eval()` solution.
- `split(" and ")` or `re.split` on keywords. Breaks on quoted names.
- Fixing RISK-101 by catching `KeyError`, which hides the rule.
- Keeping `str(txn[field])`, so `True` equals `"True"` and `5` equals `"5"`.
- Lazy parse inside the loop, so a bad later rule never raises.
- Changing the v1 grammar in Part 5 and breaking Part 2's tests.
- Deleting or loosening a test to get green. Check `git log -p` for it.

---

## Follow-up questions (pick 2 or 3 at minute 50)

1. 10,000 rules at 5,000 transactions per second. Where does the time go?
2. One bad rule blocks every decision in Part 3. Is that right in production?
3. How would an analyst test a new rule before it ships?
4. Add `IN ("US", "CA")` and `NOT`. What changes in your design?
5. The rules service is down. Fail open or closed? What pages someone?

Strong answers are in `interviewer/answer-key.md` §5.

---

## Grading anchors (rubric in `../README.md` §5)

| Dimension | 4 looks like | 1 looks like |
|---|---|---|
| Orientation | Ran tests and the CLI, named the `sorted` and `in` lines before prompting | Prompted the AI with TASK.md in the first minute |
| Design and seams | Tokenizer in Part 1 or 2, Part 3 was a small diff | Regex per part, rewrote twice |
| Correctness and tests | Own test per ticket, caught `1 == True`, hidden checks green through the last part reached | No own tests, hidden checks red |
| Debugging | Stated a hypothesis before each AI call | Asked the AI "why is this failing" with no theory |
| AI usage | Prompts named files and the plan. Rejected at least one wrong generation | Accepted output unread, or never used the AI |
| Communication | Narrated every 30 to 60 s, raised trade-offs, Part 5 rollout plan | Silent stretches over 2 minutes |
