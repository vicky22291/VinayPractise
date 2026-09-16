# 01. Data types and a leaderboard

> Goal: after this I can pick the right Redis type for a use case and say what it costs in memory and time complexity.

**Concept link:** `concepts/caching.md`
**Time:** 15 min. Hard stop.
**Status:** todo

## Setup

```
$ cd tool-practise/redis
$ docker compose up -d
$ docker exec -it redis redis-cli
```

## Steps

### 1. String as an atomic counter (2 min)

Why: `INCR` runs inside the single thread, so no two clients can interleave. This is the primitive under every counter and rate limiter.

```
> SET page:home:views 0
OK
> INCR page:home:views
(integer) 1
> INCRBY page:home:views 10
(integer) 11
> GET page:home:views
"11"
```

### 2. Hash as an object (3 min)

Why: one key holding many fields. Small hashes are stored as a compact "listpack", far cheaper than one string key per field.

```
> HSET user:42 name "vinay" plan "pro" logins 0
(integer) 3
> HINCRBY user:42 logins 1
(integer) 1
> HGETALL user:42
1) "name"
2) "vinay"
3) "plan"
4) "pro"
5) "logins"
6) "1"
> MEMORY USAGE user:42
(integer) 88          <- roughly. Under ~100 bytes for a 3-field hash.
> OBJECT ENCODING user:42
"listpack"
```

### 3. Sorted set as a leaderboard (5 min)

Why: skip list plus hash table. `ZADD` O(log N), rank query O(log N), top-K O(log N + K). This is the answer to "design a leaderboard".

```
> ZADD lb 100 alice 250 bob 175 carol 300 dave
(integer) 4
> ZREVRANGE lb 0 2 WITHSCORES
1) "dave"
2) "300"
3) "bob"
4) "250"
5) "carol"
6) "175"
> ZINCRBY lb 200 alice
"300"
> ZREVRANK lb alice
(integer) 0           <- ties: lexical order of member breaks them. alice < dave, so alice is rank 0.
> ZRANGEBYSCORE lb 200 +inf
1) "bob"
2) "alice"
3) "dave"
```

### 4. List and set, one command each (2 min)

Why: know they exist, know the one use case each.

```
> LPUSH jobs job1 job2 job3
(integer) 3
> RPOP jobs
"job1"                <- list as a FIFO queue. BRPOP blocks, so workers do not poll.
> SADD seen a b c
(integer) 3
> SISMEMBER seen b
(integer) 1           <- set for O(1) membership. Dedup, follower sets.
```

## Break it (3 min)

Load 1M members into a sorted set and see the memory cost. Terminal B:

```
$ docker exec -i redis sh -c 'for i in $(seq 1 1000000); do echo "ZADD big $i m$i"; done | redis-cli --pipe'
All data transferred. Waiting for the last reply...
Last reply received from server.
errors: 0, replies: 1000000
$ docker exec redis redis-cli MEMORY USAGE big
(integer) ~90000000   <- expect roughly 80 to 100 MB. About 90 bytes per member.
$ docker exec redis redis-cli INFO memory | grep used_memory_human
```

Wait. `maxmemory` is 64mb in the compose file. What happened to the load? Check:

```
$ docker exec redis redis-cli INFO stats | grep evicted_keys
$ docker exec redis redis-cli DBSIZE
```

What I saw:

```
<paste>
```

Then in Terminal A, time a full range read while it blocks everyone:

```
> ZRANGE big 0 -1
```

Notice the prompt hangs for a moment. Every other client waited too.

## What I learned

- Sorted set costs about ___ bytes per member at 1M members.
- A full `ZRANGE` on 1M members blocked the server for about ___ ms.
- ...

## Interview soundbite

> "For the leaderboard I'd use a sorted set: O(log N) updates and top-K reads. At 1M players that's roughly 100 MB, so it fits on one node; the thing I'd guard against is anyone running an unbounded ZRANGE on it, because Redis is single-threaded and that stalls every client."

## Cleanup

```
$ docker exec redis redis-cli FLUSHALL
```
