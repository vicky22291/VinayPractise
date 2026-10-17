## Part 2: fix it

Fix every root cause you found. Your Part 1 tests and all existing tests must
pass.

Constraints:

- The body a merchant receives may change only in its `id` field. Every other
  byte stays the same: compact UTF-8 JSON.
- Keep the shape of the retry schedule: first retry after 2 minutes, doubling,
  never more than 6 hours apart, about 3 days in total.

Before you call it done: one of your fixes changes what every receiver sees.
Tell the interviewer which one, whether merchants on an old SDK can still
verify, and how you would roll it out and roll it back.
