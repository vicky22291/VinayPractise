# Apache Spark Officially Sets a New Record in Large-Scale Sorting

- Source: https://www.databricks.com/blog/2014/11/05/spark-officially-sets-a-new-record-in-large-scale-sorting.html
- Published: 2014-11-05
- Authors: Reynold Xin
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

A month ago, we shared with you our entry to the 2014 Gray Sort competition, a 3rd-party benchmark measuring how fast a system can sort 100 TB of data (1 trillion records). Today, we are happy to announce that our entry has been reviewed by the benchmark committee and we have officially won the [Daytona GraySort contest](http://sortbenchmark.org/)!

In case you missed our [earlier blog post](https://www.databricks.com/blog/2014/10/10/spark-petabyte-sort.html), using Spark on 206 EC2 machines, we sorted 100 TB of data on disk in 23 minutes. In comparison, the previous world record set by Hadoop MapReduce used 2100 machines and took 72 minutes. This means that Apache Spark sorted the same data **3X faster** using **10X fewer machines**. All the sorting took place on disk ([HDFS](https://www.databricks.com/glossary/hadoop-distributed-file-system-hdfs)), without using Spark’s in-memory cache. This entry tied with a UCSD research team building high performance systems and we jointly set a new world record.

|  | **Hadoop MR Record** | **Spark Record** | **Spark 1 PB** |
|---|---|---|---|
| Data Size | 102.5 TB | 100 TB | 1000 TB |
| Elapsed Time | 72 mins | 23 mins | 234 mins |
| # Nodes | 2100 | 206 | 190 |
| # Cores | 50400 physical | 6592 virtualized | 6080 virtualized |
| Cluster disk throughput | 3150 GB/s (est.) | 618 GB/s | 570 GB/s |
| Sort Benchmark Daytona Rules | Yes | Yes | No |
| Network | dedicated data center, 10Gbps | virtualized (EC2) 10Gbps network | virtualized (EC2) 10Gbps network |
| **Sort rate** | **1.42 TB/min** | **4.27 TB/min** | **4.27 TB/min** |
| **Sort rate/node** | **0.67 GB/min** | **20.7 GB/min** | **22.5 GB/min** |

Named after Jim Gray, the benchmark workload is resource intensive by any measure: sorting 100 TB of data following the strict rules generates 500 TB of disk I/O and 200 TB of network I/O. Organizations from around the world often build dedicated sort machines (specialized software and sometimes specialized hardware) to compete in this benchmark.

Winning this benchmark as a general, fault-tolerant system marks an important milestone for the Spark project. It demonstrates that Spark is fulfilling its promise to serve as a faster and more scalable engine for data processing of all sizes, from GBs to TBs to PBs. In addition, it validates the work that we and others have been contributing to Spark over the past few years.

Since the inception of Databricks, we have devoted much effort to improve the scalability, stability and performance of Spark. This benchmark builds upon some of our major recent work in Spark, including sort-based shuffle ([SPARK-2045](https://issues.apache.org/jira/browse/SPARK-2045)), the new Netty-based transport module ([SPARK-2468](https://issues.apache.org/jira/browse/SPARK-2468)), and external shuffle service ([SPARK-3796](https://issues.apache.org/jira/browse/SPARK-3796)). The former has been released in Apache Spark 1.1, and the latter two will be part of the upcoming Apache Spark 1.2 release.

You can read [our earlier blog post](https://www.databricks.com/blog/2014/10/10/spark-petabyte-sort.html) to learn more about our winning entry to the competition. Also expect future blog posts on these major new Spark features.

Finally, we thank Aaron Davidson, Norman Maurer, Andrew Wang, Min Zhou, the EC2 and EBS teams from Amazon Web Services, and the Spark community for their help along the way. We also thank the benchmark committee members Chris Nyberg, Mehul Shah, and Naga Govindaraju for their support.
