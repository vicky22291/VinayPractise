## Part 3: uploads arrive as GET after a 308

Ticket **SUP-418**:

> The upload service moved from `/v1/upload` to `/v2/upload` and now answers
> `308 Permanent Redirect`. Since then our nightly export POSTs arrive at
> `/v2/upload` as GET requests and are rejected.

A 308 is the permanent version of a 307: same method, same body. A 301 keeps
its current behavior (a POST becomes a GET, as browsers do). Fix it and add a
test.
