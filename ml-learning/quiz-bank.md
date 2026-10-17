# Quiz bank

> Closed-book retrieval cards. The AI asks them one at a time. Keys live in `answers/quiz-key.md` and are shown only after you answer.

## Card types

| Type | Asks for |
|---|---|
| N | A number, with its reason |
| M | A mechanism: why or how |
| T | Transfer: a variant not run, or the payments version |
| D | Debugging: a symptom and the first check |

- Each lab gets three cards: one M, one N, and one T or D.
- D comes every other lab. Debugging was the largest gap in Anthropic's randomized trial of engineers learning a new library with AI help (see `research/practical-machine-learning-curriculum.md`).
- Card ID: the lab number and the type, for example `09-N`.

## A good card

- Asks for recall: no multiple choice, no yes or no.
- Takes under 60 seconds, closed book.
- Tests the mechanism or the judgement, not an API name.
- Has a key with 1 to 3 must-mention items.
- Is not answered by the lab file's own text.
- Takes its numbers from the reference run or a cited source. A measured number goes in the key, never in the question: this bank is safe to show at any time.

## Boxes and due dates

Grade each answer against its key. **Hit:** every must-mention item. **Partial:** some of them. **Miss:** none.

| Result | Box after | Due |
|---|---|---|
| New card | 1 | next session |
| Hit in box 1 | 2 | 7 days later |
| Hit in box 2 | 3 | 21 days later |
| Hit in box 2, N card | retired | none |
| Hit in box 3 | 4 | 60 days later |
| Hit in box 4 | retired | none |
| Partial | same box | next session |
| Miss | 1 | next session |

- Due is a date, `YYYY-MM-DD`. "Next session" means tomorrow's date, so the card comes up at the first session from then on.
- A card is due when its Due date is today or earlier.
- Log: one entry per review, `YYYY-MM-DD hit`, `partial` or `miss`, separated by `; `.
- A retired card stays in the table with Box `retired` and an empty Due.

## Opener (0:00, 5 min)

- The AI asks three due cards, one at a time. Misses first (cards whose last review was a miss), then oldest Due first. Never two from the same lab. If fewer than three qualify, it asks fewer.
- Lab 01 uses three items from the fastbook chapter 1 questionnaire instead.
- Do not open the bank first.

## Weekly sweep (20 min)

- Once a week: every due card, oldest Due first, at most 30. The rest roll over.
- Why: in the learning review's 20-seed simulation, the opener alone got 0 of 111 cards to 3 reviews. With the weekly sweep all 111 got there, at a median of 2 days overdue and about 31 reviews a week.

## Close (0:57, 3 min)

The AI drafts three cards to these rules. You edit or replace them in 3 minutes. Questions go here. Keys go to `answers/quiz-key.md`.

## Cards

| ID | Lab | Type | Question | Box | Due | Log |
|---|---|---|---|---|---|---|
| 09-N (example) | 09 | N | On card data with 0.17% fraud, what accuracy does 'never fraud' score, and why does that make accuracy useless here? | 1 | `<date>` | Example only, never asked. Delete this row when the first real card goes in. |
