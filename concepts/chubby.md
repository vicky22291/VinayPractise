# Concept: Chubby

> One-liner: Chubby is Google's lock service (2006): a cell of 5 replicas elects one master with Paxos, the master serves a tiny filesystem of small files with **advisory reader/writer locks**, **sessions** kept alive by KeepAlive RPCs, **consistent client caches** invalidated by the master, and **sequencers** (fencing tokens) so a stale lock holder cannot damage anything. It exists to do coarse-grained work like electing the GFS or Bigtable master and to be the name service, and it is the design that ZooKeeper and etcd re-implemented in the open.

Depth target: high-level, same as [etcd.md](etcd.md) and [zookeeper.md](zookeeper.md). Chubby is not something you deploy; you read it because every "design a lock service / leader election / coordination store" question is Chubby's paper with the names changed, and because the paper is the best written account of what goes wrong in production with locks, caches, and sessions.

Sources: "The Chubby lock service for loosely-coupled distributed systems" (Burrows, OSDI 2006) and "Paxos Made Live" (Chandra, Griesemer, Redstone, PODC 2007), read in full. Every number in section 13 is from those two papers.

---

## 1. Mental model

A Chubby **cell** is 5 machines. One is the **master**; it holds a master lease from the others and serves every read and write. Clients talk only to the master, keep a **session** alive with KeepAlive RPCs, and cache file contents locally with the master invalidating on change. Locks are **advisory** and **coarse-grained**: held for hours or days by a primary, not milliseconds by a transaction.

```mermaid
%% Chubby in one picture: five replicas, one master, sessions, cached files, advisory locks, and the sequencer that makes locks safe
flowchart LR
    GFS["GFS / Bigtable:<br/>elect a master, publish<br/>its address in a file"]
    NS["Name service:<br/>thousands of clients<br/>read small files"]
    subgraph CELL["Chubby cell, 5 replicas, 3 must be up"]
        M["Master<br/>master lease ~12 s,<br/>serves all reads and writes"]
        R1["Replica"]
        R2["Replica"]
    end
    DB[("Replicated database<br/>WAL + snapshot,<br/>files, locks, sessions,<br/>ephemeral files")]
    CACHE["Client-side cache<br/>data, metadata, handles,<br/>absence of files<br/>invalidated by master"]
    SEQ["Sequencer<br/>lock name + mode +<br/>generation, checked<br/>by the file server"]
    FS["Downstream server<br/>(e.g. a chunk server)"]

    GFS -->|"Acquire lock on /ls/cell/gfs/master"| M
    NS -->|"KeepAlive every ~12 s,<br/>reads from cache"| M
    M -->|"Paxos: majority ack"| R1
    M -->|"Paxos: majority ack"| R2
    M --> DB
    M -->|"invalidations on KeepAlive reply"| CACHE
    GFS -->|"GetSequencer"| SEQ
    SEQ -->|"passed on every request"| FS
    FS -.->|"CheckSequencer"| M

    class GFS,NS client
    class M,R1,R2 service
    class DB store
    class CACHE cache
    class SEQ decision
    class FS external
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

- **Why a lock service and not a Paxos library.** The paper's answer: teams bolt availability onto working systems late, and "acquire a lock, write the master's address into a file" is something every programmer already understands. A consensus library would have forced them to redesign.
- **Why coarse-grained.** Lock churn is low, so the master handles tens of thousands of clients. Locks survive master fail-over so a primary is not re-elected because Chubby hiccupped.
- **Reads and writes both go to the master**, reads served from its memory under the master lease. Compare ZooKeeper, where any replica serves reads.

**Why this matters at Staff level.** Senior answers describe leader election with a lock. Staff answers cover the four things the paper spends its pages on: what a lock holder does when it cannot tell whether it still holds the lock (jeopardy, grace period), how a downstream server rejects a stale holder (sequencer, lock-delay), what a client cache promises and what it costs the master (invalidation on the KeepAlive path), and what actually caused outages and data loss over 700 cell-days (network and software, not disks).

---

## 2. Namespace, files, and handles

The interface looks like a filesystem so that existing tools work and programmers need no new concepts. `/ls/foo/wombat/pouch`: `ls` for lock service, `foo` the cell (resolved by DNS), the rest is the cell's tree.

```mermaid
%% What Chubby keeps per node. Small files, per-node ACLs, and generation numbers that change on every kind of write.
flowchart TD
    N["Node /ls/cell/service/master<br/>file or directory,<br/>permanent or ephemeral"]
    D["Contents<br/>whole-file read and write,<br/>256 KB cap added later"]
    ACL["Three ACL names<br/>read / write / change-ACL,<br/>inherited from the parent"]
    META["Metadata<br/>instance number,<br/>content generation,<br/>lock generation,<br/>ACL generation,<br/>64-bit checksum"]
    LOCK["Advisory lock<br/>exclusive (writer) or<br/>shared (reader)"]
    H["Handle<br/>from Open(), with check digits<br/>and a sequence number,<br/>events subscribed at open"]

    N --> D
    N --> ACL
    N --> META
    N --> LOCK
    H -->|"all operations go through"| N

    class N store
    class D,META store
    class ACL,LOCK service
    class H client
    classDef store   fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef client  fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
```

Deliberate omissions, each with a reason in the paper: no moves (cross-directory rename is expensive under partitioning), no path-based permissions (one lookup per file, ACL is per node), no modified time on directories, no last-access time (so the cache never has to write back), no symbolic links.

- **Ephemeral files** vanish when no client has them open (directories: when empty). They are the "I am alive" indicator, one per process, and the basis of membership.
- **Generation numbers** are the concurrency story: `SetContents` can pass a content generation and fails if the file changed; the lock generation goes into the sequencer; the instance number distinguishes a re-created node from the old one with the same name.
- The API is small: `Open`, `Close`, `Poison`, `GetContentsAndStat`, `SetContents`, `Delete`, `Acquire` / `TryAcquire` / `Release`, `GetSequencer` / `SetSequencer` / `CheckSequencer`, plus `SetACL` and `GetStat`. Whole-file operations only.

---

## 3. Sessions, KeepAlives, and the master lease

A session is a lease between client and master. The client keeps it alive with a **KeepAlive** RPC that the master deliberately **blocks** until the lease is nearly out, then answers with a new lease. Every event and cache invalidation rides back on that reply. So there is almost always one KeepAlive parked at the master per client, and RPC traffic is 93% KeepAlives.

```mermaid
%% One session over a master fail-over. The grace period is what lets a session outlive a dead master. Times from the paper's Figure 2.
sequenceDiagram
    participant C as Client library
    participant A as Application
    participant M1 as Old master
    participant M2 as New master

    C->>M1: KeepAlive (blocked at master)
    M1->>M1: commit lease M2 in the database
    M1-->>C: reply: lease extended to M2 (default +12 s, up to 60 s under load)
    Note over C,A: client keeps a conservative local lease C2 (clock rate assumption, RPC time in flight)
    C->>M1: next KeepAlive immediately
    Note over M1: old master dies, no reply
    Note over C,A: local lease C2 expires: session in jeopardy, cache flushed and disabled, grace period starts (45 s)
    C-->>A: jeopardy event: quiesce
    C->>M2: KeepAlive with old epoch (rejected, wrong epoch)
    Note over M2: elected after 4 to 6 s typical, up to 30 s seen
    M2->>M2: extend every session lease to the max the old master could have granted
    C->>M2: KeepAlive with new epoch
    M2-->>C: lease C3, fail-over event
    C-->>A: safe event: session recovered, rescan data, events may have been lost
    Note over C,M2: had the grace period elapsed first: expired event, handles and locks gone
```

- **Jeopardy** is the honest state: the client's own lease ran out and it cannot tell whether the master expired the session. It stops trusting its cache and warns the application. If a KeepAlive succeeds within the **grace period (45 s)**, the application saw only a delay; if not, the session is **expired** and every lock and ephemeral file is gone.
- **Master lease.** The master holds a lease from a majority of replicas (renewed as long as it keeps winning votes) so it can serve reads from memory alone: no other master can exist while the lease is valid. Election happens only after the lease expires, which bounds fail-over at lease plus election.
- **Lease length is the load knob.** Under heavy load the master stretches leases from 12 s toward 60 s so it processes fewer KeepAlives. Failing to answer KeepAlives in time is the typical symptom of an overloaded master.
- Compare ZooKeeper: same session idea, but ZooKeeper's client pings on a timer and the cluster expires; Chubby's KeepAlive is the transport for everything, so a client cannot keep its session without also acknowledging invalidations.

---

## 4. Consistent client cache

Clients cache file data, metadata, open handles, and even the **absence** of files (negative caching, 32k entries in the sample cell), all in memory, with a lease. The master keeps a list of who might cache what and invalidates on change; it never pushes updates.

```mermaid
%% Write path with cache invalidation. The write blocks until every possible cacher has acknowledged or let its lease lapse. One round, because the node is uncachable meanwhile.
sequenceDiagram
    participant W as Writer
    participant M as Master
    participant C1 as Client 1 (cached)
    participant C2 as Client 2 (cached, slow)

    W->>M: SetContents(/svc/master, addr)
    M->>M: mark node uncachable, record write
    M-->>C1: invalidation on KeepAlive reply
    C1->>M: flush, ack via next KeepAlive
    M-->>C2: invalidation on KeepAlive reply
    Note over C2: no ack within its cache lease
    Note over M: proceeds when every client acked or its lease expired
    M-->>W: write complete
    C1->>M: GetContentsAndStat (cache miss, node cacheable again)
    M-->>C1: new contents, cached
```

- The cache is **strictly consistent**: a client never reads stale data from it, because the write does not complete until all cachers have dropped it. The paper calls this "heavyweight" and says it is why Chubby is a bad pub/sub system.
- Handles are cached too: reopening a file you already opened costs no RPC. Locks can be cached as well, held until another client's conflicting request produces an event.
- Cost: one slow client delays every writer of that file for up to a cache lease. Mitigation in the paper: piggybacking invalidations on KeepAlives means a client cannot stay alive while ignoring them.
- This is where DNS-style TTL caching was rejected: TTLs either make the name service slow to update or hammer the master. Invalidation gives immediate updates at the cost of tracking cachers.

---

## 5. Locks, sequencers, and lock-delay

Locks are advisory: holding `/foo` does not stop anyone reading `/foo`, it only stops others from *acquiring* the lock. The hard problem is not mutual exclusion inside Chubby, it is the **delayed message from a client that lost the lock** arriving at some other server.

```mermaid
%% The stale-holder problem and the two answers: sequencers for servers you can modify, lock-delay for the ones you cannot
sequenceDiagram
    participant A as Primary A
    participant CH as Chubby
    participant B as Primary B
    participant S as File server

    A->>CH: Acquire(/svc/primary, exclusive)
    CH-->>A: held, lock generation 7
    A->>CH: GetSequencer()
    CH-->>A: seq {name, exclusive, gen 7}
    A->>S: write X (seq gen 7) ... delayed in the network
    Note over A,CH: A's session expires (GC pause, partition)
    Note over CH: lock-delay: keep the lock unclaimable for up to 60 s if A did not release cleanly
    B->>CH: Acquire(/svc/primary, exclusive)
    CH-->>B: held, lock generation 8
    B->>S: write Y (seq gen 8)
    S->>CH: CheckSequencer(gen 8) or compare with the highest seen
    S-->>B: OK
    A->>S: the delayed write X (seq gen 7) finally arrives
    S-->>A: rejected, gen 7 < gen 8
```

- A **sequencer** is an opaque string: lock name, mode, lock generation. The holder passes it on every request to servers that guard the resource; the server checks it against Chubby (or against the highest sequencer it has seen) and rejects anything older. This is the fencing token from [leases-fencing-clocks.md](leases-fencing-clocks.md), and the paper is where the idea was published.
- **Lock-delay** is the fallback for servers you cannot modify: if a lock is freed because the holder died rather than released, nobody can take it for up to a minute. It reduces the window for delayed messages; it does not close it.
- **Coarse-grained by design.** Few clients hold locks (1k exclusive, 0 shared in the sample cell). Fine-grained locking is left to the application, which can use one Chubby lock to elect a server that then hands out its own cheap locks. Lock loss on Chubby fail-over is acceptable because it is rare; lock loss on every network blip would not be.

Primary election in four lines, from the paper: all candidates `Acquire` the same lock; the winner writes its identity into the file with `SetContents`; the others read the file (with a modification event) to find the primary; the primary gets a sequencer and its servers `CheckSequencer` it, or use a lock-delay.

---

## 6. Events

Subscribed at `Open`, delivered asynchronously after the change has taken effect (so a client that reads after the event sees the new state):

| Event | Used for |
|---|---|
| File contents modified | "The primary's address changed", the name service |
| Child added / removed / modified | Membership via ephemeral files, mirroring, without holding the children open |
| Master failed over | "You may have missed events, rescan" |
| Handle or lock invalid | Usually a communication problem |
| Lock acquired, conflicting lock request | Rarely used; the paper says they could have been omitted, clients wait for the file write instead |

Events are a notification that something changed, not the change itself. Same design conclusion as ZooKeeper's one-shot watch: re-read after the event.

---

## 7. Under the hood: replicas, Paxos, database, fail-over

```mermaid
%% Inside a cell. Paxos replicates the database log; the master alone talks to clients; DNS carries the replica list.
flowchart LR
    DNS["DNS: replica list<br/>for cell foo"]
    CL["Client library<br/>master location request,<br/>then everything to the master"]
    subgraph CELL["Cell: 5 replicas in separate racks"]
        M["Master<br/>elected by Paxos,<br/>holds master lease"]
        R1["Replica 1"]
        R2["Replica 2"]
        R3["Replica 3"]
        R4["Replica 4"]
    end
    LOG[("Paxos-replicated log<br/>one disk write per instance,<br/>batched, then snapshot")]
    GFS[("GFS: snapshot backup<br/>every few hours, other building")]
    REP["Replacement machine<br/>from the free pool,<br/>DNS updated, catches up"]

    CL -->|"lookup"| DNS
    CL -->|"all RPCs"| M
    M -->|"propose"| R1
    M -->|"propose"| R2
    M -->|"propose"| R3
    M -->|"propose"| R4
    M --> LOG
    M -.->|"backup"| GFS
    R4 -.->|"dead for hours"| REP

    class DNS,CL client
    class M,R1,R2,R3,R4 service
    class LOG,GFS store
    class REP cache
    classDef client  fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store   fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache   fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
```

- **Consensus**: Multi-Paxos with a master lease, see [paxos.md](paxos.md). Writes are acknowledged when a majority has them. Reads never touch the replicas. A replica dead for a few hours is replaced from a free pool and DNS is updated; the new one catches up from the log.
- **Database**: first the replicated version of Berkeley DB (path-name keys sorted so siblings are adjacent), then, because its replication code was young and Chubby needed only atomic operations, a purpose-built WAL plus snapshot store on top of their own Paxos. "Paxos Made Live" is that rewrite: one disk write per Paxos instance on each replica (not five), batching, master leases, snapshots with a "snapshot handle" tying the app snapshot to the log position, and a corrupted-disk replica that rejoins as a non-voter until it has caught up. Their benchmark: 640 ops/s at 20 workers on 5-byte files, 3.6x the Berkeley DB version.
- **Backup**: every few hours the master writes a database snapshot to GFS in a different building.
- **Mirroring**: a global cell (replicas spread across distant datacenters) holds config that is mirrored into every local cell; the event mechanism keeps mirrors current within seconds.

### 7.1 Fail-over, the part with "a rich source of interesting bugs"

```mermaid
%% The new master's nine steps, condensed. The database holds sessions, locks and ephemerals; the rest is rebuilt conservatively.
flowchart TD
    E["Old master's lease expires,<br/>replicas elect a new master<br/>(4 to 6 s typical, 30 s seen)"]
    S1["1. New client epoch number:<br/>every call must carry it,<br/>old-epoch packets rejected"]
    S2["2. Answer master-location only"]
    S3["3. Rebuild sessions and locks<br/>from the database, extend every<br/>lease to the max the old<br/>master could have granted"]
    S4["4. Accept KeepAlives only"]
    S5["5. Send fail-over event: clients<br/>flush caches, apps told<br/>events may be lost"]
    S6["6. Wait for every session to<br/>ack or expire"]
    S7["7. All operations allowed,<br/>old handles recreated on use"]
    S8["9. After ~1 minute, delete<br/>ephemeral files nobody<br/>reopened"]

    E --> S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8

    class E critical
    class S1,S2,S3,S4,S5,S6,S7,S8 service
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
```

- **Client epoch** is the master's fencing token against its own past: a packet sent to a previous master, even one on the same machine, is rejected.
- **Conservative lease extension** is why sessions survive fail-over: the new master cannot know what the old one promised, so it assumes the maximum.
- The original design wrote every new session to the database, which melted under start-up storms; they changed it to write a session on its first modification, lock, or ephemeral open. Read-only sessions then cost nothing durable. Proxies made this worse, because a proxy's sessions look like one client to the master (section 8).

---

## 8. Scaling a cell: 90,000 clients on one master

Chubby's clients are **processes**, not machines. One cell per datacenter of several thousand machines sees tens of thousands of sessions on one master that is an ordinary machine. So every scaling trick reduces traffic to the master rather than speeding it up.

```mermaid
%% Four levers, all of which cut master traffic. Proxies divide KeepAlives and reads by Nproxy; partitioning divides everything by N but keeps one master per partition.
flowchart LR
    C["90k client processes<br/>in one datacenter"]
    P["Proxies<br/>hold one session to the master<br/>on behalf of many clients,<br/>KeepAlives and reads cut<br/>by a factor of Nproxy"]
    CA["Client cache<br/>data, metadata, handles,<br/>absence of files"]
    L["Longer leases<br/>12 s to 60 s under load:<br/>fewer KeepAlives"]
    PART["Partitioning<br/>N partitions per cell,<br/>node D goes to<br/>hash(parent of D) mod N"]
    M["One master<br/>1 to 2k RPC/s,<br/>93% KeepAlive,<br/>overload above ~90k sessions"]
    LIM["Cross-partition ops:<br/>ACLs, directory delete,<br/>still touch several masters"]

    C -->|"~10% of load: reads"| CA
    C -->|"sessions"| P
    P -->|"one session per proxy"| M
    CA -->|"misses only"| M
    L -.-> M
    PART -.-> M
    PART -.-> LIM

    class C client
    class P,L,PART service
    class CA cache
    class M critical
    class LIM decision
    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

- The master is the red node by construction: one process, ordinary hardware, every read and write. The paper is explicit that micro-optimising it "has little effect"; only cutting traffic does.
- **Proxies** are trusted and can answer KeepAlives and reads themselves; writes and lock operations still go through (under 1% of load). A proxy that dies takes many sessions into jeopardy at once, which is the fail-over interaction they call out.
- **Partitioning** was designed and never needed in practice. Its rule keeps siblings together (hash the parent) so directory listing stays local.
- Naming turned out to be the dominant use: 60% of open files are name-related. The consistent cache was heavier than a name service needs, so they added a protocol-conversion name server and a DNS front end.

---

## 9. What went wrong: the lessons section

The paper's best part. Each of these is a Staff-level interview answer waiting to happen.

| Surprise | What happened | What they did |
|---|---|---|
| Developers do not plan for unavailability | Apps assumed Chubby, especially the global cell, was always up; a Chubby outage became their outage | Review every planned use, inject artificial outages, make the client library keep working through short outages |
| No quotas | One team rewrote a 1.5 MB file on every user action until it dwarfed every other client | 256 KB file size limit; it took about a year to move the data out |
| Pub/sub attempts | The invalidation cache makes Chubby slow for anything but trivial fan-out | Caught in review |
| Abusive clients | Loops that call `Open` in a tight loop, or that never close handles | Artificial delays in `Open`, review of RPC rates and file counts |
| Java clients | JNI wrapper for the C library was slow and awkward; teams avoided it | Kept the C library as the single implementation |
| Fail-over cost | Writing every new session durably melted under start-up storms; proxies multiplied sessions | Sessions recorded on first write or lock; rethink proxy fail-over |
| Fine-grained locks | Expected demand, never materialised | Not built |
| Outages | 61 in 700 cell-days; most under 15 s, 52 under 30 s; the long nine were network maintenance (4), network (2), software (2), overload (1) | Apps tolerate 30 s; the client library's grace period is 45 s |
| Data loss | 6 times in a few dozen cell-years: 4 database software bugs, 2 operator errors during upgrades to fix those bugs, 0 hardware | Rewrote the database on their own Paxos; runtime consistency checks (Paxos Made Live) |

---

## 10. Failure modes and what pages you

| Failure | Behaviour | Design response |
|---|---|---|
| Master dies | Master lease expires, election 4 to 6 s typical, up to 30 s. Sessions survive via grace period. Locks survive | Grace period 45 s > worst election; clients quiesce on jeopardy |
| Client cannot reach master for > local lease | Jeopardy: cache disabled, app warned. If > grace period: expired, locks and ephemerals lost | Fencing with sequencers, lock-delay for legacy servers |
| Master overloaded (> 90k sessions, read storms) | KeepAlives answered late, sessions dropped in bulk | Longer leases, proxies, client cache, review of abusive clients |
| One slow cacher | Delays every write to that file for up to one cache lease | Invalidation on KeepAlive path, so an alive client must ack |
| Replica dies | Majority continues; replaced within hours from the free pool via DNS | Five replicas, three needed |
| Datacenter loses the cell | Everything that used it as a name service or lock root stalls | Local cell per DC, global cell mirrored, apps must tolerate ~30 s |
| Database corruption on a replica | Detected by checksum / GFS marker; replica rejoins as a non-voter and catches up | Paxos Made Live section 5.1 |
| Delayed packet from an old master or old client | Rejected by client epoch / master epoch | Epoch numbers on every call |

---

## 11. Chubby, ZooKeeper, etcd

```mermaid
%% Three generations of the same design. The arrows are what each one changed.
flowchart LR
    CH["Chubby (2006, Google)<br/>Paxos, master serves all reads,<br/>consistent client cache,<br/>sessions via KeepAlive,<br/>advisory locks + sequencers"]
    ZK["ZooKeeper (2008, Yahoo)<br/>Zab, any replica serves reads,<br/>no client cache, one-shot watches,<br/>sessions via ping, ephemeral<br/>sequential nodes for locks"]
    ET["etcd (2013, CoreOS)<br/>Raft, MVCC revisions,<br/>resumable watch stream,<br/>leases per key, Txn CAS,<br/>gRPC, revision as fencing token"]

    CH -->|"drop the cache, serve reads<br/>locally (faster, stale),<br/>watches instead of invalidations"| ZK
    ZK -->|"add history: revisions,<br/>watch from any point,<br/>flat keys, leases not sessions"| ET

    class CH,ZK,ET service
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
```

| | Chubby | ZooKeeper | etcd |
|---|---|---|---|
| Consensus | Multi-Paxos + master lease | Zab | Raft |
| Reads | Master only, from memory under lease | Any server, local, may be stale | Linearizable via ReadIndex, or local serializable |
| Client cache | Consistent, master-invalidated | None in the protocol | None in the protocol |
| Liveness | Session, KeepAlive blocked at master | Session, client ping | Lease, keepalive stream |
| Change notice | Events on handle | One-shot watches | Watch stream from a revision |
| Locks | First-class advisory locks, shared / exclusive | Recipe on sequential ephemerals | Recipe on Txn + lease |
| Fencing token | Sequencer (name, mode, generation) | Sequence number, `czxid` | `revision`, `create_revision` |
| Stale-holder fallback | Lock-delay up to 60 s | None | None |
| Scale unit | One cell per DC, ~90k sessions | Ensemble + observers | One cluster, ~50k writes/s |
| Where | Google internal | Hadoop, HBase, Kafka < 4.0 | Kubernetes, CNCF |

---

## 12. When you meet it in an interview

Chubby is the answer key for:

- **Design a distributed lock service** (#33): section 3 (sessions, jeopardy, grace), section 5 (sequencers, lock-delay), section 7.1 (fail-over with epochs), section 8 (why one master and how to keep it alive).
- **Leader election for GFS / a file system master** (#3): acquire the lock, write the address into the file, everyone else watches the file, servers check the sequencer.
- **Name service / service discovery**: consistent cache vs TTL, and why the paper ended up adding a DNS front end anyway.
- **Coordination store sizing**: KeepAlive-dominated load, lease length as the throttle, proxies before partitioning.

What a Staff answer refuses to build, quoting the paper: fine-grained locks in the lock service, mandatory locks, a pub/sub system on the event mechanism, a storage system in the lock service (256 KB), and a fail-over design that writes every session durably.

---

## 13. Numbers worth memorizing

- Cell: **5 replicas**, **3 must be up**; typically **one cell per datacenter** of several thousand machines, plus a **global cell** spread across datacenters.
- Master lease and session lease default **12 s**, stretched up to **~60 s** under load. Grace period **45 s**. Lock-delay bound **1 minute**.
- Master election **4 s and 6 s** in two recent cases, **up to 30 s** observed; sample cell fail-over duration **14 s**.
- Sample cell: **22k** direct clients, **32k** proxied, **12k** open files (60% naming), **230k** client-cache entries for **24k** distinct files (~10 clients per file), **32k** negative-cache entries, **1k** exclusive locks, **0** shared, **8k** directories, **22k** files (90% under 1 KB), RPC **1 to 2k/s**, **93%** KeepAlive, **2%** GetStat, **1%** Open, **0.4%** SetContents, Acquire **31 ppm**.
- Scale: up to **90,000** clients on one master; overload above that. Mean latency "a small fraction of a millisecond" until overload.
- Outages: **61** in **700 cell-days**, most **≤ 15 s**, **52 < 30 s**; apps tolerate **30 s**. Data loss **6** times in a few dozen cell-years (4 software, 2 operator, 0 hardware).
- File size cap **256 KB** (after a 1.5 MB file rewritten per user action). Reads under **10%** of load; proxies cut KeepAlives and reads by **Nproxy**; partitioning by **hash(parent) mod N**.
- Paxos Made Live: **one** disk write per Paxos instance per replica instead of five; **640 ops/s** at 20 workers on 5-byte files vs 178 on the Berkeley DB version (3.6x); 100 MB database.

---

## 14. Interview soundbite

> "Chubby is a lock service: five replicas run Paxos to elect a master with a lease, the master serves a small filesystem out of memory, and clients hold sessions kept alive by KeepAlive RPCs that the master blocks and uses to carry cache invalidations. Locks are advisory and coarse-grained, held by a primary for its whole life. The two ideas I carry into any design: when my session lease runs out I am in jeopardy, so I stop trusting my cache and wait a grace period before I assume I lost the lock; and I never let a lock be the only protection, I hand every downstream server a sequencer, the lock's generation number, and it rejects anything older, with a lock-delay as a fallback for servers I cannot change. Operationally the master is the bottleneck by design: ninety thousand sessions, ninety-three percent of RPCs are KeepAlives, so the levers are longer leases, client caching, and proxies, not a faster master. The paper's own lessons: apps do not plan for outages, so I test with injected ones; there were no quotas, so I add them on day one; and the data loss they saw came from software and operators, never disks."

Follow-ups an interviewer will ask, in order of likelihood:

1. The lock holder pauses and its session expires. How do you stop its late writes? (Section 5, sequencer; lock-delay if the server cannot check.)
2. Why is the master the only reader? (Section 3, master lease makes memory reads safe; section 8, the cost is that it is the bottleneck.)
3. What happens to sessions and locks when the master dies? (Section 3 and 7.1, grace period, conservative lease extension, epochs.)
4. Why a lock service rather than a Paxos library? (Section 1, teams add availability late; locks are a known concept.)
5. Why coarse-grained? (Section 5, low churn, survive fail-over, fine-grained belongs to the app.)
6. How does the client cache stay consistent, and what does it cost? (Section 4, invalidation before write completes, one slow client delays writers.)
7. How do you scale to 90k clients? (Section 8, leases, cache, proxies, then partitioning.)
8. What actually caused outages? (Section 9, network and software; 30 s tolerance.)
9. Chubby vs ZooKeeper vs etcd for a new system? (Section 11, etcd; the differences are read path, cache, and history.)
10. What would you leave out? (Section 12, fine-grained locks, mandatory locks, pub/sub, large files.)

Related: [paxos.md](paxos.md) (the consensus underneath, and Paxos Made Live's engineering), [zookeeper.md](zookeeper.md) and [etcd.md](etcd.md) (the open-source descendants), [leases-fencing-clocks.md](leases-fencing-clocks.md) (sequencer = fencing token, jeopardy = lease expiry handling), [caching-patterns.md](caching-patterns.md) (invalidation vs TTL, the name-service trade-off), `hld/distributed-file-system/` (GFS master election is the canonical use), `hld/distributed-job-scheduler/` (partition ownership with epochs).
