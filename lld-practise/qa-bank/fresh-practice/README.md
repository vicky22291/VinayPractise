# Q&A Bank (machine coding practice)

Clean starter for a fresh rep, copied from the `starter` tag of `~/workspaces/qa-bank` on 2026-10-26. No `reset.sh` here, because this folder lives in the main repo.

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

- Java 21 target, Spring Boot 3.5.16, Maven. Web, validation, test starters.
- `GET /health`, `POST /echo` and `GET /hello[?name=X]` are the sample endpoints. Replace them as you go.
- `HealthControllerTest` shows the full-context MockMvc pattern (`@SpringBootTest`).
- `HelloWorldControllerTest` shows the faster web-slice pattern (`@WebMvcTest`). Mock services with `@MockitoBean`.

## Commands

```bash
./dev.sh                              # run all tests, then start the server on :8080 if they pass
./dev.sh test                         # run all tests
./dev.sh test HelloWorldControllerTest   # one class (or Class#method)
./dev.sh run                          # start the server only (Ctrl+C stops it)
./dev.sh smoke                        # curl the running server (same as ./curl.sh)
PORT=9090 ./dev.sh run                # if :8080 is taken
git restore --source=HEAD . && git clean -fdx .   # back to the committed starter (run from this folder)
```

## Rules for a rep

1. AI plugins off (Copilot, JetBrains AI). Notes closed.
2. Timer on. Talk out loud as if the interviewer is listening.
3. Log the minute of the first `curl` 201 and the first green test.
4. When done, copy the attempt somewhere if you want to keep it, then restore the starter so the next rep starts clean.

## Run log

| Date | Rep | First 201 (min) | First green test (min) | Parts done | Weakest moment |
|---|---|---|---|---|---|
| | | | | | |
