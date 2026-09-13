# Kubernetes Internals

<!-- nav:start -->
**[← All systems](../README.md)** · [Start here: 00 Overview](kubernetes-00-overview.md) · [Pattern catalogue](patterns.md)
<!-- nav:end -->

**Baseline: v1.34.** Deltas through v1.37 live in
[`kubernetes-09-delta-since-1.34.md`](kubernetes-09-delta-since-1.34.md). Read that file's errata before quoting any
number in an interview.

> *etcd holds the truth, the apiserver guards and publishes it, and every other
> component is a loop that watches a slice of it and makes reality match.*

| File | Covers |
|---|---|
| [`kubernetes-00-overview.md`](kubernetes-00-overview.md) | Reading map, architecture, the three design bets |
| [`kubernetes-01-apiserver-etcd.md`](kubernetes-01-apiserver-etcd.md) | Request pipeline, storage layer, watch cache, P&F |
| [`kubernetes-02-controllers.md`](kubernetes-02-controllers.md) | Shared informers, workqueues, leader election |
| [`kubernetes-03-scheduler.md`](kubernetes-03-scheduler.md) | Scheduling cycle, framework plugins, preemption |
| [`kubernetes-04-kubelet-node-runtime.md`](kubernetes-04-kubelet-node-runtime.md) | Pod lifecycle, CRI, cgroups, eviction |
| [`kubernetes-05-networking.md`](kubernetes-05-networking.md) | CNI, kube-proxy modes, Services, EndpointSlice |
| [`kubernetes-06-storage.md`](kubernetes-06-storage.md) | CSI, PV/PVC binding, attach/detach, resize |
| [`kubernetes-07-extensibility-security.md`](kubernetes-07-extensibility-security.md) | CRDs, webhooks, CEL, RBAC, admission |
| [`kubernetes-08-autoscaling-and-scale.md`](kubernetes-08-autoscaling-and-scale.md) | HPA/VPA/CA/Karpenter, the 5k-node envelope |
| [`kubernetes-09-delta-since-1.34.md`](kubernetes-09-delta-since-1.34.md) | Version deltas and errata |
| [`patterns.md`](patterns.md) | Cross-system pattern catalogue (Kubernetes only) |

**Scale envelope:** 5,000 nodes / 150,000 pods / `min(110, 10x cores)` pods per
node. SLOs: p99 <= 1s for non-list API calls, p99 <= 5s for pod startup
excluding image pull. Past that the answer is more clusters, not a bigger one.

**Red nodes in this folder:** the `ScheduleOne` loop (`03`) and `kube-scheduler`
(`08`). Both are the same single-threaded scheduling cycle, ~100-300 pods/s.
