# Real-World MapReduce and Batch Systems: Architecture Survey

Research summary of how companies built and scaled MapReduce-style systems. Focus: cluster size, machine spec, concrete numbers.

---

## Google MapReduce (OSDI 2004, CACM 2008/2010)

**Cluster and Hardware:**
Google's production clusters ran on approximately 1800 machines.
https://www.usenix.org/legacy/event/osdi04/tech/full_papers/dean/dean.pdf
Each machine: dual 2 GHz Intel Xeon processors with Hyperthreading, 4 GB RAM, two 160 GB IDE disks.

**Grep Benchmark:**
Scanned 10 billion 100-byte records (92,337 pattern matches).
M=15,000 map tasks, R=1 reducer. Time not published.
https://www.usenix.org/legacy/event/osdi04/tech/full_papers/dean/dean.pdf

**Sort Benchmark:**
Sorted approximately 1 TB of data using MapReduce.
https://www.usenix.org/legacy/event/osdi04/tech/full_papers/dean/dean.pdf

**Backup Tasks (Speculative Execution):**
Backup task effect demonstrated via machine-kill experiment. When killing machines, backup tasks prevented task stragglers. Exact percentage improvement not stated in available abstracts.

**Usage (2008 CACM):**
Published in Communications of the ACM, Volume 51, Number 1, pages 107-113 (January 2008).
https://dl.acm.org/doi/pdf/10.1145/1327452.1327492

**Usage (2010 CACM):**
"MapReduce: A Flexible Data Processing Tool" (CACM 2010). Specific job/day and PB/day numbers not extracted from available sources.

---

## Google Petasort Records

**2008 Petasort:**
Sorted 1 petabyte (100-byte records) in just over 6 hours using 4000 machines.
https://research.google/blog/sorting-petabytes-with-mapreduce-the-next-episode/

**2011 Petasort (repeat experiment):**
Sorted 1 petabyte in 33 minutes using 8000 machines.
Order of magnitude improvement (12x speedup) from 2008.
https://research.google/blog/sorting-petabytes-with-mapreduce-the-next-episode/

**2011 10-Petabyte Sort:**
Sorted 10 petabytes in 6 hours 27 minutes using 8000 machines.
https://research.google/blog/sorting-petabytes-with-mapreduce-the-next-episode/

---

## Google FlumeJava (PLDI 2010)

**Overview:**
Authors: Craig Chambers, Ashish Raniwala, Frances Perry, et al.
PLDI 2010, pages 363-375.
https://dl.acm.org/doi/10.1145/1806596.1806638

Java library for building data-parallel pipelines. Deferred execution with DAG optimization. Used internally by hundreds of pipeline developers at Google.

**Impact:**
Later materialized into Google Cloud Dataflow (announced June 2014).
https://www.datanami.com/2014/06/25/google-re-imagines-mapreduce-launches-dataflow/

---

## Facebook Hive + Hadoop

**Data Growth:**
2007: 15 TB data set.
2009: 2 PB data set (133x growth in 2 years).
Daily load: routinely 15 TB per day.
https://engineering.fb.com/2009/06/10/web/hive-a-petabyte-scale-data-warehouse-using-hadoop/

**User and Job Scale:**
Hundreds of users using the system. Thousands of jobs on the cluster.
Over 700 TB of data in warehouse. More than 200 users per month.
https://engineering.fb.com/2009/06/10/web/hive-a-petabyte-scale-data-warehouse-using-hadoop/

**Later Scale (2014):**
Facebook scaled data warehouse to 300 PB by 2014 via RCFile to ORC migration.
https://engineering.fb.com/2014/04/10/core-infra/scaling-the-facebook-data-warehouse-to-300-pb/

---

## Yahoo Hadoop TeraSort Records

**2008 Benchmark:**
Owen O'Malley, Yahoo Grid Team: 1 TB sorted in 209 seconds on 910 nodes.
Previous record: 297 seconds.
https://perspectives.mvdirona.com/2008/07/hadoop-wins-terasort/

**2009 Benchmark:**
100 TB sorted in ~58 minutes (0.578 TB/minute) on 3800 nodes.
1 PB sorted in 16 hours on 3800 nodes.
Same cluster sorted 1 TB in 62 seconds.
https://www.databricks.com/blog/2014/11/05/spark-officially-sets-a-new-record-in-large-scale-sorting.html

---

## Apache Hadoop YARN (SoCC 2013)

**Hadoop 1 Limitation:**
JobTracker single point of failure. Scaling beyond 4000 nodes extremely difficult.
https://www.cse.ust.hk/~weiwa/teaching/Fall15-COMP6611B/reading_list/YARN.pdf

**YARN Improvement:**
Split JobTracker into ResourceManager (cluster resources) + ApplicationMaster (app lifecycle).
Extends scalability from 4000 to over 7000 nodes.
https://www.cse.ust.hk/~weiwa/teaching/Fall15-COMP6611B/reading_list/YARN.pdf

---

## Microsoft Dryad (EuroSys 2007)

**Scale and Design:**
Designed to scale from single multi-core machine to data centers with thousands of machines.
Demonstrated excellent performance with close-to-linear scaling on cluster experiments.
https://www.microsoft.com/en-us/research/wp-content/uploads/2007/03/eurosys07.pdf

---

## Microsoft Apollo Scheduler (OSDI 2014)

**Production Scale:**
Deployed on production clusters at Microsoft.
Handles thousands of computations with millions of tasks daily on 20,000+ machines.
https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-boutin_0.pdf

**Architecture:**
Distributed estimation-based scheduling. Global cluster info via loosely-coordinated mechanism. Opportunistic + regular tasks for high utilization and low latency.

---

## Microsoft Cosmos + SCOPE

**Scale Evolution:**
Started: petabytes to exabytes. Hundreds of thousands of jobs daily. Hundreds of thousands of machines.
Tens of thousands of SCOPE jobs execute daily, processing tens of petabytes of data.
Even single jobs consume tens of petabytes and produce similar volumes via millions of parallel tasks.
https://learn.microsoft.com/en-us/archive/blogs/seliot/microsoft-cosmos-petabytes-perfectly-processed-perfunctorily

**SCOPE Query Language:**
SQL-like scripting for distributed data processing on Cosmos.

---

## Apache Spark (NSDI 2012)

**RDD Benchmark Results:**
20x faster than Hadoop on iterative applications.
40x speedup on real-world data analytics report.
1 TB dataset scan in 5-7 seconds (interactive latency).
https://www.usenix.org/system/files/conference/nsdi12/nsdi12-final138.pdf

**Memory Advantage:**
Wikipedia full-text search: 20 seconds with disk (Hadoop), <1 second with Spark RDDs.
PageRank 30 machines: 3x speedup (in-memory), 3x more (data partitioning), 8x total vs disk systems.

---

## Databricks Spark GraySort 2014

**World Record:**
100 TB sorted in 23 minutes using 206 EC2 machines.
All sorting on disk (HDFS), not using in-memory cache.
Sort rate: 4.27 TB/minute.
https://www.databricks.com/blog/2014/11/05/spark-officially-sets-a-new-record-in-large-scale-sorting.html

**Comparison to Hadoop MapReduce:**
Hadoop previous record: 100 TB in 72 minutes on 2100 nodes.
Spark: 3x faster, 10x fewer machines.
https://www.databricks.com/blog/2014/11/05/spark-officially-sets-a-new-record-in-large-scale-sorting.html

---

## Sort Benchmark (sortbenchmark.org)

**GraySort:**
Definition: Sort rate (TB/minute) while sorting 100 TB minimum.
Input: 100-byte records, first 10 bytes random key.

**MinuteSort:**
Definition: Amount of data sortable in 60 seconds or less.

**Tencent 2016 Record:**
60.7 TB/minute (100 TB in 98.8 seconds).
512 nodes with OpenPOWER POWER8 processors, 512 GB RAM each, NVMe SSDs, 100 Gb Mellanox networking.
https://sortbenchmark.org/

**CloudSort (cost benchmark):**
2022: Exoshuffle-CloudSort sorted 100 TB for $97 (0.97/TB) on 40 i4i.4xlarge EC2 instances.

---

## LinkedIn Magnet Shuffle Service (VLDB 2020)

**Scale:**
15-18 PB of shuffle data processed daily.
Over 10,000 nodes across production clusters.
Spark workloads represent >70% of cluster compute resources.
https://www.linkedin.com/blog/engineering/open-source/introducing-magnet

**Performance Gains (sample ML job):**
Shuffle fetch wait time: 20,636 min (vanilla) -> 445 min (Magnet). 98% reduction.
Executor task runtime: 50,771 min -> 29,928 min. 41% reduction.
End-to-end job runtime: 42 min -> 31 min. 26% reduction.

**Production Impact:**
3-4x reduction in shuffle fetch wait time. 10x increase in locally-accessed shuffle data.
Reduced 100-1000+ daily shuffle failures to minimal levels.

---

## Uber Remote Shuffle Service (RSS)

**Daily Scale:**
220,000 applications handled daily.
8-10 PB of data shuffled per day.
80,000 shuffles daily.
https://www.uber.com/blog/ubers-highly-scalable-and-distributed-shuffle-as-a-service/

**Infrastructure:**
400-node RSS cluster per data center (2 data centers).
10,000+ node Spark production cluster.
Per RSS node: 80 vCores, 384 GB memory, 4 x 4 TB NVMe SSD (16 TB total).

**Performance:**
P99 read throughput: 2 TB/minute. P99 write throughput: 0.6 TB/minute.
Single jobs process up to 40 TB shuffle data.
Reduced drive wear to 12x less than planned. 90% reduction in shuffle-related failures.

---

## Alibaba Celeborn (Apache Remote Shuffle Service)

**History:**
2020: Started as Remote Shuffle Service at Alibaba.
December 2021: Open-sourced to community.
October 2022: Donated to Apache Software Foundation.
https://cwiki.apache.org/confluence/display/INCUBATOR/CelebornProposal

**Adoption:**
Used by LinkedIn, Stripe, and other companies for Spark, Flink, MapReduce, Tez.

---

## Failure Modes and Critiques

**DeWitt and Stonebraker (2008):**
"MapReduce: A major step backwards." Published January 2008.
Criticized as poor implementation, not novel, overlooking 40 years of database technology.
https://www.cs.utexas.edu/~rossbach/cs380p/papers/dewitt08blog-mapreduce-backwards.pdf

**Mantri OSDI 2010 (Microsoft Bing):**
Production MapReduce jobs suffer from stragglers.
After state-of-the-art mitigation, stragglers still 8x slower than median task.
https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Ananthanarayanan.pdf

---

## Key Takeaways

1. **Cluster Size Growth:** From 1800 machines (Google 2004) to 400,000+ machines (Microsoft Cosmos, LinkedIn Magnet).

2. **Bandwidth Explosion:** Shuffle-intensive workloads drive petabyte-scale data movement daily. Remote shuffle services (Magnet, Uber RSS, Celeborn) became critical infrastructure.

3. **Specialization:** Google evolved beyond MapReduce (FlumeJava -> MillWheel -> Dataflow). Microsoft built general-purpose schedulers (Apollo) and data platforms (Cosmos). Apache ecosystem standardized on Spark.

4. **Stragglers Remain:** Despite advances, tail latency remains problematic. Mantri, speculation, and replica scheduling all needed.

5. **Sort Benchmark:** Demonstrates system efficiency. From Hadoop 209 seconds (2008, 910 nodes) to Spark 23 minutes (2014, 206 nodes) to Tencent 98.8 seconds (2016, 512 nodes).

---

## Sources Table

| ID | URL | Source |
|----|-----|--------|
| 1 | https://www.usenix.org/legacy/event/osdi04/tech/full_papers/dean/dean.pdf | Google MapReduce OSDI 2004 paper |
| 2 | https://dl.acm.org/doi/pdf/10.1145/1327452.1327492 | Google CACM 2008: Simplified Data Processing |
| 3 | https://research.google/blog/sorting-petabytes-with-mapreduce-the-next-episode/ | Google petasort 2008-2011 blog post |
| 4 | https://dl.acm.org/doi/10.1145/1806596.1806638 | FlumeJava PLDI 2010 |
| 5 | https://engineering.fb.com/2009/06/10/web/hive-a-petabyte-scale-data-warehouse-using-hadoop/ | Facebook Hive warehouse 2009 |
| 6 | https://perspectives.mvdirona.com/2008/07/hadoop-wins-terasort/ | Yahoo Hadoop TeraSort 2008 |
| 7 | https://www.databricks.com/blog/2014/11/05/spark-officially-sets-a-new-record-in-large-scale-sorting.html | Databricks Spark GraySort 2014 |
| 8 | https://www.cse.ust.hk/~weiwa/teaching/Fall15-COMP6611B/reading_list/YARN.pdf | YARN SoCC 2013 paper |
| 9 | https://www.microsoft.com/en-us/research/wp-content/uploads/2007/03/eurosys07.pdf | Microsoft Dryad EuroSys 2007 |
| 10 | https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-boutin_0.pdf | Apollo scheduler OSDI 2014 |
| 11 | https://learn.microsoft.com/en-us/archive/blogs/seliot/microsoft-cosmos-petabytes-perfectly-processed-perfunctorily | Microsoft Cosmos blog post |
| 12 | https://www.usenix.org/system/files/conference/nsdi12/nsdi12-final138.pdf | Spark RDD NSDI 2012 |
| 13 | https://sortbenchmark.org/ | Sort Benchmark official site |
| 14 | https://www.linkedin.com/blog/engineering/open-source/introducing-magnet | LinkedIn Magnet shuffle service 2020 |
| 15 | https://www.uber.com/blog/ubers-highly-scalable-and-distributed-shuffle-as-a-service/ | Uber Remote Shuffle Service blog |
| 16 | https://cwiki.apache.org/confluence/display/INCUBATOR/CelebornProposal | Apache Celeborn proposal |
| 17 | https://www.cs.utexas.edu/~rossbach/cs380p/papers/dewitt08blog-mapreduce-backwards.pdf | DeWitt/Stonebraker MapReduce critique |
| 18 | https://www.usenix.org/legacy/event/osdi10/tech/full_papers/Ananthanarayanan.pdf | Mantri OSDI 2010 stragglers paper |
| 19 | https://www.datanami.com/2014/06/25/google-re-imagines-mapreduce-launches-dataflow/ | Google Cloud Dataflow 2014 announcement |
| 20 | https://engineering.fb.com/2014/04/10/core-infra/scaling-the-facebook-data-warehouse-to-300-pb/ | Facebook warehouse scaled to 300 PB 2014 |

---

## Spot-check corrections (editor, 2026-10-03)

| Claim above | Correct value | Source |
|---|---|---|
| Backup task effect "not stated" | OSDI 2004 §5.4: sort with backup tasks disabled took 1283 s vs 891 s, "an increase of 44% in elapsed time". After 960 s all but 5 reduce tasks were done; those 5 took 300 s more | mapreduce-osdi04.pdf §5.4 |
| Machine-kill experiment details missing | §5.5: 200 of 1746 worker processes killed; job finished in 933 s, "just an increase of 5% over the normal execution time" | same |
| Google usage table missing | Table 1, Aug 2004: 29,423 jobs, 634 s average completion, 79,186 machine-days, 3,288 TB input, 758 TB intermediate, 193 TB output, 157 workers per job, 1.2 worker deaths per job, 3,351 map and 55 reduce tasks per job. Typical large run: M = 200,000, R = 5,000 on 2,000 workers. Master state ~1 byte per map/reduce pair | same, §3.5 and §6 |
| CACM 2008 and 2010 usage numbers | Not verified: dl.acm.org and cacm.acm.org return 403 to every fetcher. Do not quote them | |
| Magnet "15-18 PB daily" | Not on the LinkedIn post. The post says "more than 10,000 nodes", Spark is "more than 70% of cluster compute", "tens of PB of daily processed data". The 98% / 41% / 26% figures are for one ML job with ~2 TB of shuffle. The VLDB paper says "Around 15% of the total Spark computation resources on our clusters are wasted due to this latency", average block "around 10s of KBs", end to end "nearly 30%" | https://www.linkedin.com/blog/engineering/open-source/introducing-magnet , https://www.vldb.org/pvldb/vol13/p3382-shen.pdf |
| Uber "90% reduction in shuffle-related failures", "12x less drive wear" | Post says container failures from shuffle "reduced to almost 95%" and SSD wear-out time went "from ~3 months to ~36 months". The 220k apps, 80k shuffles, 8 to 10 PB/day, ~400 RSS nodes per DC, 80 vCores / 384 GB / 4 x 4 TB NVMe, ~40 TB single shuffle and P99 2 TB/min read, 0.6 TB/min write are confirmed | Uber post (WebFetch) |
| Mantri "stragglers still 8x slower" | Paper abstract: outliers "inflate the completion time of jobs by 34% at median"; Mantri "reduces the completion time of jobs by 32%" | Ananthanarayanan.pdf |
| Riffle | Paper: "up to a 10x reduction in the number of shuffle I/O requests and 40% improvement in the end-to-end job completion time"; average request size shrinks from 1.7 MB to 50 KB as tasks grow | riffle-eurosys18.pdf |
