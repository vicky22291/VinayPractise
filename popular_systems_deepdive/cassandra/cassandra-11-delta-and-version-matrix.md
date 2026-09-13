# Cassandra 11 — Version Delta, Config Renames, and Vendor Divergence

**Read this before quoting any number from reports 00–10.** Everything here was verified against the `cassandra-5.0` branch (at 5.0.10-SNAPSHOT) and against the Apache release pages, not from memory.

---

<!-- nav:start -->
[← 10 Scale & Operations](cassandra-10-scale-operations.md) · **[Index](README.md)** · →
<!-- nav:end -->

<!-- toc:start -->
<details>
<summary><b>Sections in this report (9)</b></summary>

- [1. Release state as of this writing](#1-release-state-as-of-this-writing)
- [2. The three most-repeated errors about 5.0](#2-the-three-most-repeated-errors-about-50)
- [3. Feature matrix, 4.0 → 6.0](#3-feature-matrix-40--60)
- [4. Config unit suffixes — the 4.1 rename (CASSANDRA-15234)](#4-config-unit-suffixes--the-41-rename-cassandra-15234)
- [5. Complete verified 5.0 defaults reference](#5-complete-verified-50-defaults-reference)
- [6. DataStax / Astra divergence from Apache Cassandra](#6-datastax--astra-divergence-from-apache-cassandra)
- [7. Errata for reports 00–10](#7-errata-for-reports-0010)
- [8. How to re-verify this yourself](#8-how-to-re-verify-this-yourself)
- [9. Sources](#9-sources)

</details>
<!-- toc:end -->

## 1. Release state as of this writing

| Line | Status | Notes |
|---|---|---|
| **5.0** | **Latest GA.** 5.0 GA 2024-09-05; latest patch **5.0.9** (Aug 2026); 5.0.8 shipped April 2026 | Maintained until the 5.3.0 release |
| 4.1 | Previous stable | Maintained until 5.2.0 |
| 4.0 | Older stable | Maintained until 5.1.0 |
| 3.11 and earlier | EOL | Security fixes case-by-case only |
| **6.0** | **`6.0-alpha1` — not GA** | Carries CEP-21 (CMS) and CEP-15 (Accord). The release originally planned as "5.1" was renamed to 6.0 |

**Notable 5.0.x patch content**: 5.0.8 (April 2026) **backported CEP-37 Automated Repair from 6.0**, added TLS 1.3 auto-negotiation in `cassandra-stress`, and hardened `SnapshotLoader` and the data-resurrection startup check **[doc — release notes]**.

---

## 2. The three most-repeated errors about 5.0

Each was checked directly in `conf/cassandra.yaml` or Java source on the `cassandra-5.0` branch.

| Common claim | Verified reality | Where checked |
|---|---|---|
| "5.0 uses trie memtables" | **False by default.** `memtable.configurations.default: {inherits: skiplist}`. `TrieMemtable` is opt-in per table or by editing the `default` configuration | `conf/cassandra.yaml` |
| "5.0 uses the BTI SSTable format" | **False by default.** `sstable.selected_format` defaults to `big`; the file states *"The default format is `big`, the legacy SSTable format in use since Cassandra 3.0"* | `conf/cassandra.yaml` |
| "5.0 uses Unified Compaction Strategy" | **False by default.** `default_compaction` is unset; the comment states the fallback is `SizeTieredCompactionStrategy` with `min_threshold: 4`, `max_threshold: 32` | `conf/cassandra.yaml` |
| "TCM / Accord are in 5.0" | **False.** Both are 6.0 features; 6.0 is at alpha1 | Apache downloads page; CEP-21/CEP-15 |
| "`column_index_size` defaults to 4KiB" | **False.** The `4KiB` line is a commented *example*. Undefined means **64 KiB for `big`, 16 KiB for `bti`** | `conf/cassandra.yaml` |

**The practical consequence, restated from [report 00](cassandra-00-overview.md)**: an out-of-the-box 5.0 node is architecturally a well-tuned 4.1 node. The 5.0 storage-engine features are a menu you opt into.

---

## 3. Feature matrix, 4.0 → 6.0

| Feature | 4.0 | 4.1 | **5.0** | 6.0-alpha |
|---|---|---|---|---|
| `num_tokens` default | 16 | 16 | **16** | 16 |
| Unit-suffixed config names | no | **introduced** | yes | yes |
| Zero-copy (entire-SSTable) streaming | **yes** | yes | yes | yes |
| Audit logging, full query logging | **yes** | yes | yes | yes |
| Virtual tables (`system_views.*`) | **yes** | yes | yes (+ settings redaction) | yes |
| Paxos v2 | no | **yes** | yes | superseded by Accord |
| Guardrails framework | partial | **yes** | **substantially expanded** | yes |
| Pluggable memtables (CEP-11) | no | no | **yes** | yes |
| Trie memtables (CEP-19) | no | no | **yes, opt-in** | yes |
| BTI SSTable format (CEP-25) | no | no | **yes, opt-in** | yes |
| Unified Compaction Strategy (CEP-26) | no | no | **yes, opt-in** | yes |
| Storage-Attached Indexes (CEP-7) | no | no | **yes** | yes |
| Vector type + ANN (CEP-30) | no | no | **yes** | yes |
| Dynamic Data Masking (CEP-20) | no | no | **yes** | yes |
| CIDR authorizer (CEP-33) | no | no | **yes** | yes |
| JDK 17 | no | no | **yes** | yes |
| Automated repair (CEP-37) | no | no | **backported in 5.0.8** | yes |
| Transactional Cluster Metadata (CEP-21) | no | no | **no** | **yes — required** |
| Accord transactions (CEP-15) | no | no | **no** | **yes** |
| Materialized views enabled by default | no | no | **no** (`false`) | no |
| SASI enabled by default | no | no | **no** (`false`) | no |

**Removed / disabled things people still cite**: `read_repair_chance` and `dclocal_read_repair_chance` table options (removed in 4.0 — read repair now fires only on digest mismatch); Thrift and compact storage (`drop_compact_storage_enabled: false`); SASI (`sasi_indexes_enabled: false`).

---

## 4. Config unit suffixes — the 4.1 rename (CASSANDRA-15234)

4.1 introduced typed, unit-suffixed configuration names. Old names still work in 5.0 for backward compatibility, but **all `cassandra.yaml` documentation and defaults use the new form**, and this series quotes the new form throughout.

| Old (≤ 4.0) | New (4.1+, used in 5.0) | 5.0 default |
|---|---|---|
| `commitlog_sync_period_in_ms` | `commitlog_sync_period` | `10000ms` |
| `commitlog_sync_batch_window_in_ms` | `commitlog_sync_group_window` | `1000ms` (group mode) |
| `commitlog_segment_size_in_mb` | `commitlog_segment_size` | `32MiB` |
| `commitlog_total_space_in_mb` | `commitlog_total_space` | `8192MiB` (commented) |
| `memtable_heap_space_in_mb` | `memtable_heap_space` | ¼ heap (commented `2048MiB`) |
| `memtable_offheap_space_in_mb` | `memtable_offheap_space` | ¼ heap (commented `2048MiB`) |
| `max_hint_window_in_ms` | `max_hint_window` | `3h` |
| `hinted_handoff_throttle_in_kb` | `hinted_handoff_throttle` | `1024KiB` |
| `max_hints_file_size_in_mb` | `max_hints_file_size` | `128MiB` |
| `hints_flush_period_in_ms` | `hints_flush_period` | `10000ms` |
| `read_request_timeout_in_ms` | `read_request_timeout` | `5000ms` |
| `range_request_timeout_in_ms` | `range_request_timeout` | `10000ms` |
| `write_request_timeout_in_ms` | `write_request_timeout` | `2000ms` |
| `counter_write_request_timeout_in_ms` | `counter_write_request_timeout` | `5000ms` |
| `cas_contention_timeout_in_ms` | `cas_contention_timeout` | `1000ms` |
| `truncate_request_timeout_in_ms` | `truncate_request_timeout` | `60000ms` |
| `request_timeout_in_ms` | `request_timeout` | `10000ms` |
| `compaction_throughput_mb_per_sec` | `compaction_throughput` | `64MiB/s` |
| `sstable_preemptive_open_interval_in_mb` | `sstable_preemptive_open_interval` | `50MiB` |
| `stream_throughput_outbound_megabits_per_sec` | `stream_throughput_outbound` | `24MiB/s` (commented) |
| `inter_dc_stream_throughput_outbound_megabits_per_sec` | `inter_dc_stream_throughput_outbound` | `24MiB/s` (commented) |
| `column_index_size_in_kb` | `column_index_size` | undefined → 64KiB (big) / 16KiB (bti) |
| `batch_size_warn_threshold_in_kb` | `batch_size_warn_threshold` | `5KiB` |
| `batch_size_fail_threshold_in_kb` | `batch_size_fail_threshold` | `50KiB` |
| `file_cache_size_in_mb` | `file_cache_size` | `512MiB` (commented) |
| `key_cache_size_in_mb` | `key_cache_size` | blank → `min(5% heap, 100MiB)` |
| `row_cache_size_in_mb` | `row_cache_size` | `0MiB` (disabled) |
| `trickle_fsync_interval_in_kb` | `trickle_fsync_interval` | `10240KiB` |
| `dynamic_snitch_update_interval_in_ms` | `dynamic_snitch_update_interval` | `100ms` |
| `dynamic_snitch_reset_interval_in_ms` | `dynamic_snitch_reset_interval` | `600000ms` |

**Note on the unit-suffix change**: `stream_throughput_outbound` changed *units* as well as name — the old option was megabits per second, the new one is `MiB/s`. Copying a numeric value across the rename silently changes throughput by ~8×. This is the one rename that is a genuine footgun rather than cosmetic.

---

## 5. Complete verified 5.0 defaults reference

All read directly from `conf/cassandra.yaml` on `cassandra-5.0`. **Commented** means the line is commented out in the shipped file, so the value shown is the documented default that the code applies.

### Cluster and placement
| Setting | Default |
|---|---|
| `num_tokens` | `16` |
| `allocate_tokens_for_local_replication_factor` | `3` |
| `partitioner` | `org.apache.cassandra.dht.Murmur3Partitioner` |
| `endpoint_snitch` | `SimpleSnitch` ⚠️ change for production |
| `phi_convict_threshold` | `8` (commented) |
| `storage_port` | `7000` |
| `native_transport_port` | `9042` |
| `internode_compression` | `dc` |

### Durability
| Setting | Default |
|---|---|
| `commitlog_sync` | `periodic` |
| `commitlog_sync_period` | `10000ms` |
| `commitlog_segment_size` | `32MiB` |
| `commitlog_compression` | unset |
| `trickle_fsync` | `false` |
| `trickle_fsync_interval` | `10240KiB` |

### Memtables and SSTables
| Setting | Default |
|---|---|
| `memtable.configurations.default` | `inherits: skiplist` ⚠️ trie is opt-in |
| `memtable_allocation_type` | `heap_buffers` |
| `memtable_flush_writers` | `2` (single data dir) |
| `memtable_cleanup_threshold` | `1/(memtable_flush_writers+1)` — deprecated but the formula still governs |
| `sstable.selected_format` | `big` ⚠️ bti is opt-in |
| `column_index_size` | undefined → 64KiB (big) / 16KiB (bti) |
| `disk_access_mode` | `mmap_index_only` (commented) |

### Compaction
| Setting | Default |
|---|---|
| `default_compaction` | unset → `SizeTieredCompactionStrategy` (`min_threshold: 4`, `max_threshold: 32`) |
| `concurrent_compactors` | `min(disks, cores)`, capped at 8 |
| `compaction_throughput` | `64MiB/s` |
| `sstable_preemptive_open_interval` | `50MiB` |
| `unified_compaction.scaling_parameters` | `T4` |
| `unified_compaction.min_sstable_size` | `100MiB` |
| `unified_compaction.target_sstable_size` | `1GiB` |
| `unified_compaction.base_shard_count` | `4` |
| `unified_compaction.sstable_growth` | `0.333` |
| `unified_compaction.survival_factor` | `1` |

### Concurrency and timeouts
| Setting | Default |
|---|---|
| `concurrent_reads` / `concurrent_writes` / `concurrent_counter_writes` | `32` / `32` / `32` |
| `read_request_timeout` | `5000ms` |
| `range_request_timeout` | `10000ms` |
| `write_request_timeout` | `2000ms` |
| `counter_write_request_timeout` | `5000ms` |
| `cas_contention_timeout` | `1000ms` |
| `truncate_request_timeout` | `60000ms` |
| `request_timeout` | `10000ms` |

### Consistency and anti-entropy
| Setting | Default |
|---|---|
| `hinted_handoff_enabled` | `true` |
| `max_hint_window` | `3h` |
| `hinted_handoff_throttle` | `1024KiB` |
| `max_hints_delivery_threads` | `2` |
| `hints_flush_period` | `10000ms` |
| `max_hints_file_size` | `128MiB` |
| `dynamic_snitch_update_interval` | `100ms` |
| `dynamic_snitch_reset_interval` | `600000ms` |
| `dynamic_snitch_badness_threshold` | `1.0` |
| `repair_session_space` | unset → 1/16 heap |
| `stream_throughput_outbound` | `24MiB/s` (commented) |
| `inter_dc_stream_throughput_outbound` | `24MiB/s` (commented) |

### Table-level (from `TableParams.java`)
| Setting | Default |
|---|---|
| `gc_grace_seconds` | `864000` (10 days) |
| `read_repair` | `BLOCKING` |
| `bloom_filter_fp_chance` | `0.01` (STCS/UCS) / `0.1` (LCS) |
| `speculative_retry` | `99p` |
| `crc_check_chance` | `1.0` |

### Caches, backup, guardrails
| Setting | Default |
|---|---|
| `key_cache_size` | blank → `min(5% heap, 100MiB)` |
| `row_cache_size` | `0MiB` (disabled) |
| `file_cache_size` | `512MiB` (commented) |
| `auto_snapshot` | `true` |
| `auto_snapshot_ttl` | `30d` (commented) |
| `incremental_backups` | `false` |
| `snapshot_before_compaction` | `false` |
| `tombstone_warn_threshold` / `tombstone_failure_threshold` | `1000` / `100000` |
| `batch_size_warn_threshold` / `batch_size_fail_threshold` | `5KiB` / `50KiB` |
| `unlogged_batch_across_partitions_warn_threshold` | `10` |
| `sai_sstable_indexes_per_query_warn_threshold` | `32` |
| `sai_sstable_indexes_per_query_fail_threshold` | `-1` (disabled) |
| `sai_string_term_size_warn/fail_threshold` | `1KiB` / `8KiB` |
| `sai_frozen_term_size_warn/fail_threshold` | `1KiB` / `8KiB` |
| `sai_vector_term_size_warn/fail_threshold` | `16KiB` / `32KiB` |
| `cdc_enabled` | `false` |
| `materialized_views_enabled` | `false` |
| `sasi_indexes_enabled` | `false` |
| `transient_replication_enabled` | `false` |
| `drop_compact_storage_enabled` | `false` |

---

## 6. DataStax / Astra divergence from Apache Cassandra

Marked **[doc]** — established from vendor documentation and third-party migration write-ups, not from Apache source, since these products are closed or separately maintained.

| Area | Apache Cassandra 5.0 | DataStax Enterprise / Astra |
|---|---|---|
| **Default compaction** | STCS (verified in source) | **UCS is the default in Astra Serverless**; DSE historically shipped `TieredCompactionStrategy`, which UCS replaces **[doc]** |
| **SSTable format** | `big` default, `bti` opt-in | DSE introduced the **proprietary BTI format first**; Apache's `bti` (CEP-25) brings equivalent capability to open source **[doc]** |
| **Indexing** | SAI (CEP-7), open source since 5.0 | SAI originated at DataStax and shipped in DSE/Astra before Apache 5.0 |
| **Vector search** | CEP-30, `vector<float,n>` + ANN via SAI | Astra shipped vector search ahead of Apache 5.0; tuning surface and index parameters may differ **[doc]** |
| **Architecture** | Node-based, operator-managed | **Astra Serverless separates storage and compute** and does not expose the node model at all — most of [report 10](cassandra-10-scale-operations.md) does not apply |
| **Repair** | Operator-scheduled; CEP-37 in-tree from 5.0.8 | Managed by the service |
| **Config surface** | Full `cassandra.yaml` | Substantially restricted in Astra; many tunings in this series are unavailable |
| **Extras** | — | DSE adds Search (Solr), Analytics (Spark), Graph — none in Apache Cassandra |

**Practical guidance.**
- **Do not carry a default across the boundary.** "UCS is the default" is true of Astra Serverless and false of Apache 5.0. Verify against the product you are actually running.
- **Migration target.** Third-party guidance holds that Apache Cassandra 5.0 has closed the main DSE feature gaps — BTI-equivalent format, UCS replacing TieredCompactionStrategy, SAI with vector search, dynamic data masking — making 5.0 the appropriate DSE migration target today **[doc — AxonOps migration guide]**.
- **What does not port**: DSE Search, DSE Analytics, DSE Graph, and Astra's serverless storage/compute separation. These are architectural, not configuration.
- **Interview caution.** DataStax authored much of the documentation the internet indexes for "Cassandra". Where a blog states a default, check which product it means.

---

## 7. Errata for reports 00–10

Items that were checked and are worth flagging as lower confidence or as likely to change.

| Report | Item | Confidence |
|---|---|---|
| 01 | Bloom filter memory ≈ 1–2 GB per TB at fp 0.01 | **[inferred]** order-of-magnitude only; depends entirely on partition count, not bytes |
| 01 | BTI adoption effectively one-way | **[inferred]** — downgrade is technically a rewrite, but untested at scale |
| 04 | TWCS window sizing rule of thumb (TTL/25) | **[doc/community]** — not in source |
| 04 | UCS space-amplification headroom vs STCS/LCS | **[inferred]** from the sharding design |
| 06 | Gossip convergence "seconds to tens of seconds" | **[inferred]** from the 1 Hz round; no source-stated bound |
| 07 | CEP-37 configuration surface | **[low confidence]** — landed in 5.0.8 (April 2026); verify config names against your patch version's `NEWS.txt` |
| 07 | Overstreaming volume estimates | **[inferred]** — arithmetic from tree depth, not measured |
| 08 | SAI internal index structures (term dictionary, numeric tree, ANN graph family) | **[inferred]** from CEP-7/CEP-30 and behaviour; not from `cassandra.yaml` |
| 08 | SAI vector search vs dedicated vector DBs | **[inferred]** — no benchmark verified here |
| 09 | **Entire report** | **[design]** — 6.0 is at alpha1. No config name in [report 09](cassandra-09-tcm-accord.md) should be quoted as current |
| 10 | JDK 17 ~20% improvement | **[doc]** — Apache announcement claim, not independently verified |
| 10 | 5.0 density ceiling with UCS+BTI | **[doc]** — vendor claim; decide your own number from recovery-time arithmetic |
| All | Patch-level content beyond 5.0.9 | Check `NEWS.txt` for your exact version |

---

## 8. How to re-verify this yourself

```bash
git clone --branch cassandra-5.0 --depth 1 https://github.com/apache/cassandra.git
cd cassandra
grep -n "base.version" build.xml                 # which patch level the branch is at
grep -nE "^[a-z_]+:" conf/cassandra.yaml         # every uncommented default
grep -n -A6 "^# default_compaction" conf/cassandra.yaml
grep -n -A8 "^memtable:" conf/cassandra.yaml
grep -n -B4 -A6 "selected_format" conf/cassandra.yaml
grep -nE "UCS_[A-Z_]+\(" src/java/org/apache/cassandra/config/CassandraRelevantProperties.java
grep -nE "gcGraceSeconds|readRepair =" src/java/org/apache/cassandra/schema/TableParams.java
less NEWS.txt                                     # upgrade notes and per-version changes
```

**The habit worth keeping**: a default quoted from a release announcement, a blog or a book is a claim about intent. A default read out of `conf/cassandra.yaml` on the branch you are running is a fact. The gap between the two is where most of this report's corrections live.

---

## 9. Sources

- [Apache Cassandra downloads — current GA and maintenance windows](https://cassandra.apache.org/download/)
- [`apache/cassandra@cassandra-5.0`](https://github.com/apache/cassandra/tree/cassandra-5.0) — `conf/cassandra.yaml`, `NEWS.txt`, `build.xml`, and the Java sources cited in each report
- [`cassandra-6.0-alpha1` release tag](https://github.com/apache/cassandra/releases/tag/cassandra-6.0-alpha1)
- [New Features in Apache Cassandra 5.0](https://cassandra.apache.org/doc/latest/new) — the CEP-to-feature mapping
- [Apache Cassandra 5.0 announcement](https://cassandra.apache.org/_/blog/Apache-Cassandra-5.0-Announcement.html)
- [ASF announcement of Cassandra 5.0](https://news.apache.org/foundation/entry/the-apache-software-foundation-announces-apache-cassandra-5-0-the-most-advanced-secure-and-ai-ready-cassandra-yet)
- CASSANDRA-15234 — configuration unit suffixes and typed settings
- AxonOps — *Migrating from DataStax Enterprise to Open-Source Apache Cassandra* **[vendor doc, used for the DSE/Astra divergence table]**
- Instaclustr — *Exploring the key features of Cassandra 5.0* **[vendor doc, used for the Astra UCS-default claim]**

---

---

<!-- nav:start -->
[← 10 Scale & Operations](cassandra-10-scale-operations.md) · **[Index](README.md)** · →
<!-- nav:end -->
