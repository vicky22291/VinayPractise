# Event-time Aggregation and Watermarking in Apache Spark’s Structured Streaming

*Part 4 of Scalable Data @ Databricks*

- Source: https://www.databricks.com/blog/2017/05/08/event-time-aggregation-watermarking-apache-sparks-structured-streaming.html
- Published: 2017-05-08
- Authors: Tathagata Das
- Categories: engineering, open-source, data-engineering
- Images: 5 total, 5 extracted as architecture

*This is the fourth post in a [multi-part series](https://www.databricks.com/blog/2017/01/19/real-time-streaming-etl-structured-streaming-apache-spark-2-1.html) about how you can perform complex [streaming analytics](https://www.databricks.com/glossary/streaming-analytics) using Apache Spark.*

---

[Continuous applications](https://www.databricks.com/blog/2016/07/28/continuous-applications-evolving-streaming-in-apache-spark-2-0.html) often require near real-time decisions on real-time aggregated statistics—such as health of and readings from IoT devices or detecting anomalous behavior. In this blog, we will explore how easily streaming aggregations can be expressed in Structured Streaming, and how naturally late, and out-of-order data is handled.

## Streaming Aggregations

Structured Streaming allows users to express the same streaming query as a batch query, and the Spark SQL engine incrementalizes the query and executes on streaming data. For example, suppose you have a streaming [DataFrame](https://www.databricks.com/blog/2015/02/17/introducing-dataframes-in-spark-for-large-scale-data-science.html) having events with signal strength from IoT devices, and you want to calculate the running average signal strength for each device, then you would write the following Python code:

This code is no different if eventsDF was a DataFrame on static data. However, in this case, the average will be continuously updated as new events arrive. You choose different *[output modes](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#starting-streaming-queries)* for writing the updated averages to external systems like file systems and databases. Furthermore, you can also implement custom aggregations using Spark’s [user-defined aggregation function (UDAFs)](https://docs.databricks.com/spark/latest/spark-sql/udaf-scala.html).

## Aggregations on Windows over Event-Time

In many cases, rather than running aggregations over the whole stream, you want aggregations over data bucketed by time windows (say, every 5 minutes or every hour). In our earlier example, it’s insightful to see what is the average signal strength in last 5 minutes in case if the devices have started to behave anomalously. Also, this 5 minute window should be based on the timestamp embedded in the data (aka. event-time) and not on the time it is being processed (aka. processing-time).

Earlier Spark Streaming DStream APIs made it hard to express such event-time windows as the API was designed solely for processing-time windows (that is, windows on the time the data arrived in Spark). In Structured Streaming, expressing such windows on event-time is simply performing a special grouping using the `window()` function. For example, counts over 5 minute tumbling (non-overlapping) windows on the eventTime column in the event is as following.

In the above query, every record is going to be assigned to a 5 minute tumbling window as illustrated below.

**Summary:** The diagram maps events arriving at different processing times to event-time positions and five-minute tumbling windows.

**Components:**

- Processing Time: Spark record arrival timeline
- Events: event records with timestamps, device IDs, and values
- Event Time: timeline contained in each event
- Tumbling Windows: five-minute non-overlapping event-time windows

**Flows:**

- Processing Time -> Event 1202: record processed
- Processing Time -> Event 1207: record processed
- Processing Time -> Event 1213: record processed
- Event 1202 -> Event Time 1202: event time
- Event 1207 -> Event Time 1207: event time
- Event 1213 -> Event Time 1213: event time
- Event Time 1202 -> Window 1200 to 1205: window assignment
- Event Time 1207 -> Window 1205 to 1210: window assignment
- Event Time 1213 -> Window 1210 to 1215: window assignment

**Numbers:** 12:00, 12:02, 12:05, 12:07, 12:10, 12:13, 12:15, 123, 678, 789, dev1, dev3, 5 min

```mermaid
%% Event processing time maps records to event-time tumbling windows
flowchart LR
    P[Processing Time]
    E1[Event 12:02 dev1 123]
    E2[Event 12:07 dev1 789]
    E3[Event 12:13 dev3 678]
    T[Event Time]
    W1[Window 12:00 to 12:05]
    W2[Window 12:05 to 12:10]
    W3[Window 12:10 to 12:15]
    L[Legend]

    P -. record processed .-> E1
    P -. record processed .-> E2
    P -. record processed .-> E3
    E1 -->|event time 12:02| T
    E2 -->|event time 12:07| T
    E3 -->|event time 12:13| T
    T -->|window assignment| W1
    T -->|window assignment| W2
    T -->|window assignment| W3

    L[Grey dashed arrival, orange event time, blue window assignment]

    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class P,T service
    class E1,E2,E3 queue
    class W1,W2,W3 store
    class L external
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2017/05/mapping-of-event-time-to-5-min-tumbling-windows.png</sub>

Each window is a group for which running counts are calculated. You can also define overlapping windows by specifying both the window length and the sliding interval. For example:

In the above query, every record will be assigned to multiple overlapping windows as illustrated below.

**Summary:** The diagram shows how Spark Structured Streaming maps out-of-order events to overlapping 10-minute windows sliding every 5 minutes.

**Components:**

- Processing Time: Spark Structured Streaming trigger timeline
- Events: timestamped device records
- Event Time: timestamps carried by records
- Overlapping Windows: event-time aggregation windows
- Window mapping: assignment of each event to matching windows

**Flows:**

- Processing Time -> Events: records are processed at 12:02, 12:07, and 12:13
- Events -> Event Time: record timestamps map to event-time positions
- Event Time -> Overlapping Windows: each event maps to multiple overlapping windows
- Event Time -> Window mapping: event timestamps determine window membership

**Numbers:** 12:00, 12:02, 12:05, 12:07, 12:10, 12:13, 12:15, 12:20, 10 mins, 5 mins, 123, 789, 678, dev1, dev3

```mermaid
%% Event-time records mapped to overlapping Spark Structured Streaming windows
flowchart LR
    P[Processing Time]
    E[Events]
    T[Event Time]
    W[Overlapping Windows]
    M[Window Mapping]

    P -->|processing positions| E
    E -->|record timestamps| T
    T -->|12:02 maps to 12:00 to 12:10| W
    T -->|12:07 maps to 12:00 to 12:10 and 12:05 to 12:15| W
    T -->|12:13 maps to 12:05 to 12:15 and 12:10 to 12:20| W
    T -->|event time determines membership| M
    M -->|window assignments| W

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class P client
    class E queue
    class T service
    class W store
    class M decision
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2017/05/mapping-of-event-time-to-overlapping-windows-of-length-10-mins-and-sliding-interval-5-mins.png</sub>

This grouping strategy automatically handles late and out-of-order data — the late event would just update older window groups instead of the latest ones. Here is an end-to-end illustration of a query that is grouped by both the `deviceId` and the overlapping windows. The illustration below shows how the final result of a query changes after new data is processed with 5 minute triggers when you are grouping by both `deviceId` and sliding windows (for brevity, the “signal” field is omitted).

**Summary:** The diagram shows late data updating counts for overlapping event-time windows in Spark Structured Streaming.

**Components:**

- Input Stream with timestamped device records
- Processing Time timeline with five minute triggers
- Result Tables containing windowed counts
- Late data record generated at 12:04 and arriving at 12:11
- Updated count for the 12:00 - 12:10 window

**Flows:**

- Input Stream -> Processing Time: timestamped device events arrive
- Processing Time -> Result Tables: five minute triggers produce incremental counts
- Late data record -> Result Tables: updates the old 12:00 - 12:10 dev2 window count

**Numbers:** 12:00, 12:02, 12:03, 12:04, 12:05, 12:06, 12:07, 12:10, 12:11, 12:13, 12:15, 12:20, 5 minutes, 1, 2

```mermaid
%% Event time aggregation with late data updating an older window
flowchart LR
    input[Input Stream<br/>12:02 dev1<br/>12:03 dev2<br/>12:06 dev3<br/>12:07 dev1<br/>12:04 dev2<br/>12:13 dev3]
    time[Processing Time<br/>12:00 12:05 12:10 12:15]
    first[Result Table<br/>12:00 - 12:10<br/>dev1 1<br/>dev2 1]
    second[Updated Result Table<br/>dev1 2<br/>dev2 1<br/>dev3 1<br/>12:05 - 12:15 dev1 1<br/>12:05 - 12:15 dev3 1]
    late[Late Data<br/>12:04 dev2 arrives at 12:11]
    final[Final Result Table<br/>12:00 - 12:10 dev2 2<br/>12:05 - 12:15 dev3 2<br/>12:10 - 12:20 dev3 1]

    input -->|events arrive| time
    time -->|five minute trigger| first
    time -->|five minute trigger| second
    late -->|updates old window count| final
    second -->|next trigger| final

    classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
    class input queue
    class time service
    class first,second,final store
    class late critical
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2017/05/late-data-handling-in-windowed-grouped-aggregation.png</sub>

Note how the late, out-of-order record [12:04, dev2] updated an old window’s count.

## Stateful Incremental Execution

While executing any streaming aggregation query, the Spark SQL engine internally maintains the intermediate aggregations as fault-tolerant state. This state is structured as key-value pairs, where the key is the group, and the value is the intermediate aggregation. These pairs are stored in an in-memory, versioned, key-value “state store” in the Spark executors that is checkpointed using write ahead logs in an HDFS-compatible file system (in the configured [checkpoint location](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)). At every trigger, the state is read and updated in the state store, and all updates are saved to the write ahead log. In case of any failure, the correct version of the state is restored from checkpoint information, and the query proceeds from the point it failed. Together with replayable sources, and idempotent sinks, Structured Streaming ensures exactly-once guarantees for stateful stream processing.

**Summary:** Structured Streaming incrementally processes source data, updates durable state, writes results to a sink, and persists state updates in a write ahead log for fault tolerance.

**Components:**

- Incremental execution every trigger
- SRC source
- Process new data
- State state store
- Sink output sink
- Write ahead log
- Fault tolerant, exactly-once stateful stream processing in Structured Streaming

**Flows:**

- Incremental execution -> SRC: trigger
- SRC -> Process new data: new source data
- Process new data -> State: state update
- Process new data -> Sink: output data
- State -> Process new data: prior state
- State -> Write ahead log: asynchronous state persistence

**Numbers:** 12:00, 12:05, 12:10

```mermaid
%% Shows incremental stateful stream processing with write ahead logging
flowchart LR
    T[Incremental execution every trigger]:::client
    S[SRC source]:::external
    P[Process new data]:::service
    ST[State state store]:::store
    K[Sink output sink]:::external
    W[Write ahead log]:::queue
    F[Fault tolerant exactly once stateful stream processing in Structured Streaming]:::critical

    T -->|trigger at 12:00 12:05 12:10| S
    S -->|new source data| P
    P -->|state update| ST
    P -->|output data| K
    ST -->|prior state| P
    ST -.->|asynchronous persistence| W
    W -.->|state recovery| ST
    F -.->|describes| P

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2017/05/fault-tolerant-exactly-once-stateful-stream-processing-in-structured-streaming.png</sub>

This fault-tolerant state management naturally incurs some processing overheads. To keep these overheads bounded within acceptable limits, the size of the state data should not grow indefinitely. However, with sliding windows, the number of windows/groups will grow indefinitely, and so can the size of state (proportional to the number of groups). To bound the state size, we have to be able to drop old aggregates that are not going to be updated any more, for example seven day old averages. We achieve this using *watermarking*.

## Watermarking to Limit State while Handling Late Data

As mentioned before, the arrival of late data can result in updates to older windows. This complicates the process of defining which old aggregates are not going to be updated and therefore can be dropped from the state store to limit the state size. In Apache Spark 2.1, we have introduced ***watermarking*** that enables automatic dropping of old state data.

Watermark is a moving threshold in event-time that trails behind the maximum event-time seen by the query in the processed data. The trailing gap defines how long we will wait for late data to arrive. By knowing the point at which no more data will arrive for a given group, we can limit the total amount of state that we need to maintain for a query. For example, suppose the configured maximum lateness is 10 minutes. That means the events that are up to 10 minutes late will be allowed to aggregate. And if the maximum observed event time is 12:33, then all the future events with event-time older than 12:23 will be considered as “too late” and dropped. Additionally, all the state for windows older than 12:23 will be cleared. You can set this parameter based on the requirements of your application — larger values of this parameter allows data to arrive later but at the cost of increased state size, that is, memory usage and vice versa.

Here is the earlier example but with watermarking.

When this query is executed, Spark SQL will automatically keep track of the maximum observed value of the eventTime column, update the watermark and clear old state. This is illustrated below.

**Summary:** The diagram shows Spark Structured Streaming watermarking for windowed grouped aggregation, including event-time data, late-data handling, watermark progression, and result-table updates.

**Components:**

- Event-time data points with eventTime and deviceId
- Processing-time trigger timeline using 5 minute triggers
- Maximum event-time-seen watermark tracker
- Watermark calculated as maximum event time minus late threshold
- Windowed grouped aggregation result tables
- Intermediate state for the 12:00 to 12:10 window
- Late-data classification into within-watermark and outside-watermark events

**Flows:**

- Event-time data -> Maximum event-time-seen tracker: updates maximum observed event time
- Maximum event-time-seen tracker -> Watermark: computes watermark
- Event-time data -> Windowed grouped aggregation: updates window counts
- Late data within watermark -> Windowed grouped aggregation: updates counts
- Data outside watermark -> Windowed grouped aggregation: ignored
- Watermark -> Intermediate state: drops state older than the watermark
- Processing-time triggers -> Result tables: emits updated aggregation results

**Numbers:**

- 12:00
- 12:04, dev1
- 12:05
- 12:07, dev1
- 12:08, dev2
- 12:09, dev3
- 12:10
- 12:13, dev3
- 12:14, dev2
- 12:15
- 12:17, dev3
- 12:20
- 12:21, dev2
- 12:25
- 5 min triggers
- 10 min late threshold
- Watermark 12:14 minus 10 min equals 12:04
- Watermark 12:21 minus 10 min equals 12:11
- Windows 12:00 to 12:10, 12:05 to 12:15, and 12:10 to 12:20
- Counts 1, 2, and 3

```mermaid
%% Spark Structured Streaming watermarking and windowed aggregation
flowchart LR
    D[Event time data] -->|updates max event time| M[Maximum event time seen]
    M -->|subtracts 10 minute threshold| W[Watermark]
    D -->|groups into time windows| A[Windowed grouped aggregation]
    L[Late data within watermark] -->|updates counts| A
    T[Data outside watermark] -->|ignored in counts| A
    W -->|drops old intermediate state| S[Intermediate window state]
    P[Five minute processing triggers] -->|emits results| R[Result tables]
    A -->|updates| R

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
    classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

    class D,L,T client
    class M,W,A service
    class S,R store
    class P queue
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2017/05/watermarking-in-windowed-grouped-aggregation.png</sub>

Note the two events that arrive between the processing-times 12:20 and 12:25. The watermark is used to differentiate between the late and the “too-late” events and treat them accordingly.

## Conclusion

In short, I covered Structured Streaming’s windowing strategy to handle key streaming aggregations: windows over event-time and late and out-of-order data. Using this windowing strategy allows Structured Streaming engine to implement watermarking, in which late data can be discarded. As a result of this design, we can manage the size of the state-store.

In the upcoming version of Apache Spark 2.2, we have added more advanced stateful stream processing operations to streaming DataFrames/Datasets. Stay tuned to this blog series for more information. If you want to learn more about Structured Streaming, read our previous posts in the series.

- [Structured Streaming In Apache Spark](https://www.databricks.com/blog/2016/07/28/structured-streaming-in-apache-spark.html)
- [Real-time Streaming ETL with Structured Streaming in Apache Spark 2.1](https://www.databricks.com/blog/2017/01/19/real-time-streaming-etl-structured-streaming-apache-spark-2-1.html)
- [Working with Complex Data Formats with Structured Streaming in Apache Spark 2.1](https://www.databricks.com/blog/2017/01/19/real-time-streaming-etl-structured-streaming-apache-spark-2-1.html)
- [Processing Data in Apache Kafka with Structured Streaming in Apache Spark 2.2](https://www.databricks.com/blog/2017/04/26/processing-data-in-apache-kafka-with-structured-streaming-in-apache-spark-2-2.html)

To try Structured Streaming in Apache Spark 2.0, [try Databricks today](https://www.databricks.com/try-databricks).
