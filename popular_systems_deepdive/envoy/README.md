# Envoy Deep Dive Series

<!-- nav:start -->
**[← All systems](../README.md)** · [Start here: 00 Overview](envoy-00-overview.md) · [Interviewer prep](interviewer-prep.md) · [Pattern catalogue](patterns.md)
<!-- nav:end -->

**Series baseline: Envoy v1.39.1** (released 2026-08-27; v1.39.0 on 2026-07-14).
Every default, field name and class name was read from that tag's source tree, and
every non-trivial claim carries a permalink pinned to `v1.39.1`. Work that landed on
`main` after the v1.39.0 cut is labelled "main only". A patch release carries only
backports, so a PR merged in August is usually **not** in v1.39.1.

> *A pipeline of filters running on N independent event loops, fed by immutable
> configuration snapshots that one main thread builds from a control plane's xDS
> stream, and a response flag for every way a request can die.*

Same conventions as the Kafka and Kubernetes series: `[documented]` / `[inferred]` /
`[unverified]` marks, 13-section reports, the repo color legend.

## Contents

| File | Covers |
|---|---|
| [`envoy-00-overview.md`](envoy-00-overview.md) | Design bets, architecture, the config object model, life of a request, history and adoption, reading map |
| [`envoy-01-threading-and-process-model.md`](envoy-01-threading-and-process-model.md) | Main, worker, flush and guard-dog threads, Dispatcher, thread-local snapshots, reuse_port and balancers, runtime, watchdog, tcmalloc, io_uring |
| [`envoy-02-listeners-and-network-filters.md`](envoy-02-listeners-and-network-filters.md) | Listener manager and lifecycle, listener filters, filter chain matching, network filters, watermarks, TLS transport sockets, tcp_proxy, L4 proxies, UDP and QUIC |
| [`envoy-03-http-connection-manager-and-routing.md`](envoy-03-http-connection-manager-and-routing.md) | HCM, Balsa / nghttp2 / QUICHE codecs, filter manager statuses, flow control, header trust, timeouts, upgrades, routing, the router filter |
| [`envoy-04-cluster-manager-and-load-balancing.md`](envoy-04-cluster-manager-and-load-balancing.md) | Cluster manager init and warming, discovery types, connection pools, every LB algorithm, priorities, panic, zone-aware routing, slow start, ORCA |
| [`envoy-05-resilience.md`](envoy-05-resilience.md) | Health checks, outlier detection math, circuit breakers and retry budgets, timeout matrix, retries, hedging, rate limits, overload manager, response flags |
| [`envoy-06-xds-control-plane.md`](envoy-06-xds-control-plane.md) | xDS types, SotW vs delta, ADS, ACK/NACK, init order and warming, on-demand, xDS-TP, SDS/RTDS/ECDS, control planes, failure behaviour |
| [`envoy-07-security.md`](envoy-07-security.md) | Threat model and extension posture, TLS and mTLS, SPIFFE, SDS rotation, RBAC, ext_authz, JWT, OAuth2, header trust, path normalization, HTTP/2 hardening |
| [`envoy-08-observability-and-extensibility.md`](envoy-08-observability-and-extensibility.md) | Stats internals and cost, admin, access logs, tracing, extension registry, Lua, Wasm, ext_proc, Golang, matcher API |
| [`envoy-09-operations-and-deployment.md`](envoy-09-operations-and-deployment.md) | Topologies, hot restart and draining, validation, resource envelope, tuning, alerts, runbooks by response flag, sidecar cost, migrations |
| [`envoy-10-version-delta.md`](envoy-10-version-delta.md) | Release process, 1.30 to 1.39 changes, default-change timeline, runtime guards, extension maturity, 34 errata, upgrade playbook |
| [`envoy-11-dynamic-modules.md`](envoy-11-dynamic-modules.md) | Native extensions over a C ABI: loader, ABI, every extension point, lifecycle, threading, FFI safety, SDKs, compatibility policy, trade-offs |
| [`envoy-12-mcp-and-ai-gateway.md`](envoy-12-mcp-and-ai-gateway.md) | `mcp`, `mcp_router`, JSON-REST bridge, `a2a`, `ai_protocol_manager`, `mcp_multicluster`, and the stateless MCP 2026-07-28 revision |
| [`envoy-13-newer-traffic-features.md`](envoy-13-newer-traffic-features.md) | Reverse tunnels, composite cluster and filter, RBAC matchers, ext_authz evolution, tcp_proxy tunneling, Hickory DNS, CPU pinning, sockmap, TLS and QUIC |
| [`interviewer-prep.md`](interviewer-prep.md) | Prep for an interview with an Envoy senior maintainer: their systems, verified corrections, the extensibility opinion, landmines, question bank |
| [`patterns.md`](patterns.md) | What Envoy adds to the cross-system pattern catalogue, cross-linked to Kafka, Kubernetes, Cassandra and RocksDB |

## Reading order

00 → 03 → 04 + 05 → 01 → 06 → 02 + 07 → 08 / 09, with 10 open whenever you quote a
number. 11 to 13 are the newest subsystems and the ones most write-ups have not caught
up with. For the interview track, start at [`interviewer-prep.md`](interviewer-prep.md).

The companion system design problem is [`hld/ai-gateway/`](../../hld/ai-gateway/)
("Design an AI gateway for thousands of tenants").

## Read this first

Five things most secondary writing about Envoy gets wrong for v1.39.1 (details and more
in [report 10 §9](envoy-10-version-delta.md)):

1. **HTTP/2 defaults changed in 1.36.** The stream window is 16 MiB, the connection window 24 MiB, and max concurrent streams 1024. 256 MiB and 2^31-1 are old or maximum values.
2. **A NACK does not mean nothing changed.** CDS and LDS apply each valid resource and then NACK the whole response. An ACK means "valid", not "applied".
3. **`--concurrency` is the host's hardware thread count**, not the container's CPU limit, unless you pass `--cpuset-threads`. The 1.37 release note overstates this.
4. **Dynamic modules are not sandboxed**, and the ABI version string is warn-only. The HTTP filter kind is stable. The other kinds are alpha.
5. **Nothing is "internal" by default since 1.33.** RFC1918 addresses no longer get `x-envoy-*` header trust unless you configure `internal_address_config`.

## Diagrams

191 Mermaid diagrams: 98 flowcharts, 51 sequence diagrams, 37 state diagrams, 2 gantt,
2 timeline, 1 pie. All render with mermaid-cli 11.17 (validated 2026-09-24). Colors use
the repo legend in [`../../templates/color-legend.md`](../../templates/color-legend.md),
with an Envoy-specific role mapping:

| Envoy thing | Class |
|---|---|
| Downstream clients, listen sockets, listeners | `client` blue |
| Threads, dispatchers, filters, HCM, router, cluster manager, LBs, codecs | `service` green |
| Bootstrap file, control-plane store, certificate files | `store` purple |
| Thread-local snapshots, connection pools, host sets, DNS cache, stats store | `cache` amber |
| Watermark buffers, dispatcher post queues, the xDS stream, accept queue | `queue` cyan |
| Upstreams, control planes, ext_authz and rate limit services, the kernel | `external` grey dashed |
| Decision points | `decision` pink |

**Red means one thing per report: the thing that breaks first there.** Each report's
§8 names it with a mechanism and a number.

| Report | Red node | Why it breaks first |
|---|---|---|
| 01 | Main thread dispatcher | Every xDS update is decoded and applied synchronously on one thread. 5,000 clusters x 16 workers is 80,000 posted closures. Visible as `watchdog_miss` at 200 ms |
| 02 | Connection read and write buffers | Four 1 MiB soft buffers per proxied TCP pair. 10,000 slow peers is about 40 GiB while CPU looks idle |
| 03 | Per-stream body buffer | 1024 streams x 16 MiB window lets one HTTP/2 connection pin up to 16 GiB before a 413 |
| 04 | Per-worker connection pools | Connections = workers x hosts x pool keys, and HTTP/1 needs one connection per in-flight request, so 1024 / 1024 breakers give 503 `UO` |
| 05 | Circuit breakers (`ResourceManagerImpl`) | Little's law: 10,000 RPS at 150 ms latency needs 1,500 in flight, above the 1024 default |
| 06 | Main thread xDS processing | SotW CDS is O(total). One changed cluster out of 10,000 still costs 10,000 decodes |
| 07 | The ext_authz side call | Every protected request parks for up to 200 ms, then fails closed as 403 |
| 08 | Central stats store | 47,086 bytes per cluster in the memory golden test. 10,000 clusters is about 470 MB before traffic |
| 09 | Sidecar config-proportional memory | An unscoped sidecar in a 5,000-service mesh holds about 235 MB of cluster objects, in every pod |
| 10 | A pinned runtime guard that no longer exists | After removal the pin is silently ignored and new behaviour hits 100% of traffic |
| 11 | Module hook code on a worker | A 200 ms block stalls 1/N of capacity. A segfault kills all N workers |
| 12 | `mcp_router` fan-out | Lists wait for every backend, up to 5 s each. 20 backends at a 1% stall rate stall about 18% of calls |
| 13 | Reverse tunnel idle-socket pool | Thread-local. A worker with no tunnel waits up to about 11.5 s for a re-dial |
| prep §2 | The hot pod before client-side LB | kube-proxy's per-connection pick pins long-lived gRPC connections |

## How this series was built

- Source: `git clone --depth 1 --branch v1.39.1` of envoyproxy/envoy, read with grep
  and a proto-comment extractor. The API protos, the C++ that applies each default, the
  in-tree docs and the per-release `changelogs/*.yaml` were all checked.
- Eight parallel writers, each checking its own report against the tree. An editor pass
  cross-checked the reports against each other. That caught and fixed a wrong
  internal-address default in report 05, a NACK-semantics error in the overview, and two
  facts-sheet errors (the Linux listen backlog is `somaxconn`, not 128, and there is one
  access-log flush thread per file).
- External facts (history, adoption, Istio numbers, the MCP spec, Databricks posts) were
  fetched from primary pages on 2026-09-24. Survey claims that failed a spot-check were
  dropped.
