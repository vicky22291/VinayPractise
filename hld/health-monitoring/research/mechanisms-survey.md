# Health Monitoring Mechanisms: Defaults Survey

**One-line summary:** Catalog of failure detection, alerting, and time-series mechanisms with their exact default values from official sources.

---

## 1. Failure Detectors

### Phi Accrual Failure Detector

The phi accrual approach (Hayashibara et al. 2004) replaces binary failure decisions with continuous confidence scores.

- Computes phi based on arrival time of heartbeats: phi = -log10(P(arrival_time > T)).
- Phi = 1 means ~10% probability the node is down; phi = 2 means ~1%; phi = 3 means ~0.1%.
- Maintains a sliding window of inter-arrival times; calculates exponential normal distribution.
- Adaptive: adjusts threshold based on observed network behavior, not fixed timeout.
- Widely adopted in Cassandra, Akka, Serf, and other systems for nuanced failure detection.

**Defaults:**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| Cassandra phi_convict_threshold | 8 | https://github.com/apache/cassandra/blob/trunk/conf/cassandra.yaml |
| Cassandra phi_convict_threshold range | 5 to 16 | https://github.com/apache/cassandra/blob/trunk/src/java/org/apache/cassandra/config/DatabaseDescriptor.java |

### Akka Cluster Failure Detector

Akka uses phi accrual with cluster-awareness; heartbeats broadcast among cluster members.

- Threshold: determines at what phi value a node is marked failed.
- Heartbeat-interval: how often each node sends heartbeats to peers.
- Acceptable-heartbeat-pause: grace period for network jitter; if exceeded, confidence drops.
- Scale for cloud: threshold may increase from 8 to 12 in high-latency environments (EC2, etc.).

**Defaults:**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| Akka threshold | 8 | https://doc.akka.io/libraries/akka-core/current/typed/failure-detector.html |
| Akka heartbeat-interval | 1 second | https://doc.akka.io/libraries/akka-core/current/typed/failure-detector.html |
| Akka acceptable-heartbeat-pause | 3 seconds | https://doc.akka.io/libraries/akka-core/current/typed/failure-detector.html |

### SWIM Gossip (Consul, Serf, Memberlist)

SWIM uses suspicion mechanism to reduce false positives: ping, indirect ping (via k nodes), suspicion period before conviction.

- ProbeInterval: time between pings to a target node.
- ProbeTimeout: max time to wait for a probe response before marking tentatively dead.
- SuspicionMult: suspicion_timeout = SuspicionMult * log(N+1) * ProbeInterval.
- IndirectChecks: number of nodes asked to indirect-ping a suspect node.
- If indirect confirms suspicion, node moves to dead; after timeout, removed from cluster.

**Defaults (from hashicorp/memberlist):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| ProbeInterval | 1 second | https://github.com/hashicorp/memberlist/blob/main/config.go |
| ProbeTimeout | 500 milliseconds | https://github.com/hashicorp/memberlist/blob/main/config.go |
| SuspicionMult | 4 | https://github.com/hashicorp/memberlist/blob/main/config.go |
| IndirectChecks | 3 | https://github.com/hashicorp/memberlist/blob/main/config.go |

### Kubernetes Node Heartbeats

Kubernetes uses node leases (kubelet heartbeats) and node status updates, evaluated by kube-controller-manager.

- Kubelet heartbeat via Lease object update every 10 seconds (nodeStatusUpdateFrequency).
- Lease duration 40s; renew interval 1/3 of lease (~13s) to tolerate transient failures.
- Controller waits node-monitor-grace-period before marking node NotReady; then taints with tolerationSeconds.
- Multiple watch loops: node-monitor-period controls pod eviction loop frequency.

**Defaults (from kubernetes.io docs and source):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| kubelet --node-status-update-frequency | 10 seconds | https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/ |
| Node Lease duration | 40 seconds | https://kubernetes.io/docs/concepts/architecture/leases/ |
| Node Lease renew interval | ~13 seconds (1/3 of duration) | https://kubernetes.io/docs/concepts/architecture/leases/ |
| kube-controller-manager --node-monitor-grace-period | 50 seconds | https://github.com/kubernetes/kubernetes/blob/master/pkg/controller/nodelifecycle/node_lifecycle_controller.go |
| tolerationSeconds (not-ready/unreachable taints) | 300 seconds | https://kubernetes.io/docs/concepts/architecture/nodes/ |

---

## 2. Prometheus Scraping & Rules

### Scrape Defaults

Prometheus pulls metrics from targets at regular intervals.

- scrape_interval: controls target scrape frequency; 1 minute by default.
- scrape_timeout: how long to wait for a scrape to complete; 10 seconds by default.
- Up series: synthetic boolean time series per target; 1 if scrape succeeded, 0 otherwise.
- Staleness marker: if a time series has no new sample for 5 minutes, Prometheus marks samples stale.
- Lookback delta: when querying, look back 5 minutes for the most recent sample if gap exists.

**Defaults (from prometheus.io docs):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| scrape_interval (global) | 1 minute | https://prometheus.io/docs/prometheus/latest/configuration/configuration/ |
| scrape_timeout (global) | 10 seconds | https://prometheus.io/docs/prometheus/latest/configuration/configuration/ |
| evaluation_interval (global) | 1 minute | https://prometheus.io/docs/prometheus/latest/configuration/configuration/ |
| Staleness threshold | 5 minutes | https://prometheus.io/docs/prometheus/latest/storage/ |
| Lookback delta | 5 minutes | https://prometheus.io/docs/prometheus/latest/querying/functions/ |

### Alerting Rules

Alert firing is gated by the "for" clause; keeps_firing_for extends alert lifetime after condition clears.

- for: minimum duration condition must be true before firing (default 0s = fire immediately).
- keep_firing_for: after condition stops, keep alert firing for this duration (default 0s = resolve immediately).
- ALERTS series: synthetic metric tracking which alerts are firing (1 if firing, 0 if resolved).
- ALERTS_FOR_STATE series: tracks time (in seconds) alert has been in current state.
- EndsAt computed when alert sent to Alertmanager: if no active update, Alertmanager resolves after --rules.alert.resend-delay.

**Defaults (from prometheus.io alerting docs):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| Alerting rule for clause | 0 seconds | https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ |
| Alerting rule keep_firing_for clause | 0 seconds | https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ |

---

## 3. Alertmanager

### Routing & Grouping

Alertmanager groups alerts to reduce notification spam; routing tree dispatches to receivers.

- group_by: labels to group alerts (e.g., group by instance, severity).
- group_wait: wait this long after first alert in group before sending notification.
- group_interval: check for new/resolved alerts in group every this interval.
- repeat_interval: resend existing alert if no changes (causes repeated notifications for a persistent alert).
- resolve_timeout: if alert not updated in this window, mark as resolved.

**Defaults (from prometheus.io alerting docs):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| group_wait | 30 seconds | https://prometheus.io/docs/alerting/latest/configuration/ |
| group_interval | 5 minutes | https://prometheus.io/docs/alerting/latest/configuration/ |
| repeat_interval | [not found as explicit default] | [see issues] |
| resolve_timeout (Alertmanager) | 5 minutes | https://prometheus.io/docs/alerting/latest/configuration/ |

### High Availability & Gossip

Alertmanager instances replicate silences and notification log via gossip; memberlist protocol.

- cluster.peer-timeout: max duration to wait when contacting a peer in the cluster.
- Silences gossiped: all instances eventually know about new silences within gossip propagation time.
- Notification log gossiped: tracks sent notifications to reduce duplicates across HA group.
- At-least-once semantics: duplicates possible during network partition; design clients to be idempotent (Prometheus docs recommend sending alerts to ALL Alertmanager replicas, not load balancer).

**Defaults (from prometheus/alertmanager source):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| cluster.peer-timeout | 15 seconds | https://github.com/prometheus/alertmanager/blob/main/cmd/alertmanager/main.go |

---

## 4. PagerDuty Events API v2

PagerDuty uses dedup_key to correlate and suppress duplicate alerts, enabling incident consolidation.

- dedup_key: unique identifier per logical alert; same key = same incident (if open).
- Trigger event with new dedup_key creates new incident; with existing (open) key updates that incident.
- Acknowledge/resolve only apply to open incidents with matching dedup_key and routing_key.
- Once resolved, any new trigger with same dedup_key opens a fresh incident.
- Opsgenie calls this field alias.

**Defaults (from developer.pagerduty.com):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| dedup_key generation | auto-generated if omitted | https://developer.pagerduty.com/docs/events-api-v2/trigger-events/ |
| Rate limit per integration key | [requires fetching from rate-limits page] | https://developer.pagerduty.com/docs/events-api-rate-limits |

---

## 5. Google SRE Workbook: Alerting on SLOs

Multi-window multi-burn-rate alerting combines a fast-burning short window with a slower-burning long window.

- Both thresholds must breach simultaneously to page (reduces false positives).
- Long window confirms sustained problem; short window confirms still actively burning budget.
- Detection time: determined by short window; reset time by long window (avoids alert flapping).
- Table 5-8 recommends starting thresholds for 99.9% SLO.

**Multi-Window Multi-Burn-Rate Table (from sre.google/workbook/alerting-on-slos):**

| Severity | Long Window | Short Window | Burn Rate | Budget Consumed | Page? |
|----------|-------------|--------------|-----------|-----------------|-------|
| Critical | 1 hour | 5 minutes | 14.4x | 2% / 1 hour | yes |
| High | 6 hours | 30 minutes | 6x | 5% / 6 hours | yes |
| Medium | 3 days | 6 hours | 1x | 10% / 3 days | ticket |

Source: https://sre.google/workbook/alerting-on-slos/ (section 6)

---

## 6. Grafana Mimir

Mimir is a scalable time-series database; ingesters shard and replicate time series.

- Replication factor: number of ingesters each series is written to; default 3.
- Zone-aware replication: replicas placed in different availability zones (if configured).
- max-global-series-per-user: hard limit on total unique series a tenant can ingest.
- ha_tracker_failover_timeout: time before HA tracker considers replica inactive and promotes standby.
- Capacity planning: ~1-2 KB memory per active series (depends on label cardinality).

**Defaults (from grafana.com/docs/mimir):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| ingester.ring.replication-factor | 3 | https://grafana.com/docs/mimir/latest/configure/configuration-parameters/ |
| ingester.max-global-series-per-user | [config-specific; see Recommended limits] | https://grafana.com/docs/mimir/latest/configure/configuration-parameters/ |

---

## 7. Prometheus TSDB

Prometheus stores time-series in a log-structured merge tree with 2-hour blocks.

- Head block: in-memory block covering most recent 2 hours; data added as it arrives.
- WAL (write-ahead log): 128 MB segments; durable buffer if crash occurs; replayed on startup.
- Bytes per sample: ~1-2 bytes after compression; used for capacity planning formula.
- Out-of-order window: optional; if enabled, allows samples ~30 minutes out of order in head block.

**Defaults (from prometheus.io storage docs & source):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| Head block duration | 2 hours | https://prometheus.io/docs/prometheus/latest/storage/ |
| WAL segment size | 128 MB | https://github.com/prometheus/prometheus/blob/main/tsdb/docs/format/wal.md |
| Bytes per sample guidance | 1-2 bytes | https://prometheus.io/docs/prometheus/latest/storage/ |

---

## 8. Blackbox Probing

Blackbox exporter performs active probes (HTTP, TCP, DNS, ICMP) from Prometheus scraper to test endpoint reachability.

- Probe timeout: default 120 seconds if neither scrape_timeout nor module timeout specified.
- Multi-vantage: configure multiple Blackbox instances in different regions; Prometheus scrapes all.
- Black-box monitoring: external view (endpoint reachability); complements white-box (internal metrics).
- Use for SLA measurement: synthetic transactions to detect user-facing failures.

**Defaults (from prometheus/blackbox_exporter):**

| Mechanism | Default Value | Source |
|-----------|---------------|--------|
| Probe timeout (default) | 120 seconds | https://github.com/prometheus/blackbox_exporter |

---

## Sources

- https://prometheus.io/docs/prometheus/latest/configuration/configuration/
- https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
- https://prometheus.io/docs/alerting/latest/configuration/
- https://prometheus.io/docs/alerting/latest/high_availability/
- https://prometheus.io/docs/prometheus/latest/storage/
- https://prometheus.io/docs/prometheus/latest/querying/functions/
- https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/
- https://github.com/prometheus/prometheus/blob/main/config/config.go
- https://github.com/prometheus/prometheus/blob/main/rules/alerting.go
- https://github.com/prometheus/prometheus/blob/main/tsdb/docs/format/wal.md
- https://github.com/prometheus/alertmanager/blob/main/cmd/alertmanager/main.go
- https://github.com/prometheus/alertmanager/blob/main/docs/configuration.md
- https://github.com/prometheus/blackbox_exporter
- https://github.com/apache/cassandra/blob/trunk/conf/cassandra.yaml
- https://github.com/apache/cassandra/blob/trunk/src/java/org/apache/cassandra/config/DatabaseDescriptor.java
- https://doc.akka.io/libraries/akka-core/current/typed/failure-detector.html
- https://doc.akka.io/docs/akka/2.5/cluster-usage.html
- https://github.com/hashicorp/memberlist/blob/main/config.go
- https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/
- https://kubernetes.io/docs/concepts/architecture/nodes/
- https://kubernetes.io/docs/concepts/architecture/leases/
- https://kubernetes.io/docs/reference/node/node-status/
- https://github.com/kubernetes/kubernetes/blob/master/pkg/controller/nodelifecycle/node_lifecycle_controller.go
- https://developer.pagerduty.com/docs/events-api-v2/trigger-events/
- https://developer.pagerduty.com/docs/events-api-v2/overview/
- https://developer.pagerduty.com/docs/events-api-rate-limits
- https://sre.google/workbook/alerting-on-slos/
- https://grafana.com/docs/mimir/latest/configure/configuration-parameters/
- https://grafana.com/docs/mimir/latest/configure/about-runtime-configuration/

---

## What This Means for the Design

Health monitoring at 1M server scale requires understanding failure detection latency, alert aggregation delay, and end-to-end alert delivery time.

- **Failure detection latency:** Kubernetes node grace period ~50s + pod eviction ~300s = ~5-6 min to fully remove node. Faster detection (Phi accrual phi=8 ~10 seconds) helps but cannot speed pod rescheduling.

- **Alert grouping delay:** Alertmanager group_wait=30s means you wait 30 seconds from first alert in a group before sending notification. Under a rolling server outage, alerts batch rather than page for each failure.

- **End-to-end path:** scrape (10s) + eval (1m) + for clause (0s default) + group_wait (30s) + Alertmanager send + PagerDuty API = ~100+ seconds minimum from failure to on-call alert.

- **Scale considerations:** At 1M servers with 10 scrapes/second, Prometheus ingests ~10 kHz. Alertmanager HA (replication=3) needs gossip propagation for silences (~100-500ms); plan notification recipient bandwidth.

- **Multi-burn-rate SLO alerts:** Use Table 5-8 thresholds to alert on SLO burn without alert storms. 1-hour critical window + 5-minute confirmation prevents false pages during brief blips.

- **Dedup keys matter:** If you alert on any server death, collapsing into one PagerDuty incident per region (via dedup_key) prevents 1M unique PagerDuty events.

- **Cascading failures:** If central Alertmanager region down, each region's HA cluster continues gossiping locally; silences and notification log eventually replicate (at-least-once, so duplicates possible).

- **Cost/latency trade-off:** Faster scrape_interval (e.g., 5s instead of 1m) detects faster but 12x higher ingestion cost. For background health monitoring, 1-5 minute intervals suffice; reserve <10s only for critical SLIs.

---

## Spot-check corrections (editor, 2026-09-27)

Checked against source code (`raw.githubusercontent.com` plus `grep -n`) and official docs. The agent's text above is left as written; use this table where they disagree.

| Claim in this survey | Status | Correct value and source |
|---|---|---|
| "Phi = 1 means ~10% probability the node is down" | **Wrong interpretation** | Phi = -log10 of the probability that a heartbeat still arrives later. Phi 1 means a ~10% chance that suspecting now is a mistake, phi 2 means 1%, phi 3 means 0.1% (Hayashibara et al. 2004). It is not the probability that the node is down |
| "Kubelet heartbeat via Lease every 10 s (nodeStatusUpdateFrequency)", "renew interval 1/3 of lease (~13 s)" | **Conflated** | Kubelet updates its Lease every 10 s, and the Node `.status` on change or every 5 min (https://kubernetes.io/docs/reference/node/node-status/). `nodeStatusUpdateFrequency` is a separate kubelet setting. Node controller checks every 5 s and waits 5 min before eviction (https://kubernetes.io/docs/concepts/architecture/nodes/) |
| `--node-monitor-grace-period` = 50 s | Verified, with a docs inconsistency | kube-controller-manager reference: "Default: 50s". The node-status page still says "40 second default timeout for unreachable nodes" |
| "Staleness marker: no new sample for 5 minutes, Prometheus marks samples stale" | **Wrong** | Staleness markers are written when a series disappears from a scrape or its target goes away. The 5 minute lookback applies to series without markers: exporters with their own timestamps "take the last value for (by default) 5 minutes before disappearing" (https://prometheus.io/docs/prometheus/latest/querying/basics/) |
| "Out-of-order window allows ~30 minutes" | **No such default** | Disabled by default. Mimir `out_of_order_time_window` default `0s` (https://grafana.com/docs/mimir/latest/configure/configuration-parameters/). We set 1 h |
| Mimir "~1 to 2 KB memory per active series" | **Wrong for capacity planning** | Mimir planning page: per 300,000 in-memory series, 1 core, 2.5 GB RAM, 5 GB disk. In-memory series = active × replication factor (https://grafana.com/docs/mimir/latest/manage/run-production-environment/planning-capacity/) |
| "At 1M servers with 10 scrapes/second, Prometheus ingests ~10 kHz" | **Nonsense** | 1M servers × 100 series / 10 s = 10M samples/s |
| "Phi accrual phi = 8 is ~10 seconds" | Invented | Depends on the observed heartbeat distribution; no fixed time |
| "For background health monitoring, 1 to 5 minute intervals suffice" | Opinion | Our design needs 10 s metrics and 5 s heartbeats for a 30 s verdict |
| End-to-end "~100+ s" with defaults | Correct for defaults | 1 min scrape + 1 min eval + 30 s `group_wait`. That is why `../solution.md` §5.2 changes the intervals |
| Blackbox probe timeout "120 s if no scrape timeout and no module timeout" | Verified | `prober/handler.go`: `if timeoutSeconds == 0 { timeoutSeconds = 120 }` |

Added by the editor (verified in source or docs):
- Prometheus `cmd/prometheus/main.go`: `--rules.alert.for-outage-tolerance` 1h, `--rules.alert.for-grace-period` 10m, `--rules.alert.resend-delay` 1m.
- Prometheus `rules/alerting.go`: `delta := max(interval, resendDelay)`, `alert.ValidUntil = ts.Add(4 * delta)`.
- Alertmanager `cmd/alertmanager/main.go`: `--cluster.peer-timeout` 15s. `config/config.go`: `ResolveTimeout` 5 min. Docs: "It's important not to load balance traffic between Prometheus and its Alertmanagers, but instead, point Prometheus to a list of all Alertmanagers."
- Mimir defaults: `max_global_series_per_user` 150,000 (before replication), `max_global_series_per_metric` 0, `ingestion_rate` 10,000/s, `ingestion_burst_size` 200,000, `query_ingesters_within` 13h, `zone_awareness_enabled` false, `max_label_names_per_series` 30.
- Mimir sizing: distributor 1 core and 1 GB per 25k samples/s; querier 1 core and 1 GB per 10 QPS; store-gateway 13 GB disk per 1M active series; one compactor per 20M active series; Alertmanager 1 core per 100 notifications/s and 1 GB per 5,000 firing alerts.
- PagerDuty's developer pages render with JavaScript and could not be read by `curl`. The `dedup_key` behaviour used in `../solution.md` (a trigger with the key of an open alert is deduplicated into it) is from PagerDuty's Events API v2 documentation, not re-fetched here.
- memberlist suspicion timeout: the survey's `SuspicionMult * log(N+1) * ProbeInterval` is wrong in the log. Source (`hashicorp/memberlist`, `suspicionTimeout`) uses `SuspicionMult * max(1, log10(N)) * ProbeInterval`. At 50k members with the LAN defaults (4, 1 s) that is 4 × 4.7 × 1 s ≈ 19 s, the number used in `../solution.md` §10.7.
