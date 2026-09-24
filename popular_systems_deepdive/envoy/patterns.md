# Cross-System Patterns: What Envoy Adds

<!-- nav:start -->
**[Index](README.md)** · [Envoy 00 Overview](envoy-00-overview.md) · Sibling catalogues: [Kafka](../kafka/patterns.md) · [Cassandra](../cassandra/patterns.md) · [Kubernetes](../kubernetes/patterns.md)
<!-- nav:end -->

The other three catalogues compare storage and coordination systems. Envoy is the first **request-path data plane** in the project. It stores nothing durable, runs no consensus, and holds no replicated state. So it contributes rows the others cannot: load balancing, request-level failure handling, and config distribution from a control plane to thousands of proxies. This file keeps the same table shape and adds an Envoy column beside the closest analogue in the other series.

**How to read it.** "In Envoy" cites the Envoy report that proves the mechanism. "Closest analogue" links the sibling report. A `-` means no real analogue, which is often the most interesting cell. Claims about Envoy were read from the v1.39.1 source (see each report). Claims about the other systems are from their own series.

---

## 1. Control plane and data plane

| Pattern | Mechanism | In Envoy | Closest analogue elsewhere |
|---|---|---|---|
| **Publish desired state, data plane converges and reports** | A control plane serves versioned resources; each data-plane node applies them at its own pace and says whether it accepted them | xDS. Envoy sends `version_info` plus `response_nonce` to ACK, adds `error_detail` to NACK. Apply is per resource: CDS and LDS apply the valid resources in a response and keep the previous version of each invalid one, then NACK the whole response ([report 06](envoy-06-xds-control-plane.md)) | Kafka brokers replay `__cluster_metadata` as observers ([Kafka 03](../kafka/kafka-03-kraft-controller.md)). Kubernetes controllers write `status.observedGeneration` ([K8s 02](../kubernetes/kubernetes-02-controllers.md)). Envoy's NACK is richer than either: it rejects a bad version explicitly instead of failing to converge silently |
| **Last-known-good under control-plane loss** | The data plane never blocks on the control plane | No xDS stream means no updates, not no traffic. Health checks and outlier detection still run locally ([report 06](envoy-06-xds-control-plane.md), [report 05](envoy-05-resilience.md)) | kube-proxy keeps its programmed rules when the apiserver is down. Kafka brokers keep serving on their last `MetadataImage`. The common deadline is credentials: Envoy's SDS certs expire, kubelet client certs expire |
| **State of the world vs delta sync** | Send the full set each time (simple, O(total)) or only changes (efficient, needs per-client state on the server) | SotW xDS vs incremental (delta) xDS with `initial_resource_versions` on reconnect ([report 06](envoy-06-xds-control-plane.md)) | Kubernetes list then watch; Kafka incremental fetch sessions (KIP-227, [Kafka 05](../kafka/kafka-05-consumer-rebalance.md)); Cassandra full vs incremental repair ([C* 07](../cassandra/cassandra-07-repair-streaming.md)) |
| **Make before break** | Build and warm the replacement before routing to it; drain the old one after | Cluster warming until first EDS, listener warming until RDS and SDS, the CDS, EDS, LDS, RDS update order, hot restart socket handover before drain ([report 06](envoy-06-xds-control-plane.md), [report 09](envoy-09-operations-and-deployment.md)) | Kubernetes `maxSurge` rolling updates; Kafka reassignment adds replicas before removing old ones ([Kafka 02](../kafka/kafka-02-replication-isr.md)); Cassandra bootstrap streams data before a node joins the ring ([C* 06](../cassandra/cassandra-06-membership-gossip.md)) |
| **Dependency-ordered initialization with a timeout** | Targets register with a manager; the owner proceeds when all are ready or a deadline fires | `Init::Manager` / `Init::Target` / `Init::Watcher`; `initial_fetch_timeout` 15 s per subscription ([report 06](envoy-06-xds-control-plane.md)) | Kubernetes informer `WaitForCacheSync` before controllers start; systemd unit ordering. Envoy's timeout is the unusual part: it chooses availability (start without the resource) over completeness |

**Key judgement.** Envoy took the Kubernetes control-plane idea (publish desired state, converge locally) and pushed it into a data plane that must never stall. That forced two additions the others do not need: explicit NACK with per-resource last-known-good, and warming, because a half-configured proxy drops real traffic.

---

## 2. Concurrency and snapshots

| Pattern | Mechanism | In Envoy | Closest analogue elsewhere |
|---|---|---|---|
| **Shared-nothing event loops, connection pinned to a thread** | N threads each run their own event loop; a connection lives on one thread for life | Worker threads with `reuse_port` sockets; the kernel picks the worker ([report 01](envoy-01-threading-and-process-model.md)) | Kafka `Processor` threads get connections round robin by count, and one hot connection can dominate a processor ([Kafka 06](../kafka/kafka-06-broker-request-pipeline.md)). Same failure mode in both: balance by connection count, not by load |
| **Immutable snapshot, pointer swap, reclaim on last reference** | Writers build a new version off to the side and publish it atomically; readers hold a reference and never lock | Main thread builds route, cluster and runtime snapshots, posts them through thread-local slots; each worker swaps a `shared_ptr` ([report 01](envoy-01-threading-and-process-model.md)) | RocksDB `SuperVersion`: readers pin memtables plus SST list, compaction installs a new version ([RocksDB 02](../rocksdb/rocksdb-02-read-path-and-sst.md)). Kafka `MetadataImage` published by the loader ([Kafka 03](../kafka/kafka-03-kraft-controller.md)) |
| **Per-request snapshot pinning** | One unit of work sees one version for its whole life | An HTTP stream keeps the route config it started with, even if RDS updates mid-request ([report 03](envoy-03-http-connection-manager-and-routing.md)) | RocksDB iterators and snapshots; MVCC read timestamps in any database |
| **Deferred deletion to the end of the loop iteration** | Objects that may still be on the call stack are queued and freed after the current event finishes | `Dispatcher::deferredDelete` ([report 01](envoy-01-threading-and-process-model.md)) | Epoch-based reclamation; RocksDB deletes obsolete SSTs only when no version references them |
| **Thread-local recording, periodic merge** | Hot-path writes go to a per-thread structure; one thread aggregates on a timer | Histograms recorded per worker and merged on the main thread at each 5 s flush ([report 08](envoy-08-observability-and-extensibility.md)) | FreeBSD `counter(9)`, which Dropbox considered and rejected building into NGINX; RocksDB per-core statistics |
| **Global limits as the exception to shared-nothing** | Where a limit is only meaningful globally, accept cross-thread atomics and a small overshoot | Circuit breakers are per cluster, shared by all workers through atomics, and can be exceeded briefly ([report 05](envoy-05-resilience.md)). Local rate limit token buckets are shared too | Kafka quotas are per broker, not per thread; Kubernetes APF seats are per apiserver ([K8s 01](../kubernetes/kubernetes-01-apiserver-etcd.md)) |

---

## 3. Flow control and back-pressure

| Pattern | Mechanism | In Envoy | Closest analogue elsewhere |
|---|---|---|---|
| **High and low watermarks with read-disable** | When an output buffer passes a high watermark, stop reading the input; resume below a low watermark | Watermark buffers on connections and streams, propagated downstream codec to router to upstream codec ([report 02](envoy-02-listeners-and-network-filters.md), [report 03](envoy-03-http-connection-manager-and-routing.md)) | Kafka mutes a channel after each request, so a slow broker stops reading and TCP windows close ([Kafka 06](../kafka/kafka-06-broker-request-pipeline.md)); RocksDB write stalls ([RocksDB 01](../rocksdb/rocksdb-01-write-path.md)) |
| **Credit-based flow control inside a multiplexed connection** | Each stream and the connection get byte windows the receiver replenishes | HTTP/2 windows: 16 MiB per stream, 24 MiB per connection by default in 1.39 ([report 03](envoy-03-http-connection-manager-and-routing.md)) | Kafka is pull-based, so the consumer's fetch size is the credit. `-` in Kubernetes |
| **Graded overload response** | Measure resource pressure; apply progressively harsher actions as it rises | Overload manager: monitors (heap, cgroup memory, CPU, connections) drive actions from scaled timers and disabled keep-alive up to stop accepting requests ([report 05](envoy-05-resilience.md)) | kubelet soft then hard eviction thresholds ([K8s 04](../kubernetes/kubernetes-04-kubelet-node-runtime.md)); Kafka throttles with latency, not errors |
| **Adaptive concurrency limit** | Estimate the healthy latency floor and shrink the allowed concurrency when latency rises | `adaptive_concurrency` gradient controller ([report 05](envoy-05-resilience.md)) | Netflix concurrency-limits; TCP Vegas. `-` in the other series |

---

## 4. Failure detection and recovery

| Pattern | Mechanism | In Envoy | Closest analogue elsewhere |
|---|---|---|---|
| **Active plus passive health** | Probe endpoints on a timer and also judge them by real traffic results | Active health checks on the main thread plus outlier detection from request results ([report 05](envoy-05-resilience.md)) | Kubernetes probes (active) plus node leases (heartbeat). Cassandra's phi-accrual detector is passive, from gossip ([C* 06](../cassandra/cassandra-06-membership-gossip.md)) |
| **Bound the failure detector's blast radius** | When "everything looks unhealthy", suspect the detector and stop acting | `max_ejection_percent` 10% caps outlier ejection. Panic mode at 50% healthy routes to all hosts ([report 04](envoy-04-cluster-manager-and-load-balancing.md), [report 05](envoy-05-resilience.md)) | The Kubernetes node controller drops to 0.01 nodes/s eviction when more than 55% of a zone is not ready, and stops entirely in full disruption ([K8s 02](../kubernetes/kubernetes-02-controllers.md)). The same judgement in both: a mass failure is more likely a monitoring failure |
| **Bulkheads per destination** | Cap concurrent work per downstream dependency so one slow dependency cannot absorb all capacity | Circuit breakers per cluster per priority: 1024 connections, pending and requests, 3 retries by default ([report 05](envoy-05-resilience.md)) | Kubernetes APF priority levels; Kafka per-client quotas |
| **Retry budgets, not retry counts** | Cap retries as a fraction of live traffic, so amplification is bounded under failure | Retry budget: 20% of active plus pending requests, minimum 3 ([report 05](envoy-05-resilience.md)) | client-go workqueue exponential back-off is per item, not a budget. Google SRE's client-side throttling is the same idea, and Envoy ships it as `admission_control` |
| **Hedged requests** | Send a second copy after a delay; take whichever answers first | `hedge_on_per_try_timeout` ([report 05](envoy-05-resilience.md)) | Cassandra `speculative_retry`, default 99th percentile ([C* 03](../cassandra/cassandra-03-read-path.md)). Both turn tail latency into extra load, so both need a cap |
| **Graceful drain before exit** | Stop accepting, signal clients to go elsewhere, give in-flight work a deadline | HTTP/1 `Connection: close`, HTTP/2 GOAWAY with 5 s grace, listener drain over `--drain-time-s` 600 s ([report 09](envoy-09-operations-and-deployment.md)) | Kubernetes `preStop` plus `terminationGracePeriodSeconds` ([K8s 04](../kubernetes/kubernetes-04-kubelet-node-runtime.md)); Kafka controlled shutdown moves leadership first ([Kafka 02](../kafka/kafka-02-replication-isr.md)) |

---

## 5. Placement and load balancing *(new section: Envoy's distinctive contribution)*

| Pattern | Mechanism | In Envoy | Closest analogue elsewhere |
|---|---|---|---|
| **Power of two choices** | Sample two candidates at random, pick the less loaded; near-optimal balance with no global state | `least_request` with `choice_count` 2 when weights are equal ([report 04](envoy-04-cluster-manager-and-load-balancing.md)) | `-` in the other series. The Kubernetes scheduler scores every feasible node instead, which it can afford at pod-creation rates, not request rates |
| **Consistent hashing, ring vs table** | Map keys to backends so a membership change moves only about 1/N of keys | Ring hash (ketama, 1024 to 8M entries, binary search) and Maglev (65537-entry table, O(1) lookup) ([report 04](envoy-04-cluster-manager-and-load-balancing.md)) | Cassandra's token ring with vnodes ([C* 00](../cassandra/cassandra-00-overview.md)); IPVS `mh` and Cilium Maglev ([K8s 05](../kubernetes/kubernetes-05-networking.md)). Kafka's default partitioner is hash mod N, deliberately not consistent |
| **Locality-aware routing with spillover** | Prefer the caller's zone; spill cross-zone only as much as capacity requires | Zone-aware routing (min cluster size 6), locality weights, priority levels with the 1.4 overprovisioning factor ([report 04](envoy-04-cluster-manager-and-load-balancing.md)) | Kubernetes `trafficDistribution: PreferSameZone` ([K8s 05](../kubernetes/kubernetes-05-networking.md)); Kafka follower fetching KIP-392 ([Kafka 02](../kafka/kafka-02-replication-isr.md)); Cassandra `LOCAL_QUORUM` ([C* 05](../cassandra/cassandra-05-coordinator-consistency.md)) |
| **Slow start for new capacity** | Ramp a new backend's weight over a window instead of giving it full share at once | Slow start: linear ramp by default, floor at 10% of weight ([report 04](envoy-04-cluster-manager-and-load-balancing.md)) | `-` in the other series. Cold caches and JIT warm-up are the reasons, and Kafka's cold page cache after a broker restart is the same problem without the fix ([Kafka 00](../kafka/kafka-00-overview.md)) |

---

## 6. Extension and isolation

| Pattern | Mechanism | In Envoy | Closest analogue elsewhere |
|---|---|---|---|
| **Typed extension registry** | Extensions register a factory under a protobuf type; config selects them by type URL | `Registry::FactoryRegistry` plus `typed_config` ([report 08](envoy-08-observability-and-extensibility.md)) | Kubernetes CRDs ([K8s 07](../kubernetes/kubernetes-07-extensibility-security.md)) and scheduler framework plugins ([K8s 03](../kubernetes/kubernetes-03-scheduler.md)); Kafka pluggable authorizer and partitioner; Cassandra pluggable compaction strategies |
| **In-process vs out-of-process extension** | Trade latency for isolation: call a sidecar service, or run code in the proxy | ext_authz and ext_proc (gRPC out of process) vs Lua, Wasm, dynamic modules and native C++ (in process) ([report 08](envoy-08-observability-and-extensibility.md)) | Kubernetes admission webhooks (out) vs scheduler plugins (in). Same trade: webhooks add a network hop and a failure mode per request |
| **Middleware pipeline with explicit continuation** | Each stage can pass, stop, buffer, or answer; the chain resumes on a callback | Listener, network and HTTP filter chains with `Continue` / `StopIteration` / `continueDecoding` ([report 03](envoy-03-http-connection-manager-and-routing.md)) | Kubernetes admission chain (mutating then validating); Kafka producer and consumer interceptors |
| **Guarded behaviour changes** | Ship a change behind a flag that defaults on or off, flip it at runtime, delete the flag later | `RUNTIME_GUARD` / `FALSE_RUNTIME_GUARD` reloadable features ([report 10](envoy-10-version-delta.md)) | Kubernetes feature gates (alpha, beta, GA); Kafka `metadata.version` feature levels ([Kafka 09](../kafka/kafka-09-version-delta.md)) |

---

## 7. Operations

| Pattern | Mechanism | In Envoy | Closest analogue elsewhere |
|---|---|---|---|
| **Every rejection has a named reason** | Attach a machine-readable cause to each failed unit of work | Response flags: `UH`, `UF`, `UO`, `URX`, `UT`, `NR`, `DC` and more, in stats and access logs ([report 05](envoy-05-resilience.md), [report 09](envoy-09-operations-and-deployment.md)) | Kubernetes Event reasons and conditions; Kafka error codes. Envoy's version is per request, which makes it the most directly actionable |
| **Bound telemetry cardinality at the source** | Intern names, limit which metrics exist, drop the rest before they cost memory | Symbol table for stat names and `stats_matcher` inclusion lists ([report 08](envoy-08-observability-and-extensibility.md)) | apiserver metric cardinality limits; Prometheus relabel drops (after the fact) |
| **Validate before you apply** | Run the full config pipeline without serving | `envoy --mode validate` ([report 09](envoy-09-operations-and-deployment.md)) | `kubectl apply --dry-run=server` |
| **Live binary upgrade without dropping the port** | Hand the listening socket to a new process, drain the old | Hot restart over a Unix domain socket, sockets passed by worker index ([report 09](envoy-09-operations-and-deployment.md)) | HAProxy and NGINX reloads fork a new master or workers. In Kubernetes nobody does this: a new pod replaces the old one behind the Service |

---

## What Envoy contributes that the other systems do not

- **Request-level failure handling as a composable policy.** Timeouts, retries, budgets, hedging, outlier ejection, circuit breakers and panic mode interact on every request. None of the storage systems has this layer. Their clients do, one library at a time, which is exactly the problem Envoy was built to remove.
- **Load balancing as a first-class subsystem.** Five algorithms plus priorities, localities, subsets and slow start. Kafka and Cassandra place data. Envoy places requests, thousands of times a second per worker, with no global state.
- **A control-plane protocol designed for many clients and explicit rejection.** xDS generalizes to proxyless gRPC and to any data plane. It is the only protocol across these series where a node formally says "I refuse part of this version, here is why", while still applying the parts that were valid.
- **Configuration propagation without locks on the hot path.** The thread-local snapshot pattern is the Envoy idea most worth stealing for any multi-threaded server.

## Open questions to revisit as more systems are added

- Where does a request-path proxy's eventual consistency (stale endpoints for seconds after a scale-down) meet a storage system's strong consistency? A Cassandra coordinator routing through a stale Envoy is the interesting case.
- Is ztunnel plus waypoint (split L4 and L7 proxies) the general answer to sidecar cost, or is proxyless gRPC? Worth a comparison once a mesh-level series exists.
