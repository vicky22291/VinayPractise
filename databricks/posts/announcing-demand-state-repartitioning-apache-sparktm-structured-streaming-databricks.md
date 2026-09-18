# Announcing On-Demand State Repartitioning for Apache Spark™ Structured Streaming on Databricks

*Right-size your most demanding stateful streams, from fraud detection to real-time surveillance, without ever rebuilding your checkpoint state*

- Source: https://www.databricks.com/blog/announcing-demand-state-repartitioning-apache-sparktm-structured-streaming-databricks
- Published: 2026-09-14
- Authors: Thangam Vaiyapuri, Jay Palaniappan, B. Micheal Okutubo, Zifei Feng
- Categories: engineering, data-engineering
- Images: 0 total, 0 extracted as architecture

**Key takeaways**

- What changed: You can now resize a stateful streaming query's partitions without rebuilding the checkpoint or losing state.
- How it works: Set spark.sql.streaming.stateStore.partitions and restart your query on DBR 18+ with RocksDB state store provider. The query redistributes state to the new partition count.
- Why it matters: Tune and scale long-running streams to fit the workload, and track each resize via query progress metrics.

Anyone running stateful [Apache Spark™ Structured Streaming](https://spark.apache.org/docs/latest/streaming/index.html) queries in production eventually hits the same uncomfortable wall.

You started the query months ago. Back then, the data volume was modest, so you accepted the default of 200 shuffle partitions and moved on. The pipeline ran smoothly. Then the business grew, traffic tripled, and the state store ballooned. Suddenly, those 200 partitions are no longer the right size. Some partitions are skewed and run hot, the cluster is straining, and every microbatch takes longer than it should.

So you do the natural thing: you bump up `spark.sql.shuffle.partitions` and restart the query. Nothing changes.

The query quietly ignores your new value because the partition count was baked into the checkpoint when you first started the stream. Historically, the only way to apply a new number has been to abandon the existing checkpoint and start over, which, for a stateful query, means losing all the accumulated state you've been carefully maintaining. For a fraud model tracking millions of accounts, or a sessionization job holding days of windows, "start over" is not a phrase anyone wants to say in a production incident review.

[On-demand state repartitioning](https://docs.databricks.com/aws/en/structured-streaming/state-repartitioning) (Public Preview), available in Databricks Runtime 18 and above, removes that wall. You can now resize the number of partitions for a stateful streaming query and keep your checkpoint state intact.  

This applies to any stateful streaming query, whether you run aggregations, stream-stream joins, deduplication, sessionization, or transformWithState, and to any workload, from fraud detection to real-time monitoring.

For early adopters like Coveo, the ability to right-size their streaming infrastructure on demand immediately translated into significant operational savings. 

> At Coveo, we run large-scale stateful streaming pipelines where data volumes fluctuate significantly over time. With Databricks and the State Repartitioning capability, we’ve cut our related Amazon S3 API costs by 40%.  Before, every scaling decision forced a trade-off: either overprovision or rebuild from new checkpoints, which drove storage API costs nearly the same as compute costs. Now we scale freely as demand shifts, without disrupting the existing state or triggering costly checkpoint migrations.”  —Alexis Chicoine, Senior Software Developer, Coveo

## Under the hood: Why were state partitions locked?

To understand why Coveo’s results represent a meaningful leap forward for Structured Streaming, we have to look at why the partition count was ever frozen in the first place.

A stateful streaming query keeps its state in a state store, and that state is physically partitioned. Each key in your stream,  a user ID, an account number, a window, is hashed to a specific partition, and the data for each partition is stored in its own separate RocksDB instance within the checkpoint. The number of partitions defines the layout of the entire state store on disk.

If you simply changed the partition count between restarts, the hashing would no longer line up. A key that previously lived in one partition (say, partition 47) might now hash to a different one (partition 12), but its accumulated state is still sitting in the original partition's files. The query would, in effect, lose track of its own memory. To prevent exactly this kind of silent corruption, Structured Streaming locked the partition count at checkpoint creation and ignored any later changes to `spark.sql.shuffle.partitions`.

Safe, but inflexible. The two costs you paid were:

1. **You couldn't tune.** If 200 partitions turned out to be the wrong choice, you were stuck with it for the life of the checkpoint.
2. **You couldn't scale with the workload.** As data volume grew or shrank, your partition count couldn't keep pace.

On-demand state repartitioning addresses both by doing the one thing the old design refused to do,  but doing it safely, by physically redistributing the state to match the new partition count.

## What you need to get started

The requirements are short:

- **Databricks Runtime 18 or above.**
- **The RocksDB state store provider.** In DBR 17.3 and above, RocksDB is the default, and new queries created in those versions will use it unless explicitly changed.  If you want to confirm or explicitly set it, see [Configure RocksDB state store on Databricks](https://docs.databricks.com/aws/en/structured-streaming/rocksdb-state-store).

That's the entire prerequisite list. If you're on DBR 18 with the default state store, you already have everything you need.

## Changing the number of partitions

The mechanism is simple, and it reuses a pattern every streaming developer already knows: stop, reconfigure, restart.

Instead of `spark.sql.shuffle.partitions`, you set a dedicated configuration, ` spark.sql.streaming.stateStore.partitions`, and restart the query:

The key detail is the new config itself. For stateful queries, `spark.sql.streaming.stateStore.partitions` **takes precedence** over `spark.sql.shuffle.partitions`. This is what makes the change "stick" where the old approach didn't.

When the query restarts, it doesn't resume normal processing immediately. First, it finishes the last planned microbatch, if there's one still pending. Then it performs a one-time repartition operation: it physically redistributes the state data across the new number of partitions, re-hashing keys into their correct new homes so that nothing is lost or misplaced. Once that redistribution completes, the query resumes processing as usual, now using the partition count you requested.

That repartition step is the heart of the feature. It's the difference between "we changed a number" and "we safely moved your state to a new layout."

## Monitoring the repartition operation

Because repartitioning is an actual operation whose runtime is proportional to the amount of state, you'll want visibility into it. Structured Streaming surfaces this through its standard progress reporting.

After the next microbatch completes, the `StreamingQueryProgress` events include the duration of the repartition operation. Look in the event's durationMs metrics for the `controlBatch.REPARTITION` field, which reports the repartition duration in milliseconds.

A larger state footprint means a longer repartition, but we expect it to take only a few seconds for most workloads. So, on big jobs, it's worth capturing this metric to understand the duration. For more on reading these events, see [Monitoring Structured Streaming queries on Databricks](https://docs.databricks.com/aws/en/structured-streaming/stream-monitoring).

## Example: scaling a query down

Let's make this concrete with a simple aggregation,  a tumbling-window count of events by id. We'll start it with the default of 200 partitions, decide that's more than this workload needs, and scale it down to 100.

First, the query as it runs today, with the default partition count:

Now, we've watched this stream for a while and concluded that 200 partitions is overkill. We're paying coordination overhead for parallelism we don't need. We stop the query, set the new partition count, and restart it with the same options and the same checkpoint:

When the restarted query comes up, it wraps up the last planned microbatch, if there's one still pending, runs the repartition to redistribute state from 200 partitions down to 100, and then carries on counting with every window and every running total fully preserved. The same procedure works in reverse: to scale up under a heavier load, you'd simply set a larger number.

The same approach applies to Spark Declarative Pipelines (SDP). See the [SDP example](https://docs.databricks.com/aws/en/structured-streaming/state-repartitioning#lakeflow-pipelines-example) in the docs for a full walkthrough.

## When to use state repartitioning

On-demand state repartitioning is a tuning and scaling tool rather than a routine operation. It proves valuable in a few key situations: 

- **Right-sizing after launch. **You started the pipeline with the default 200 partitions on day one because the stream was small and fine-tuning wasn't worth it. Six months later, that number is baked into a checkpoint you can't afford to lose, and it's not enough. Ex: a fraud-scoring stream that launched in a single pilot region now covers every market, and 200 partitions leave each one holding far too much state. With on-demand repartitioning, you can increase the partition count to match what you now carry without losing your existing checkpoint.
- **Changing workloads. **You sized the stream for the peak traffic. Ex: An ad-bidding pipeline runs hot through the day and goes quiet overnight, so a value tuned for the daytime peak leaves most partitions idle at 3 am. With on-demand repartitioning, you scale up going into the busy stretch and back down once it passes, so partitioning follows actual load rather than the worst case.
- **Backfilling historical data:  **Backfill and steady-state processing need different partition counts, and previously, you had to choose one for the checkpoint's life. Ex: reprocessing two years of history needs a high count to spread the work and finish fast, but that same count is wasteful once you're back to steady-state traffic. On-demand repartitioning lets you scale up for backfilling and down to steady-state size after catching up, all without losing the checkpoint and state.
- **Performance tuning.** Partition count affects parallelism, state size, and shuffle overhead, and the optimal value is hard to predict. Ex: you might think 200 is too small and that 400 would reduce microbatch latency, but testing used to require rebuilding state and reprocessing data, wasting resources. On-demand repartitioning lets you adjust the count against your live checkpoint and monitor controlBatch.REPARTITION and microbatch durations, and decide based on measurements rather than guessing.

Because each change requires a stop and restart with a one-time repartition pause, treat it as a deliberate maintenance action. Plan the resize for a window where a brief processing pause is acceptable, and watch `controlBatch.REPARTITION` to confirm how long it took, and let the query settle back into its normal rhythm.

## Conclusion

For years, the partition count of a stateful streaming query was a decision you made once, at the very beginning, and then never revisited, or paid dearly to rebuild the state from scratch. On-demand state repartitioning removes these constraints. Safely redistributing state across a new partition count turns a start-time-only decision into one you can revisit whenever your workload calls for it.

The result is exactly what operators of long-running streams have wanted: the freedom to right-size a query based on its scaling needs, with nothing more than a stop, a config change, and a restart, without losing its state.

On-demand state repartitioning is available in Databricks Runtime 18 and above, using the RocksDB state store provider. For the full reference, see [On-demand state repartitioning for stateful streaming queries](https://docs.databricks.com/aws/en/structured-streaming/state-repartitioning).
