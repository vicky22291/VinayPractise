# Hotel Booking (machine coding practice)

Practice reps, copied from the local workspace `~/workspaces/hotel-booking` on 2026-10-25. Its git history and `reset.sh` stay there.

## The prompt (Part 1, as the interviewer gives it)

Guests search hotels and reserve rooms. Build the API in memory.

| Endpoint | Body / header | Result |
|---|---|---|
| `POST /api/v1/hotels` | `{name, city, roomTypes: [{type, count, pricePerNight}]}` | 201 |
| `GET /api/v1/availability?city=&checkIn=&checkOut=` | | 200, room types free on every night of the stay |
| `POST /api/v1/reservations` | `{hotelId, roomType, checkIn, checkOut}` + header `X-Guest-Id` | 201 `RESERVED` with `holdExpiresAt` · 409 sold out · 400 bad dates |
| `POST /api/v1/reservations/{id}/confirm` | | 200 `CONFIRMED` · 409 if expired |

**Must hold:** 20 concurrent requests for the last room on overlapping nights give exactly one 201. Model inventory per room type per night.

Format: 90 min. Build Part 1 by about minute 30. Claude reveals Parts 2 to 4 live, one at a time (say "start hotel coding mock").

## Setup (already done)

- Java 21 target, Spring Boot 3.5.16, Maven. Web, validation, test starters.
- `GET /health` and `POST /echo` are the sample endpoints. Replace them as you go.
- `HealthControllerTest` shows the MockMvc pattern.

## Commands

```bash
mvn spring-boot:run     # start on :8080
./curl.sh               # smoke test the running server
mvn test                # run tests
```

## Rules for a rep

1. AI plugins off (Copilot, JetBrains AI). Notes closed.
2. Timer on. Talk out loud as if the interviewer is listening.
3. Log the minute of the first `curl` 201 and the first green test.

## Run log

| Date | Rep | First 201 (min) | First green test (min) | Parts done | Weakest moment |
|---|---|---|---|---|---|
| | | | | | |
