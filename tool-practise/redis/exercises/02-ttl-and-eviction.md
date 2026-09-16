# 02. TTL and eviction

> Goal: after this I can explain exactly what Redis does when memory is full, and pick an eviction policy on purpose.

**Concept link:** `concepts/caching.md`
**Time:** 15 min. Hard stop.
**Status:** todo

## Setup

Fresh server (FLUSHALL from exercise 01 is enough). Terminal A in `redis-cli`.

## Steps

### 1. TTL basics (3 min)

Why: expiry is how a cache stays bounded without anyone deleting. Redis expires lazily on read plus a background sampler (~10 times per second, 20 keys each round).

```
> SET session:abc "data" EX 5
OK
> TTL session:abc
(integer) 4
> PTTL session:abc
(integer) 3210
(wait 5 seconds)
> GET session:abc
(nil)
> TTL session:abc
(integer) -2          <- -2 means key does not exist. -1 means exists with no TTL.
```

### 2. See the current eviction policy (1 min)

```
> CONFIG GET maxmemory
1) "maxmemory"
2) "67108864"         <- 64 MB, from docker-compose.yml
> CONFIG GET maxmemory-policy
1) "maxmemory-policy"
2) "allkeys-lru"
```

The policies worth knowing:

| Policy | Evicts | Use when |
|---|---|---|
| `noeviction` | nothing, writes fail with OOM | Redis is a database, losing data is worse than failing |
| `allkeys-lru` | least recently used, any key | pure cache, default choice |
| `volatile-lru` | LRU among keys with a TTL | mix of cache keys (TTL) and must-keep keys (no TTL) |
| `allkeys-lfu` | least frequently used | hot set is stable, a one-off scan should not evict it |
| `volatile-ttl` | shortest remaining TTL first | keys already say how long they matter |

Redis LRU is approximate: it samples 5 keys (`maxmemory-samples`) and evicts the oldest of them. Not a true LRU list. Cheaper and close enough.

### 3. Fill it up and watch eviction (5 min)

Why: seeing `evicted_keys` climb is what makes "cache is losable" real.

Terminal B, drop the limit to 1 MB so it fills fast:

```
$ docker exec redis redis-cli CONFIG SET maxmemory 1mb
OK
$ docker exec -i redis sh -c 'for i in $(seq 1 20000); do echo "SET k:$i xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; done | redis-cli --pipe'
$ docker exec redis redis-cli DBSIZE
(integer) ~6000       <- far fewer than 20000. The rest were evicted.
$ docker exec redis redis-cli INFO stats | grep evicted_keys
evicted_keys:~14000
$ docker exec redis redis-cli INFO memory | grep -E "used_memory_human|maxmemory_human"
```

Which keys survived? The most recently written ones:

```
> EXISTS k:1
(integer) 0
> EXISTS k:20000
(integer) 1
```

## Break it (4 min)

Switch to `noeviction` and see what a full cache does to writers.

```
$ docker exec redis redis-cli CONFIG SET maxmemory-policy noeviction
OK
$ docker exec -i redis sh -c 'for i in $(seq 1 5000); do echo "SET n:$i xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; done | redis-cli --pipe'
errors: ~5000, replies: 5000
```

Terminal A:

```
> SET anything "x"
(error) OOM command not allowed when used memory > 'maxmemory'.
> GET k:20000
"xxxx..."             <- reads still work. Only writes fail.
```

This is the difference between a cache and a database. With `noeviction`, a full Redis makes every write path in your service return errors.

What I saw:

```
<paste>
```

Restore:

```
$ docker exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
$ docker exec redis redis-cli CONFIG SET maxmemory 64mb
$ docker exec redis redis-cli FLUSHALL
```

## What I learned

- With a 1 MB limit and ~130 byte values, about ___ keys fit before eviction starts.
- Under `noeviction`, writes return `OOM` but reads keep working.
- ...

## Interview soundbite

> "Redis eviction is approximate LRU: it samples a handful of keys and evicts the oldest of the sample. For a pure cache I set allkeys-lru; if the same instance holds keys I can't lose I give those no TTL and use volatile-lru. I never leave noeviction on a cache, because a full cache would start failing writes instead of dropping cold data."

## Cleanup

Done above.
