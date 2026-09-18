# Do your Streaming ETL at Scale with Apache Spark’s Structured Streaming

- Source: https://www.databricks.com/blog/2017/09/01/streaming-etl-scale-apache-sparks-structured-streaming.html
- Published: 2017-09-01
- Authors: Tathagata Das
- Categories: announcements, data-streaming, company, events
- Images: 1 total, 1 extracted as architecture

At the [Spark Summit in San Francisco in June](https://www.databricks.com/blog/2017/06/06/simple-super-fast-streaming-engine-apache-spark.html), we announced that Apache Spark’s Structured Streaming is marked as production-ready and shared benchmarks to demonstrate its performance compared to other streaming engines.

Structured Streaming is a novel way to process streams. Not only does this new way make it easy to build end-to-end streaming applications, but it also handles all the underlying complexities for fault-tolerance. You as a developer need not worry about it.

**Summary:** Apache Spark converts a batch-like streaming query into an optimized physical plan and a series of incremental execution plans.

**Components:**

- Input stream using Spark readStream
- Kafka source
- Logical plan using Project, Filter, and Write to Parquet
- Optimized physical plan using an optimized operator
- Parquet sink
- Incremental execution plans for new data batches
- DataFrames, Datasets, and SQL

**Flows:**

- Input -> Read from Kafka: streaming records
- Read from Kafka -> Project: selected device and signal fields
- Project -> Filter: records matching signal greater than 15
- Filter -> Write to Parquet: filtered records
- Kafka Source -> Optimized Operator: Kafka input for optimization
- Optimized Operator -> Parquet Sink: optimized output
- Logical Plan -> Optimized Physical Plan: optimized query execution plan
- Optimized Physical Plan -> Incremental Execution Plans: new batches of data processed incrementally

**Numbers:** 15; t=1; t=2; t=3

```mermaid
%% Shows Spark streamification from Kafka input through incremental execution
flowchart LR
    A[Read from Kafka] -->|streaming records| B[Logical Plan]
    B -->|optimize query| C[Optimized Physical Plan]
    C -->|execute new batches| D[Incremental Execution Plans]
    A -->|Kafka input| E[Kafka Source]
    E -->|input data| F[Optimized Operator]
    F -->|optimized output| G[Parquet Sink]
    B -->|query stages| H[Project Filter Write to Parquet]
    D -->|t equals 1 2 3| I[New data batches]

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class A,E queue
    class B,H service
    class C,F,D service
    class G store
    class I queue
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2017/08/image1-1.jpg</sub>

At the [Data + AI Summit](https://www.databricks.com/dataaisummit), I will present two talks covering many aspects of Structured Streaming. The first talk covers concepts, APIs, integration with external sources and sinks, underlying incremental Spark SQL execution engine, and fault-tolerant semantics, while the second will focus on stateful stream processing using *mapGroupsWithState* APIs.

1. [Easy, Scalable, fault-tolerant Stream Processing with Structured Streaming in Apache Spark](https://www.databricks.com/dataaisummit)
2. [Deep Dive into Stateful Streaming Processing in Structured Streaming](https://www.databricks.com/dataaisummit)

Why should you attend these sessions? If you are a data engineer or data scientist who wants to turbocharge your ETL with streaming, build low-latency predictive IoT or fraud-detection applications with fast-data, and create streaming pipelines for data ingestion and real-time streaming analytics, then attend my sessions.

And see you Dublin!
