# Q&A Bank (machine coding practice)

Practice reps, copied from the local workspace `~/workspaces/qa-bank` on 2026-10-25. Its git history and `reset.sh` stay there.

## The prompt (as the interviewer gives it)

Build the MVP backend for a Stack Overflow style Q&A bank. Keep all data in memory.

- Create a question.
- List questions, each with a UUID.
- Upvote a question.

Test it through Postman/curl, unit tests or integration tests. Keep business logic separate from the web layer (DTOs, DAO).

Format: 45 min coding, then 45 min discussion. Clarify aloud for the first 3 minutes.

Graded on: create + list work, at least one basic error handled, 400 on bad input, 201/200 codes, a UUID per question, web vs business layer split, concurrency on the votes map, at least one test and one comment, clean OOP, debugging.

Compare your contract with the one on the prep page (#coding) only after the rep.

## Setup (already done)

- Java 21 target, Spring Boot 3.5.16, Maven. Web, validation, test starters, MapStruct.
- `GET /health` and `POST /echo` are the sample endpoints. Replace them as you go.
- `HealthControllerTest` shows the MockMvc pattern.

## APIs

All data is in memory. Writes take `X-User-Id` (the caller) and `Idempotency-Key` (a retry with the same key replays the first result, marked `Idempotent-Replayed: true`). Reads are public. Designs are in `docs/design/`.

| Endpoint | Does | Design |
|---|---|---|
| `POST /questions` | Create a question with optional tags: 201 | `CreateQuestion.md` |
| `GET /questions` | List questions, newest first, a page at a time, optionally by tag: 200 | `ListQuestions.md` |
| `GET /questions/{id}` | Get a question with its answers: 200 | `GetQuestion.md` |
| `PUT /questions/{id}` | The author replaces content and tags: 200 | `UpdateQuestion.md` |
| `POST /questions/{qid}/answers` | Answer a question, one answer per user: 201 | `AddAnswer.md` |
| `GET /questions/{qid}/answers/{aid}` | Get one answer: 200 | `GetAnswer.md` |
| `PUT /questions/{qid}/answers/{aid}` | The answer's author replaces its content: 200 | `UpdateAnswer.md` |
| `POST /questions/{qid}/upvotes` | Upvote a question, once per user and never your own: 201 with the count | `Upvote.md` |
| `POST /questions/{qid}/answers/{aid}/upvotes` | Upvote an answer, with the same rules: 201 with the count | `Upvote.md` |
| `POST /questions/{qid}/downvotes` | Downvote a question, never your own. One vote per user, up or down: 201 with the count | `Downvote.md` |
| `POST /questions/{qid}/answers/{aid}/downvotes` | Downvote an answer, with the same rules: 201 with the count | `Downvote.md` |

## Commands

```bash
mvn spring-boot:run     # start on :8080
./curl.sh               # smoke test every API against the running server (BASE=... for another one)
mvn test                # run unit tests
mvn verify              # unit tests plus FTs; starts the app on :8081 for the FTs, then stops it
mvn verify -Dft.groups=api       # unit tests plus the per-API FTs only: the quick green gate
mvn verify -Dft.groups=journey   # unit tests plus the journey FTs only
mvn verify -Dft.groups=journey -Dit.test=BusyDayJourneyFT -Djourney.seed=<s>   # rerun a busy day's seed, both modes
mvn verify -Dft.port=8082 -Dft.jmxPort=9002   # FTs on other ports (defaults 8081 and JMX 9001)
```

Pick an FT group with `-Dft.groups`, not `-Dgroups`. Surefire reads `groups` too, so `mvn verify -Dgroups=api` runs none of the unit tests and still passes. See `docs/design/UserJourneys.md`, Build and tags.

## Rules for a rep

1. AI plugins off (Copilot, JetBrains AI). Notes closed.
2. Timer on. Talk out loud as if the interviewer is listening.
3. Log the minute of the first `curl` 201 and the first green test.

## Run log

| Date | Rep | First 201 (min) | First green test (min) | Parts done | Weakest moment |
|---|---|---|---|---|---|
| | | | | | |
