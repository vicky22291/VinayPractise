# Popular Systems Deep Dives

Source-verified internals of three systems that come up constantly in Staff
interviews. Each folder is one system. Read the `-00-overview.md` first, it
carries the reading map for the rest.

| Folder | Baseline | Files | Diagrams |
|---|---|---|---|
| [`kubernetes/`](kubernetes/) | v1.34, deltas to v1.37 | 10 + patterns | 124 |
| [`kafka/`](kafka/) | Apache Kafka 4.3 | 10 + patterns + README | 112 |
| [`cassandra/`](cassandra/) | Apache Cassandra 5.0 | 12 + patterns | 50 |

## Navigating

Every report is wired into the series, so you can move without going back to a
file listing:

- **Prev / Index / Next** bar at the top and bottom of all 32 reports.
- **Collapsible section list** under the nav bar, linking all 413 sections.
- **Inline cross-references.** A mention of "report 05" in the prose is a live
  link, including the cross-system ones in the pattern catalogues (`C* report
  09` from a Kafka table jumps straight to the Cassandra file).
- **Index tables** in each system README and each `00-overview.md`.

Start at a system README, or jump straight to its `00-overview.md`.

| System | Start here | Pattern catalogue |
|---|---|---|
| Kubernetes | [`kubernetes-00-overview.md`](kubernetes/kubernetes-00-overview.md) | [`patterns.md`](kubernetes/patterns.md) |
| Kafka | [`kafka-00-overview.md`](kafka/kafka-00-overview.md) | [`patterns.md`](kafka/patterns.md) |
| Cassandra | [`cassandra-00-overview.md`](cassandra/cassandra-00-overview.md) | [`patterns.md`](cassandra/patterns.md) |

## What these are

Long-form reference notes, not flashcards. Every default, config name and
version claim was read out of the relevant release's source tree, and claims
are tagged `[documented]` / `[doc]` / `[inferred]` / `[unverified]` so you know
which numbers you can quote in an interview and which you cannot.

Start with `cassandra/cassandra-00-overview.md` if you want to see why that
matters. It opens by correcting three things most secondary writing about
Cassandra 5.0 gets wrong.

## Colors

All 286 diagrams were recolored to the repo legend in
[`../templates/color-legend.md`](../templates/color-legend.md). The bundles
shipped with their own palette, which conflicted with ours in two ways worth
knowing about:

- Their palette grouped nodes by **component family** (log storage, replication,
  control plane). Ours groups by **role** (client, service, store, cache,
  queue). Where a family had no matching role, the node is now green `service`.
  About 70% of nodes land there, because these systems are mostly compute.
- Their palette used **red for the control plane**. Ours reserves red for the
  thing that breaks first. All control-plane red was removed.

Red now appears on exactly five nodes, each one named as a bottleneck or SPOF
in that file's own prose:

| Node | File | Why |
|---|---|---|
| `ScheduleOne` loop | `kubernetes/kubernetes-03-scheduler.md` | Single goroutine by design, ~100-300 pods/s |
| `kube-scheduler` | `kubernetes/kubernetes-08-autoscaling-and-scale.md` | Same cycle, seen from the scale side |
| `QuorumController` | `kafka/kafka-03-kraft-controller.md` | Single-threaded `KafkaEventQueue` |
| `KafkaRequestHandlerPool` | `kafka/kafka-08-scale-and-operations.md` | First ceiling on almost every cluster |
| Partition size thresholds | `cassandra/cassandra-10-scale-operations.md` | ~100 MB / ~100k rows, then GC degrades |

How each diagram type carries color:

| Type | Count | Mechanism |
|---|---|---|
| `flowchart` | 139 | `classDef` + `class`, full 8-class legend on every one. All flow top to bottom (`TD`/`TB`) |
| `sequenceDiagram` | 86 | `box rgb(...)` participant groups, remapped to legend hexes |
| `stateDiagram-v2` | 61 | `classDef`, colored by the component family that owns the state |

State diagrams color lifecycle states by the component family that owns them,
rather than by role. A state is not a component, so the role legend does not
apply to it directly. They use the same eight colors.

## Note on `patterns.md`

Each folder has one, and they are three divergent versions of the same
cross-system catalogue rather than a clean lineage:

- `kubernetes/patterns.md` is the original, Kubernetes only.
- `kafka/patterns.md` adds a Kafka column plus a section on what Kafka
  contributes that Kubernetes does not.
- `cassandra/patterns.md` adds a Cassandra column plus an anti-entropy section,
  but does **not** contain the Kafka additions.

Read `cassandra/patterns.md` and `kafka/patterns.md` together for the full set.
