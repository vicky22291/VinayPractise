# Cross-System Patterns

<!-- nav:start -->
**[Index](README.md)** · [Kubernetes 00 Overview](kubernetes-00-overview.md) · Sibling catalogues: [Cassandra](../cassandra/patterns.md) · [Kafka](../kafka/patterns.md)
<!-- nav:end -->

A running catalogue of recurring distributed-systems patterns, the mechanism behind each, and which studied systems use it. Seeded from the Kubernetes deep dives (`systems/kubernetes-*.md`); extend a row rather than adding a duplicate pattern when a new system is added.

**Systems covered so far:** Kubernetes (all subsystems), etcd. Entries under *Elsewhere* for systems not yet deep-dived are pointers for future reports, not verified findings from this project.

---

## 1. Consensus and replication

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Raft consensus** | Leader-based log replication; entries committed once a quorum acks; leader elected by randomized timeouts | etcd — the entire cluster state sits behind one Raft group ([report 01](kubernetes-01-apiserver-etcd.md)) | Consul, TiKV, CockroachDB, Kafka KRaft, Spanner (Paxos per split) |
| **Quorum reads (ReadIndex)** | Leader confirms it is still leader via a heartbeat round before serving a read, avoiding a log write | etcd linearizable reads; kube-apiserver uses them when `resourceVersion=""` | Consul consistent reads, Zookeeper `sync()`, Spanner reads at TrueTime |
| **Single Raft group as a scaling ceiling** | All writes serialize through one leader; capacity is one node's fsync throughput | etcd, hence the 5,000-node envelope; mitigated by `--etcd-servers-overrides` splitting Events onto a second etcd | Contrast: Spanner, CockroachDB and TiKV shard into many Raft groups; Kafka partitions per topic |
| **Leader election as an optimisation, not a lock** | Lease renewed before expiry; no fencing token validated by the resource being guarded | `coordination.k8s.io/Lease` for kube-controller-manager, kube-scheduler, CSI sidecars ([report 02](kubernetes-02-controllers.md)). A stalled leader can still write | Chubby and Zookeeper *do* issue fencing tokens; HDFS NameNode uses epoch numbers. Kubernetes deliberately relies on idempotence instead |

**Key judgement.** Kubernetes accepted a single-Raft-group ceiling in exchange for a strictly serialisable, watchable, whole-cluster keyspace. Every scaling limit in section 9 of the reports traces back to that one bet.

---

## 2. Storage engines and on-disk structures

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Write-ahead log** | Append durably, then apply to the in-memory/paged structure; replay on restart | etcd WAL, fsynced before Raft commit ([report 01](kubernetes-01-apiserver-etcd.md)) | Postgres WAL, Kafka segments, Cassandra commitlog, InnoDB redo log, RocksDB WAL |
| **B+tree page store** | Copy-on-write B+tree with a freelist; random reads cheap, writes amplify | etcd's bbolt backend; fragmentation requires `defrag` to return space to the filesystem | Postgres/InnoDB heaps+indexes; contrast LSM trees below |
| **LSM tree** | Buffer writes in memtables, flush to sorted files, compact in the background | *Not used by etcd* — a notable divergence from most modern KV stores | RocksDB, Cassandra, HBase, ScyllaDB, TiKV, BigTable |
| **MVCC with a monotonic revision** | Every mutation gets a global revision; old versions readable until compacted | etcd revisions are exposed to clients as `resourceVersion`; the whole watch protocol depends on them | Postgres xmin/xmax, Spanner timestamps, CockroachDB MVCC |
| **Compaction vs reclamation as separate steps** | Logical version removal ≠ physical space return | etcd `compact` (drops old revisions) then `defrag` (shrinks the file). Forgetting the second causes `database space exceeded` | Postgres VACUUM vs VACUUM FULL; Cassandra tombstones vs compaction |
| **Hard size quota with an alarm** | Refuse writes rather than degrade unboundedly | etcd `--quota-backend-bytes`, 2 GiB default, NOSPACE alarm puts the cluster read-only | Kafka log retention, S3 bucket quotas — but few systems fail this hard, which is why the etcd alarm surprises people |

---

## 3. Control and coordination

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Level-triggered reconciliation** | Act on current observed state, not on the delivered event; loops are idempotent and convergent | The core model. Every controller, the kubelet syncLoop, kube-proxy's rule sync (reports 02, 04, 05) | Terraform plan/apply, Chef/Puppet, ArgoCD, AWS Auto Scaling groups. Contrast: Airflow/Step Functions, which are edge-triggered workflows |
| **Declarative desired state + observed status** | Split one object into `spec` (intent, user-owned) and `status` (reality, controller-owned) | Every Kubernetes object; `metadata.generation` vs `status.observedGeneration` closes the loop | Crossplane, Cluster API, and increasingly cloud APIs (GCP Config Connector, AWS Controllers for K8s) |
| **Optimistic concurrency control** | Compare-and-swap on a version; retry on conflict; never lock | `resourceVersion` on every write; etcd `Txn` with `ModRevision` compare; HTTP 409 to the client | DynamoDB conditional writes, S3 preconditions, Git refs, Cassandra LWT |
| **Watch + resume token** | Long-lived stream of changes keyed by a position, plus a defined "you fell too far behind" error | Kubernetes watch with `resourceVersion`; `410 Gone / too old resource version` forces a relist | Kafka consumer offsets, MongoDB change streams, DynamoDB Streams, Postgres logical replication slots |
| **Bounded history buffer** | Keep a fixed window of recent changes in memory to serve late/slow readers | apiserver watch cache ring buffer (100 → 102,400 entries); scheduler's event-based requeue | Kafka retention window, Redis replication backlog |
| **Expectations / in-flight accounting** | Controller records what it just asked for so it does not re-issue before the cache catches up | `UIDTrackingControllerExpectations` in the ReplicaSet controller ([report 02](kubernetes-02-controllers.md)) | Any actor-model system's outstanding-request table; TCP's in-flight window is the same idea |

---

## 4. Caching and staleness

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Read-through cache in front of the datastore** | One reader populates a shared cache; many consumers served from RAM | apiserver watch cache (one reflector per resource, thousands of watchers) | CDN origin shielding, DB read replicas, Facebook's leases in Memcache |
| **Client-side replicated cache** | Every consumer maintains a full local mirror via list+watch | client-go informers in every controller, kubelet, kube-proxy ([report 02](kubernetes-02-controllers.md)) | Envoy xDS state-of-the-world, ZooKeeper watches, Consul agent caches |
| **Deliberately stale cache with a safety backstop** | Accept staleness, then revalidate at the point where being wrong is expensive | Scheduler snapshot is stale → kubelet re-runs admission and can reject the pod (reports 03, 04) | TLB + page fault; browser cache + conditional GET; optimistic UI with server reconciliation |
| **Assume-then-confirm** | Mutate the local cache before the authoritative write lands; unwind on failure | Scheduler `AssumePod` / `FinishBinding` / `ForgetPod`; `Unreserve` on bind failure | Optimistic UI updates, speculative execution, DB write-behind caches |
| **Relist storms / thundering herd** | Many clients simultaneously lose their position and re-read everything | apiserver restart → every informer relists; mitigated by jittered resync, `WatchList` streaming, APF | Cache stampede on TTL expiry; the standard mitigations (jitter, request coalescing) apply identically |

---

## 5. Flow control and back-pressure

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Fair queuing with shuffle sharding** | Hash each flow into a random subset of queues so one heavy flow rarely collides with any given light one | API Priority and Fairness: FlowSchema → PriorityLevel → shuffle-sharded queues + seats ([report 01](kubernetes-01-apiserver-etcd.md)) | AWS shuffle sharding (Route 53, ELB), Linux SFQ, Google's Slicer |
| **Admission shedding before expensive work** | Reject or queue at the cheapest point in the pipeline | APF runs *before* authorization in the apiserver handler chain | Envoy admission control, TCP SYN cookies, database connection pools |
| **Client-side rate limiting** | Callers self-limit to protect a shared server | `--kube-api-qps` / `--kube-api-burst` on every control-plane component and controller | gRPC client throttling, AWS SDK adaptive retry mode |
| **Exponential backoff with a dedup queue** | Failures requeue with growing delay; duplicate keys collapse | client-go `workqueue` (dirty/processing sets, 5ms→1000s exponential limiter, 10 qps/100 burst bucket); scheduler backoffQ (1s→10s) | SQS visibility timeout + DLQ; Celery retries; any well-behaved retry loop |
| **Event-driven requeue instead of periodic polling** | Wake a blocked item only when something that could unblock it changes | Scheduler QueueingHint / `EventsToRegister` replacing the 5-minute unschedulable flush ([report 03](kubernetes-03-scheduler.md)) | Epoll vs busy-wait; condition variables; database triggers vs cron |

---

## 6. Failure detection and recovery

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Lease-based liveness** | Renew a small object frequently; absence of renewal means "presumed dead" | Node Lease renewed every 10s in `kube-node-lease`; node-lifecycle controller reacts after the grace period (reports 02, 04) | Chubby/Zookeeper sessions, Consul TTL checks, DynamoDB lock client |
| **Separate heartbeat from full status** | A cheap frequent signal plus an expensive infrequent one | Node Lease (tiny, 10s) vs full Node status update (large, 5m) — this split is what made 5,000-node clusters viable | Gossip heartbeats vs full state exchange in Cassandra; BGP keepalives vs full route refresh |
| **Rate-limited mass eviction** | Cap how fast a detected failure can cascade into workload movement | node-lifecycle controller's eviction rate limits, `--large-cluster-size-threshold`, secondary rate for unhealthy zones | Circuit breakers; AWS ASG health-check grace; any "don't let the detector cause the outage" control |
| **Polling as a health proxy** | A loop whose own latency is the signal | PLEG `relist` every 1s; `PLEG is not healthy` after 3 minutes marks the node NotReady ([report 04](kubernetes-04-kubelet-node-runtime.md)) | Watchdog timers, heartbeat threads in JVM GC detection |
| **Cooperative deletion with finalizers** | Object marked for deletion; removal blocked until every registered party acks | `deletionTimestamp` + `metadata.finalizers`; the garbage collector's foreground/background propagation ([report 02](kubernetes-02-controllers.md)) | Two-phase resource teardown in Terraform; reference counting; the classic failure mode is the same — one absent party wedges everything |

---

## 7. Extension and isolation

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Out-of-process plugin at the trust boundary** | Third-party code runs in its own process, reached over a narrow RPC | CRI (containerd), CNI (exec'd binaries), CSI (gRPC over unix socket), DRA device plugins (reports 04, 05, 06) | Envoy's ext_authz/ext_proc, PAM/NSS, Postgres FDW, browser extension sandboxes |
| **Sidecar adapter owning the API glue** | Vendor implements only the domain logic; a first-party sidecar translates Kubernetes objects into plugin calls | CSI `external-provisioner`, `external-attacher`, `external-resizer`, `external-snapshotter`, `node-driver-registrar` | Service mesh sidecars; the Adapter pattern generally |
| **Interception hooks with a declared failure policy** | Extension points that can block writes must declare what happens when they are unavailable | Admission webhooks' `failurePolicy: Fail|Ignore`; the deadlock when a webhook gates its own pods ([report 07](kubernetes-07-extensibility-security.md)) | Circuit-breaker fallbacks; fail-open vs fail-closed in auth proxies |
| **In-process policy language over remote hooks** | Move the common case into a sandboxed expression language to remove a network hop and an availability dependency | CEL `ValidatingAdmissionPolicy` / `MutatingAdmissionPolicy` replacing many webhooks | eBPF replacing userspace packet handlers; WASM filters in Envoy; SQL check constraints vs application validation |
| **Schema-first user extension** | Users add types to the existing store rather than running a new server | CRDs with structural schemas, versioning, conversion webhooks, `x-kubernetes-list-type` driving merge semantics | Postgres custom types; Salesforce custom objects; contrast aggregated API servers, which are a full new backend |

---

## 8. Scheduling and placement

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Monolithic scheduler with a cached cluster view** | One process, one decision at a time, over a snapshot | kube-scheduler: single-threaded scheduling cycle, concurrent binding ([report 03](kubernetes-03-scheduler.md)) | Borg (the direct ancestor); contrast Mesos two-level offers and Omega shared-state optimistic |
| **Filter-then-score (feasibility then preference)** | Reduce to feasible candidates, then rank; never score infeasible nodes | Scheduling Framework PreFilter/Filter → PreScore/Score/NormalizeScore | SQL query planning (predicate pushdown then cost model); ad serving retrieval + ranking |
| **Sampling instead of full evaluation** | Stop after examining enough candidates to make a good-enough decision | `percentageOfNodesToScore` (adaptive, floor 5%, minimum 100 nodes), with a round-robin start index for fairness | Power of two choices; Sparrow's batch sampling; ML candidate generation |
| **Priority + preemption with a minimality search** | High-priority work displaces low-priority work, choosing the least-damaging victim set | DefaultPreemption PostFilter: remove all lower-priority pods, then reprieve one at a time respecting PDBs | Borg priority bands; YARN preemption; OS process priorities with nice/OOM score |
| **Nomination without binding** | Reserve intent on a node without committing, so the decision can be revisited | `status.nominatedNodeName` after preemption — the pod re-competes next cycle | Two-phase commit's prepare phase, but deliberately abandonable |

---

## 9. Dataplane and networking

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Control plane programs a local dataplane** | Central intent, per-node enforcement, eventually consistent | kube-proxy translating Services + EndpointSlices into iptables/IPVS/nftables/eBPF rules ([report 05](kubernetes-05-networking.md)) | Envoy + xDS, OpenFlow controllers, BGP route reflectors |
| **Full-state resync over incremental patching** | Recompute the whole ruleset and apply atomically rather than diffing | kube-proxy's `iptables-restore` of the entire table; `--minSyncPeriod` to bound the cost | Terraform apply, Envoy state-of-the-world xDS, DNS zone transfers (AXFR vs IXFR) |
| **O(n) rule chains as a scaling wall** | Linear match cost per packet as the object count grows | iptables mode at 10k+ Services; solved by IPVS hashing and nftables verdict maps (100k endpoints: ~88.5s vs ~1.4s sync) | Linear ACL evaluation in firewalls; the general fix is always a hash/trie/map |
| **Sharding a large collection into bounded objects** | Split one hot object into many small ones to bound watch payloads | EndpointSlice (100 endpoints per slice) replacing the single Endpoints object | Kafka partitions; DynamoDB item size limits driving fan-out tables |
| **Connection tracking as hidden state** | The dataplane keeps per-flow state that outlives the control-plane object | conntrack entries surviving endpoint removal — the reason rolling updates drop connections | NAT gateways, stateful firewalls, load balancer connection draining |

---

## 10. Resource management

| Pattern | Mechanism | In Kubernetes | Elsewhere |
|---|---|---|---|
| **Request/limit split** | One number for admission and share allocation, another for enforcement | requests → scheduling + `cpu.weight`; limits → CFS quota and OOM kill (reports 04, 08) | Borg's requested vs limit; JVM `-Xms`/`-Xmx`; cgroups generally |
| **Service classes from resource shape** | Derive a QoS tier from the request/limit relationship rather than a separate field | Guaranteed / Burstable / BestEffort, driving cgroup placement and `oom_score_adj` | Diffserv in networking; storage tiers; AWS burstable instance families |
| **Local pressure eviction ranked by contract** | The node sheds load itself, worst-behaved tenant first | kubelet eviction manager: rank by QoS, then usage over request, before the kernel OOM killer intervenes | Load shedding in RPC servers; Linux OOM score; airline overbooking |
| **Reactive utilisation autoscaling with damping** | Ratio-based target tracking plus a stabilisation window to prevent oscillation | HPA `ceil(replicas × current/target)`, 10% tolerance, 300s scale-down stabilisation ([report 08](kubernetes-08-autoscaling-and-scale.md)) | AWS target-tracking scaling; thermostat control loops; TCP congestion control |
| **Disruption budgets as a safety interlock** | Voluntary operations must ask permission; involuntary ones ignore it | PDBs enforced by the Eviction API but not by node-pressure eviction or a raw DELETE | Maintenance windows; Chubby's "at most N down"; Cassandra's `nodetool drain` conventions |

---

## Open questions to revisit as more systems are added

- **Where else does "level-triggered wins" hold, and where does it fail?** It requires cheap full-state reads. Kafka and Spanner cannot use it for the data path — is the boundary exactly "control plane vs data plane"?
- **Fencing tokens.** Kubernetes is the outlier in *not* having them. Compare against Chubby, HDFS and Kafka's producer epoch when those reports exist, and characterise precisely what class of side effect makes their absence unacceptable.
- **Single Raft group vs sharded consensus.** Compare etcd's ceiling against Spanner's per-split Paxos and CockroachDB's range leases; quantify the operational cost of the sharded design.
- **B+tree vs LSM for a metadata store.** etcd chose bbolt. Compare against ZooKeeper (in-memory + snapshots) and TiKV (RocksDB) on read latency, write amplification and compaction pauses.

---

<!-- nav:start -->
**[Index](README.md)** · [Kubernetes 00 Overview](kubernetes-00-overview.md) · Sibling catalogues: [Cassandra](../cassandra/patterns.md) · [Kafka](../kafka/patterns.md)
<!-- nav:end -->
