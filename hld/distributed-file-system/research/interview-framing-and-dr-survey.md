# Research: how the question is asked, and cross-DC / DR patterns

Raw research notes (Sep 2026). Claims carry a source URL. Used as input to `solution.md`, `edge-cases.md`, and `deep-dives/disaster-recovery.md`. Not polished study material.

## A. How the question is asked and graded

### Prompt wording candidates report
- "Design a distributed file system": hierarchical, immutable file storage and mutable directory operations across hundreds of petabytes for thousands of customers. https://www.hellointerview.com/community/questions/distributed-file-system/cm72f6jsq00s0117g6xf78mxg
- "Design Dropbox / Google Drive backend". https://medium.com/@bugfreeai/google-system-design-interview-designing-a-file-storage-service-like-dropbox-or-google-drive-f35c6d79b111
- "Design GFS or HDFS" at Google, Meta, Uber. https://leetcode.com/discuss/interview-question/system-design/1325960/gfs-google-file-system-design-reviewscommentsthoughts

### Follow-ups interviewers ask
- Leader dies after acking a write but before replicating it. https://grokkingtechcareer.substack.com/p/distributed-file-storage
- Rename atomically across directory shards. Expected: single leader serializes, or a multi-step protocol with a defined visible intermediate state.
- Storage node dies mid-upload. Expected: recovery timeline, re-replication targets, does repair flood the network.
- Shard 10 B files of metadata. https://www.systutorials.com/colossus-successor-to-google-file-system-gfs/
- Network partition between replicas, split brain. Ceph stretch needs about 10 ms RTT between sites. https://ceph.io/en/news/blog/2025/stretch-cluuuuuuuuusters-part2/
- Upgrade or move data between DCs with zero downtime. https://www.tryexponent.com/blog/meta-system-design-interview

### Mechanisms interviewers look for
- WAL before visibility, leases with time-bound authority, fencing tokens, W + R > N quorum reasoning, chunk versioning, an explicit consistency model with the inconsistency window described. https://medium.com/@mayank.sharma2796/achieving-data-consistency-in-distributed-systems-leases-and-fencing-a6ca319a0e99

### Common rejection reasons
1. Vague consistency claims with no description of what a user sees during the window. https://designgurus.substack.com/p/why-eventually-consistent-is-the
2. No failure analysis. Leader death, partition, node loss treated as rare.
3. Shard key optimises one access pattern and breaks another (rename across directories).
4. No operational detail: repair bandwidth caps, under-replication queue, backpressure. https://grokkingtechcareer.substack.com/p/distributed-file-storage
5. Dropbox variant only: no content-addressed chunking or delta sync. https://designgurus.substack.com/p/system-design-interview-question-e46

### Requirement lists from prep sites
- Hello Interview / systemdesignhandbook: upload and retrieval across hundreds of PB, directory create / rename / delete, immutable files plus mutable directories, multi-tenancy. https://systemdesignhandbook.com/blog/distributed-file-storage/
- NFR: strong for metadata (rename, delete), 99.9%+ availability, RPO 15 min cross-region typical, sub-second metadata at billions of files. https://systemdesignhandbook.com/guides/design-dropbox/

### Staff vs Senior on this problem
- Refuse features: "do we need RPO 0 cross-region, or is async enough?"
- Blast radius per shard: "one metadata shard down affects ~1% of files".
- Migration with rollback, 3 am pager list, cost of EC vs replication, fail open vs fail closed when metadata is unreachable. https://www.hellointerview.com/blog/staff-level-system-design

## B. Cross-DC and DR patterns

### Colossus
- Each cluster is single-datacenter. Cross-DC replication is done by layers above the file system. https://cloud.google.com/blog/products/storage-data-transfer/a-peek-behind-colossus-googles-file-system
- Metadata in Bigtable, Paxos-replicated inside the DC. Erasure coding for bulk data at about 1.5x overhead. https://news.ycombinator.com/item?id=11713406
- No atomic move across metadata shards. https://www.systutorials.com/colossus-successor-to-google-file-system-gfs/

### Spanner (the reference for sync cross-region)
- Paxos commit within region about 5 ms, about 9 ms including leader work; cross-continent adds RTT, 100 ms and up. https://research.google.com/archive/spanner-osdi2012.pdf

### Tectonic
- One cluster per datacenter. Tolerates host, rack, power domain failure. Geo-replication is the tenant's job (built above Tectonic). https://engineering.fb.com/2021/06/21/data-infrastructure/tectonic-file-system/

### Azure Storage
| Option | Copies | RPO | Failover |
|---|---|---|---|
| LRS | 3 sync in one DC | 0 | n/a |
| ZRS | 3 sync across 3 AZs | 0 | automatic |
| GRS | 3 sync primary + 3 async secondary | typically < 15 min, no SLA | manual account failover, may lose data |
https://learn.microsoft.com/en-us/answers/questions/1142969/rto-and-rpo-of-lrs-and-grs-storage-accounts

### HDFS
- No native cross-DC replication. DistCp copies between clusters. Cloudera recommends < 80 ms RTT for replication jobs; tested up to 360 ms with heavy degradation. https://docs-archive.cloudera.com/documentation/enterprise/6/6.3/topics/cm_bdr_hdfs_replication.html
- `.snapshot` is copy-on-write metadata, blocks are shared with the parent; cheap to take, still lives in the same cluster. https://issues.apache.org/jira/browse/HDFS-5442
- JournalNodes across DCs would put WAN latency on every edit. [unverified as a documented recommendation, but follows from the QJM design]

### Ceph
- Stretch cluster: 2 data sites + 1 monitor-only tiebreaker. Max ~10 ms RTT between data sites, tiebreaker tolerates ~100 ms. Replication size 4. RPO 0. https://ceph.io/en/news/blog/2025/stretch-cluuuuuuuuusters-part2/ and part3
- RBD mirroring: journal-based roughly doubles write latency; snapshot-based is async with minutes of RPO. https://docs.ceph.com/en/quincy/rbd/rbd-mirroring/

### The principle
- Sync cross-region replication adds roughly +80 to 100 ms per write. https://www.kai-waehner.de/blog/2025/08/04/multi-region-kafka-using-synchronous-replication-for-disaster-recovery-with-zero-data-loss-rpo0/
- "Avoiding coordination is the one fundamental thing that allows us to build distributed systems that out-scale a single machine." Marc Brooker. https://brooker.co.za/blog/2023/10/18/optimism.html
- Do we really need RPO 0: https://medium.com/@siddontang/do-we-really-need-rpo-0-for-regional-disaster-recovery-for-database-services-3884b676d940

### Numbers to quote
| Scenario | Number |
|---|---|
| Paxos commit inside a DC | 5 to 9 ms |
| Sync cross-region write penalty | +80 to 100 ms |
| Azure GRS RPO | < 15 min typical |
| Ceph stretch site RTT | <= 10 ms |
| HDFS DistCp RTT guidance | < 80 ms |
| Ceph journal mirroring | ~2x write latency |
