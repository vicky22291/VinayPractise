## Part 4: survive production

In production MapDraw sometimes answers `429` or `5xx`, and sometimes the
connection drops after MapDraw has already accepted the render. Every render
costs us a credit.

1. The client becomes
   `MapDrawClient(base_url, api_key, timeout=10, sleep=time.sleep)`. All
   waiting goes through `sleep`, so tests can pass a fake one.
2. On `429`, wait the number of seconds in `Retry-After`, then retry.
3. On `500`, `502`, `503`, `504`, a dropped connection or a timeout, retry with
   exponential backoff: wait 0.5 s, then 1 s, then 2 s, then 4 s.
4. At most 5 attempts per `render` call in total. After that, raise
   `MapDrawError`.
5. Never retry any other status, such as `400`, `401` or `409`.
6. One call to `render` must never cost more than one credit, even when the
   response to the first attempt was lost.

To try it by hand, restart the fake with
`python3 tools/mapdraw_server.py --fault-rate 0.4`. It prints the number of
billed renders when you stop it.

Before you code it, tell the interviewer what you would log.
