# Kubernetes Internals — Appendix: Delta from v1.34 to v1.37

<!-- nav:start -->
[← 08 Autoscaling & Scale](kubernetes-08-autoscaling-and-scale.md) · **[Index](README.md)** · →
<!-- nav:end -->

<!-- toc:start -->
<details>
<summary><b>Sections in this report (7)</b></summary>

- [1. How to read this appendix](#1-how-to-read-this-appendix)
- [2. Release timeline](#2-release-timeline)
- [3. Feature-gate movement (v1.34 → v1.37)](#3-feature-gate-movement-v134--v137)
- [4. Removals and deprecations](#4-removals-and-deprecations)
- [5. Per-report errata](#5-per-report-errata)
- [6. New subsystems worth a future deep dive](#6-new-subsystems-worth-a-future-deep-dive)
- [7. Sources](#7-sources)

</details>
<!-- toc:end -->

## 1. How to read this appendix

- Reports `01`–`08` are pinned to **v1.34** (2025-08-27) and were not retroactively updated.
- This file lists only what changed in v1.35–v1.37. Stage claims are verified against `release-1.37` `kube_features.go` (both the `pkg/features` and apiserver copies) or the release CHANGELOGs.
- Anything not listed here is still accurate as of **v1.37** to the best of this verification. Unconfirmed items are **[unverified]**; **[inferred]** marks reasoning; everything else is **[documented]**.

## 2. Release timeline

| Version | Name | Released | EOL | Theme |
|---|---|---|---|---|
| v1.34 | Of Wind & Will (O' WaW) | 2025-08-27 | 2026-10-27 | Series baseline. |
| v1.35 | Timbernetes (The World Tree Release) | 2025-12-17 | 2027-02-28 | 60 enhancements (17/19/22 stable/beta/alpha); in-place resize GA, cgroup v1 deprecated. |
| v1.36 | ハル (Haru) | 2026-04-22 | 2027-06-28 | 70 (18/25/27); user namespaces GA, MutatingAdmissionPolicy GA, in-tree Portworx removed. |
| v1.37 | Garhwal | 2026-08-26 | 2027-10-28 | 67 (16/23/27); SELinuxMount GA, Pod Certificates GA, WAS to `v1beta1`, etcd 3.7 + RangeStream. |

**What to notice**
- v1.34 goes EOL 2026-10-27 — the series baseline is about to become unsupported.
- v1.37 carries the window's largest upgrade hazards (`SELinuxMount`, `scheduling.k8s.io/v1alpha2` drop).

## 3. Feature-gate movement (v1.34 → v1.37)

Stages source-verified. "on"/"off" = default. `—` = gate did not exist in v1.34. Sorted by report.

| Gate | v1.34 | v1.37 | Report | Impact |
|---|---|---|---|---|
| `StorageVersionMigrator` | Alpha off | **GA on** (1.37) | 01 | `storagemigration.k8s.io/v1` served by default. |
| `WatchCacheInitializationPostStartHook` | Beta off | **GA locked** (1.37) | 01 | Apiserver not ready until watch cache primed. |
| `EtcdRangeStream` | — | **Beta on** (1.37) | 01 | Cache primes via one etcd `RangeStream` RPC, not paginated `Range`. |
| `ConcurrentWatchObjectDecode` | Beta off | **Beta on** (1.37) | 01 | Parallel watch-event decode; different CPU profile. |
| `WatchListCompression` | — | **Beta on** (1.37) | 01 | gzip for `WatchList`; plain `watch` unaffected. |
| `UnknownVersionInteroperabilityProxy` | Alpha off | **Beta on** (1.36) | 01 | Mixed-version proxy; needs `--peer-ca-file` to activate. |
| `AllowUnsafeMalformedObjectDeletion` | Alpha off | **Beta on** (1.37) | 01 | Corrupt-object deletion on by default, with dry-run. |
| `ShardedListAndWatch` | — | Alpha off (1.36) | 01 | Server-side sharded LIST/WATCH. |
| `ConsistentListFromCacheSkipTimeoutFallback` | — | Alpha off (1.37) | 01 | Cache-miss consistent LIST returns 429 instead of hitting etcd. |
| `JobManagedBy` | Beta on | **GA locked** (1.35) | 02 | `spec.managedBy` unconditional. |
| `PodObservedGenerationTracking` | Beta on | **GA locked** (1.35) | 02 | Pod `status.observedGeneration` unconditional. |
| `DeploymentReplicaSetTerminatingReplicas` | Alpha off | **Beta on** (1.35) | 02 | `.status.terminatingReplicas` populated by default. |
| `MaxUnavailableStatefulSet` | Alpha off | **Beta on** (1.37) | 02 | StatefulSet rollouts exceed one-at-a-time by default. |
| `StaleControllerConsistencyJob` | — | **Beta on** (1.36) | 02 | Job controller defers sync on stale cache; new skip metric. |
| `StaleControllerConsistencyHPA` | — | **Beta on** (1.37) | 02, 08 | Same staleness guard for HPA. |
| `NodeControllerLeaseCircuitBreaker` | — | **Beta on** (1.37) | 02 | Circuit-breaks mass eviction on lease loss. |
| `EvictionRequestAPI` | — | Alpha off (1.37) | 02 | EvictionRequest/Eviction + `.spec.evictionResponders`. |
| `StatefulSetRecreateStrategy` | — | Alpha off (1.37) | 02 | `Recreate` update strategy for StatefulSet. |
| `GenericWorkload` | — | **Beta off** (1.37) | 03 | Single gate for WAS; replaces `GangScheduling`/`WorkloadAwarePreemption`. |
| `TopologyAwareWorkloadScheduling` | — | Alpha off (1.36) | 03 | Placement-based PodGroup scheduling. |
| `CompositePodGroup` | — | Alpha off (1.37) | 03 | Nested PodGroups for heterogeneous workloads. |
| `SchedulerPreQueueingHints` | — | Alpha off (1.37) | 03 | Beta in-cycle, **demoted to Alpha before release**. |
| `SchedulerAsyncAPICalls` | Beta off | Beta off | 03 | Churned: off 1.34, on 1.35, off again 1.36 (client throttling). |
| `InterPodAffinityHostnameFastPath` | — | Alpha off (1.37) | 03 | Fast path for hostname-topology affinity. |
| `InPlacePodVerticalScaling` | Beta on | **GA locked** (1.35) | 04, 08 | Resize unconditional; `…AllocatedStatus` gate removed. |
| `InPlacePodVerticalScalingInitContainers` | — | **GA locked** (1.37) | 04 | Init/sidecar containers resizable. |
| `InPlacePodLevelResourcesVerticalScaling` | — | **Beta on** (1.36) | 04 | Pod-level CPU/memory resizable in place. |
| `UserNamespacesSupport` | Beta on | **GA locked** (1.36) | 04, 07 | Unconditional; `UserNamespacesPodSecurityStandards` gate removed. |
| `KubeletInUserNamespace` | Alpha off | **Beta on** (1.37) | 04 | Rootless kubelet supported at beta. |
| `KubeletPSI` | Beta on | **GA locked** (1.36) | 04 | PSI metrics in Summary API unconditional. |
| `MemoryQoS` | Alpha off | **Beta on** (1.37) | 04 | `memory.min`/`memory.low` tiering; `memory.high` now unset by default. |
| `PodLevelResourceManagers` | — | Beta off (1.37) | 04 | CPU/memory/topology managers act on pod-level resources. |
| `PLEGOnDemandRelist` | — | **GA locked** (1.37) | 04 | PLEG relists on demand, not periodically. |
| `PodReadyToStartContainersCondition` | Beta on | **GA locked** (1.37) | 04 | Condition always reported. |
| `NodeDeclaredFeatures` | — | **GA locked** (1.37) | 03, 04 | Nodes advertise runtime capabilities; several gates depend on it. |
| `ContainerRestartRules` | Alpha off | **Beta on** (1.35) | 04 | Per-container restart rules default on. |
| `KubeletCrashLoopBackOffMax` | Alpha off | **Beta on** (1.35) | 04 | Configurable backoff ceiling. |
| `KubeletEnsureSecretPulledImages` | Alpha off | **Beta on** (1.35) | 04, 07 | Re-verifies pull credentials for cached images. |
| `ImageVolume` | Beta off | **GA locked** (1.36) | 04, 06 | OCI image volume sources unconditional. |
| `ProcMountType` | Beta on | **GA locked** (1.36) | 04, 07 | Unmasked `/proc` unconditional. |
| `NodeLogQuery` | Beta off | **GA locked** (1.36) | 04 | `nodes/logs` subresource unconditional. |
| `HostnameOverride` | Alpha off | **GA locked** (1.37) | 04, 05 | `spec.hostnameOverride` unconditional. |
| `ExtendWebSocketsToKubelet` | Alpha off | **Beta on** (1.36) | 04, 01 | Apiserver proxies WS `exec/attach/portforward` straight to kubelet. |
| `DRANodeAllocatableResources` | — | Alpha off (1.36) | 04 | DRA models CPU/memory/hugepages; kubelet accounts it in cgroups. |
| `StrictIPCIDRValidation` | Alpha off | **Beta on** (1.36) | 05 | Rejects leading-zero IPs and ambiguous CIDRs. |
| `RelaxedServiceNameValidation` | Alpha off | **GA locked** (1.37) | 05 | Relaxed Service names unconditional. |
| `NFTablesNetlink` | — | **Beta on** (1.37) | 05 | nftables mode uses netlink, not the `nft` binary. |
| `KubeProxyNFTablesLocalhostNodePorts` | — | Alpha off (1.37) | 05 | Userspace TCP proxy for localhost NodePorts (v4/v6). |
| `KubeProxyIPVS` | GA on | **Deprecated on** (1.37) | 05 | Gate added to deactivate then remove ipvs mode. |
| `SELinuxMount` | Beta off | **GA on** (1.37) | 06, 04 | **ACTION REQUIRED** — changes relabelling on every SELinux cluster. |
| `VolumeAttributesClass` | GA on | **GA locked** (1.36) | 06 | Storage version moved to `storage.k8s.io/v1`. |
| `MutableCSINodeAllocatableCount` | Beta off | **GA locked** (1.36) | 06 | CSI drivers update node volume limits at runtime. |
| `CSIServiceAccountTokenSecrets` | — | **GA locked** (1.36) | 06, 07 | CSI SA tokens move to `secrets`, out of volume context and logs. |
| `PersistentVolumeClaimUnusedSinceTime` | — | **Beta on** (1.37) | 06 | PVCs carry an `Unused` condition. |
| `VolumeLimitScaling` | Alpha off (1.35) | **Beta on** (1.37) | 06, 03 | `preventPodSchedulingIfMissing` blocks scheduling without the driver. |
| `MutatingAdmissionPolicy` | Beta off | **GA on** (1.36) | 07 | CEL mutation is `v1` and default — a real webhook alternative. |
| `ManifestBasedAdmissionControlConfig` | — | **Beta on** (1.37) | 07 | Admission config from disk; survives etcd loss. |
| `PodCertificateRequest` | Alpha off | **GA on** (1.37) | 07 | Pod-scoped X.509 identity is a core primitive. |
| `ClusterTrustBundle`(`Projection`) | Beta off | **GA on** (1.37) | 07 | Cluster-wide trust anchors unconditional. |
| `ConstrainedImpersonation` | — | **Beta on** (1.36) | 07 | Attribute-constrained impersonation. |
| `DRAResourceClaimGranularStatusAuthorization` | — | **Beta on** (1.36) | 07, 04 | **ACTION REQUIRED** — new RBAC on `resourceclaims/binding` and `/driver`. |
| `DRAAdminAccess` | Beta on | **GA locked** (1.36) | 04, 07 | Privileged device access unconditional. |
| `DRAPrioritizedList` | Beta on | **GA locked** (1.37) | 03, 04 | Ordered device alternatives in a claim. |
| `DRAResourceClaimDeviceStatus` | Beta on | **GA locked** (1.37) | 04 | Per-device status in ResourceClaim. |
| `DRADeviceTaints` | Alpha off | **GA on** (1.37) | 03, 04 | Device taints/tolerations via `resource.k8s.io/v1`. |
| `DRAExtendedResource` | Alpha off | **GA locked** (1.37) | 03, 04 | DRA devices consumable as extended resources. |
| `DRAConsumableCapacity` | Alpha off | **Beta on** (1.36) | 03, 04 | Fractional/shared device capacity. |
| `DRADeviceBindingConditions` | Alpha off | **Beta on** (1.36) | 03 | Scheduler waits on device binding conditions. |
| `HPAConfigurableTolerance` | Alpha off | **GA locked** (1.37) | 08 | Per-HPA tolerance replaces the global 10%. |
| `HPAScaleToZero` | Alpha off | **Beta on** (1.37) | 08 | HPA scales to and from zero **by default**. |
| `HPAOptimizedSelectorStore` | — | **Beta on** (1.37) | 08 | Cuts selector-overlap lock contention at high HPA counts. |
| `OpportunisticBatching` | — | **Beta on** (1.35) | 08, 01 | Control-plane request batching. |

## 4. Removals and deprecations

### Urgent Upgrade Notes

| Release | Item | Action |
|---|---|---|
| v1.37 | `SELinuxMount` GA, on by default | May break SELinux-enabled workloads. Identify and fix on v1.36, or opt out, before upgrading. |
| v1.37 | `scheduling.k8s.io/v1alpha2` dropped; group → `v1alpha3`; `DisruptionMode` enum → struct | Delete all `v1alpha2` Workload/PodGroup objects from etcd **before** upgrading. |
| v1.37 | kubelet `eventRecordQPS` = 0 now means *unlimited* | Set an explicit non-zero value (e.g. 50) to keep the old limit. |
| v1.37 | kubelet logs effective config at startup | Restrict `nodes/logs` to trusted users. |
| v1.36 | Metric renamed `volume_operation_total_errors` → `volume_operation_errors_total` | Update dashboards and alerts. |
| v1.36 | Scheduler `PreBind` plugins may run in parallel | Plugins must return `PreBindPreFlightResult`; `nil` keeps sequential behaviour. |
| v1.36 | DRA granular status RBAC (beta) | Grant `update`/`patch` on `resourceclaims/binding`; `associated-node:update` or `arbitrary-node:update` on `resourceclaims/driver`. |
| v1.36 | kubeadm flex-volume support removed | Move to CSI, or hand-mount the plugin dir via `extraVolumes` before upgrading. |
| v1.35 | kubelet `--pod-infra-container-image` removed | Remove from config/`extraArgs` or kubelet fails to start. |
| v1.35 | cgroup v1 is an error, not a warning, for kubelet ≥ v1.35 | Set `failCgroupV1: false` in `kube-system/kubelet-config` to keep cgroup v1. |

### Removed

| Removed | Release | Replacement |
|---|---|---|
| In-tree Portworx plugin; `CSIMigrationPortworx`, `InTreePluginPortworxUnregister` | 1.36 | Portworx CSI driver. |
| `git-repo` volume plugin (disabled, **no opt-in**) | 1.36 | initContainer + emptyDir. |
| kubeadm flex-volume integration | 1.36 | CSI. |
| `scheduling.k8s.io/v1alpha1` Workload API | 1.36 | `v1alpha2`, then `v1beta1` (1.37). |
| `SnapshotMetadataService` `v1alpha1` | 1.36 | `v1beta1`. |
| `storagemigration.k8s.io/v1alpha1` | 1.35 | `v1beta1` (1.35), `v1` (1.37). |
| kubelet `--pod-infra-container-image` | 1.35 | Runtime-level sandbox image config. |
| `StrictCostEnforcementForVAP`, `StrictCostEnforcementForWebhooks` | 1.35 | Locked since 1.32; behaviour unchanged. |
| `AnyVolumeDataSource` gate | 1.37 | GA and locked since 1.33. |
| `GangScheduling`, `WorkloadAwarePreemption` gates | 1.37 | `GenericWorkload`. **[documented, internally inconsistent]** |
| `PodStatusResult` type | 1.37 | Unused since 2015. |
| 18 deprecated cAdvisor kubelet flags (all but `--housekeeping-interval`) | 1.37 | None — kubelet **fails to start** if any are set. |
| cAdvisor `userDefinedMetrics`, `container_application_*`, `container_cpu_load_*_10s`, `container_tasks_state` | 1.37 | None. |
| kubectl support for `discovery/v1beta1` EndpointSlice, `networking/v1beta1` Ingress/IngressClass | 1.35 | `v1` equivalents. |

### Deprecated (still present) — all **[documented]**

- **cgroup v1**: de facto deprecated from 1.35 (`failCgroupV1` defaults true).
- **kube-proxy `ipvs`**: deprecated 1.35; `KubeProxyIPVS` marked `Deprecated` in 1.37 ahead of removal.
- **kube-proxy default mode**: still `iptables`, but warns from 1.37 when `mode` is unset; nftables becomes default later.
- **Service `.spec.externalIPs`**: warned and deprecated 1.36 (`AllowServiceExternalIPs`).
- **`metav1.FieldsV1.Raw` direct access**: use the `NewFieldsV1`/`GetRawBytes`/`SetRawBytes` accessors.
- **DRAResourceHealth `v1alpha1` kubelet gRPC**: deprecated 1.37, removal planned **v1.40**.
- **`kubectl debug` `legacy` profile**: default became `general` in 1.36; removal planned **v1.39**. `kubectl run --filename/-f` deprecated 1.37.
- **No GA-served API version was removed in 1.35–1.37** — the deprecation guide's newest removal section is still v1.32.

## 5. Per-report errata

### 01-apiserver-etcd
- Default etcd is **v3.7.0** (was 3.6.x); client library v3.6.10.
- Watch cache primes via a single `RangeStream` RPC, not paginated `Range`; new `apiserver_watch_cache_initialization_duration_seconds`.
- Apiserver readiness blocks on cache priming (`WatchCacheInitializationPostStartHook` GA-locked).
- Storage version migration is a built-in GA subsystem (`storagemigration.k8s.io/v1`), not an add-on.
- `grpc-go` v1.82.1 adds an HTTP/2 control-frame flood limit; strict path checking is permanently on.
- client-go informers under `AtomicFIFO` (on from 1.36) update the store for the whole list/relist *before* firing handlers.

### 02-controllers
- Job, DaemonSet, ReplicaSet, StatefulSet and HPA controllers **defer syncing** when their cache has not observed their own last writes (`StaleControllerConsistency*`, beta on), with `*_stale_sync_skips_total` metrics. This invalidates the report's stale-cache failure-mode description.
- `--concurrent-disruption-syncs` added to kube-controller-manager; `NodeSyncPeriod` moved to `CloudControllerManagerConfiguration.NodeLifecycleController.NodeMonitorPeriod`.
- New alpha: EvictionRequest/Eviction resources, `.spec.evictionResponders`, StatefulSet `Recreate` strategy.

### 03-scheduler
- PodGroup/Workload API is now **`scheduling.k8s.io/v1beta1`**; `v1alpha1` and `v1alpha2` are both gone. `GangScheduling` + `WorkloadAwarePreemption` consolidated into `GenericWorkload`.
- New extension points: `PlacementGenerate`, `PlacementScore`, `PodGroupPostFilter`. `MinNodeScore`/`MaxNodeScore` deprecated for `MinScore`/`MaxScore`.
- `PreBind` may run **in parallel** (opt-in) — the report's sequential-PreBind description is stale.
- Workload-aware preemption now does one scheduling attempt with all candidate victims removed: faster, less optimal victim choice. `SchedulerQueueingHints` gate removed (graduated).

### 04-kubelet-node-runtime
- **cgroup v1 nodes fail to start by default** from v1.35 unless `failCgroupV1: false`.
- PLEG relists **on demand**, not periodically — the report's periodic-relist description is stale.
- MemoryQoS beta on, but `memoryThrottlingFactor` defaults nil, so `memory.high` is not written unless configured.
- Kubelet rejects 18 legacy cAdvisor flags and **fails to start** if present; several `container_*` metric families are gone.
- New CRI `v1` RPCs `CheckpointPod`/`RestorePod`; `cri-api` signal enum keys re-prefixed `SIGNAL_` (wire format unchanged).
- Kubelet logs effective config at startup — treat `nodes/logs` as sensitive.

### 05-networking
- kube-proxy nftables mode uses **netlink directly** instead of invoking `nft`.
- ipvs is deprecated and gated for removal; kube-proxy warns when `mode` is unset ahead of the nftables default switch.
- Scale fixes: one netlink dump per address family in ipvs `syncProxyRules`; no full-sync in large-cluster mode; nftables comments truncated to the kernel's 128-byte limit; conntrack cleanup for UDP Services scaled to zero.
- Apiserver `service/proxy` now uses **EndpointSlices**, not Endpoints.

### 06-storage
- **`SELinuxMount` is GA and on** — the largest behavioural storage change in this window; relabelling semantics differ from v1.34.
- In-tree Portworx removed; `git-repo` volumes disabled with no opt-in. `VolumeAttributesClass` GA-locked at `storage.k8s.io/v1`.
- Volume group snapshots and a volume health API landed; `SnapshotMetadataService` is `v1beta1`.

### 07-extensibility-security
- **Pod Certificates and ClusterTrustBundle are GA.** `PKIXPublicKey`/`ProofOfPossession` removed from PodCertificateRequest `v1`; use `spec.stubPKCS10Request`. NodeRestriction cross-checks that the Pod mounts a `podCertificate` projection for the requested signer.
- Alpha Conditional Authorization lets authorizers allow requests conditionally on request content.
- Webhooks skip auth/authz virtual resources (`tokenreviews`, `subjectaccessreviews`), matching VAP/MAP; webhook calls load-balance across endpoints under `--enable-aggregator-routing=true`.

### 08-autoscaling-and-scale
- **HPA scales to and from zero by default** in v1.37 — the report's "HPA cannot reach zero" statement is wrong.
- `metrics.k8s.io` promoted `v1beta1` → **`v1`** (no schema change).
- HPA reconciles new and spec-changed HPAs immediately rather than waiting for resync; conditions may carry `observedGeneration`.

## 6. New subsystems worth a future deep dive

**Workload-Aware Scheduling** — `scheduling.k8s.io/v1beta1` Workload, PodGroup, PodGroupTemplate and alpha CompositePodGroup; the scheduler treats a group as the unit, with `PlacementGenerate` proposing placements, `PlacementScore` ranking them and `PodGroupPostFilter` running group-level preemption under a configurable `DisruptionMode`. It exists because gang-scheduled AI/ML and batch workloads previously needed out-of-tree coscheduling plugins.

**etcd RangeStream watch-cache init** — With etcd 3.7 and `EtcdRangeStream`, each watch cache primes from one streaming RPC instead of a paginated `Range` loop, so the apiserver never materialises a full page set. That was the dominant restart-time memory spike in large clusters; paired with the GA readiness hook it changes cold-start behaviour entirely.

**Manifest-based admission control** — `AdmissionConfiguration.staticManifestsDir` loads webhook configurations and CEL policies from disk, enforcing from apiserver startup and surviving etcd unavailability. It closes the bootstrap gap where API-stored policy cannot guard the cluster before etcd is readable.

**Pod Certificates + ClusterTrustBundle (GA)** — Pods get short-lived X.509 identities via a `podCertificate` projected volume; the kubelet raises a PodCertificateRequest for a signer to fulfil, and ClusterTrustBundle distributes the anchors. NodeRestriction enforces that a node may only request a signer the Pod actually mounts — in-tree workload identity, independent of a service mesh.

**Controller staleness guards** — Five core controllers check whether their informer has observed their own most recent writes and defer syncing if not, emitting `*_stale_sync_skips_total`. The read-your-own-write gap was causing duplicate Pod creation under load; worth recording in [`patterns.md`](patterns.md).

**DRA node-allocatable resources (alpha)** — Drivers can model CPU, memory and hugepages as devices and declare per-accelerator host *overhead*, which the kubelet accounts for when sizing cgroups, OOM scores and MemoryQoS thresholds. That overhead was previously invisible to node resource accounting.

## 7. Sources

- [Kubernetes v1.37: Garhwal](https://kubernetes.io/blog/2026/08/26/kubernetes-v1-37-release/)
- [Kubernetes v1.36: ハル (Haru)](https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/)
- [Kubernetes v1.35: Timbernetes](https://kubernetes.io/blog/2025/12/17/kubernetes-v1-35-release/)
- [Kubernetes v1.35 Sneak Peek](https://kubernetes.io/blog/2025/11/26/kubernetes-v1-35-sneak-peek/)
- [Kubernetes v1.34: Of Wind & Will (baseline)](https://kubernetes.io/blog/2025/08/27/kubernetes-v1-34-release/)
- [Kubernetes Releases (dates and EOL)](https://kubernetes.io/releases/)
- [CHANGELOG-1.35.md](https://raw.githubusercontent.com/kubernetes/kubernetes/master/CHANGELOG/CHANGELOG-1.35.md)
- [CHANGELOG-1.36.md](https://raw.githubusercontent.com/kubernetes/kubernetes/master/CHANGELOG/CHANGELOG-1.36.md)
- [CHANGELOG-1.37.md](https://raw.githubusercontent.com/kubernetes/kubernetes/master/CHANGELOG/CHANGELOG-1.37.md)
- [kube_features.go @ release-1.37](https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.37/pkg/features/kube_features.go)
- [kube_features.go @ release-1.34 (baseline diff)](https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.34/pkg/features/kube_features.go)
- [apiserver kube_features.go @ release-1.37](https://raw.githubusercontent.com/kubernetes/kubernetes/release-1.37/staging/src/k8s.io/apiserver/pkg/features/kube_features.go)
- [Deprecated API Migration Guide (source markdown)](https://raw.githubusercontent.com/kubernetes/website/main/content/en/docs/reference/using-api/deprecation-guide.md)

### Verification gaps

- The v1.35–1.37 release blogs returned only navigation chrome. Names, dates and enhancement counts come from those fetches; **every per-feature stage claim comes from the CHANGELOGs and source instead**. **[documented]**
- The v1.36/v1.37 **sneak-peek blogs could not be fetched** (provenance error). No claim here rests on them. **[unverified]**
- KEP numbers are omitted rather than guessed: most CHANGELOG entries carry PR numbers only.
- The v1.37 CHANGELOG both removes `WorkloadAwarePreemption` and adds metrics behind it. Neither it nor `GangScheduling` appears in `release-1.37` `kube_features.go`, so the removal is treated as authoritative. **[inferred]**

---

<!-- nav:start -->
[← 08 Autoscaling & Scale](kubernetes-08-autoscaling-and-scale.md) · **[Index](README.md)** · →
<!-- nav:end -->
