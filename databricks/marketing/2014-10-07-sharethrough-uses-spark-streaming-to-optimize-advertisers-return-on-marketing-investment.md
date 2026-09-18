# Sharethrough Uses Apache Spark Streaming to Optimize Advertisers' Return on Marketing Investment

- Source: https://www.databricks.com/blog/2014/10/07/sharethrough-uses-spark-streaming-to-optimize-advertisers-return-on-marketing-investment.html
- Published: 2014-10-07
- Authors: Russell Cardullo
- Categories: company, customers, data-streaming
- Images: 0 total, 0 extracted as architecture

This is a guest blog post from our friends at [Sharethrough](http://www.sharethrough.com) providing an update on how their use of Apache Spark has continued to expand.

---

## Business Challenge

Sharethrough is an advertising technology company that provides native, in-feed advertising software to publishers and advertisers. Native, in-feed ads are designed to match the form and function of the sites they live on, which is particularly important on mobile devices where interruptive advertising is less effective. For publishers, in-feed monetization has become a major revenue stream for their mobile sites and applications. For advertisers, in-feed ads have been proven to drive more brand lift than interruptive banner advertisements.

Sharethrough’s publisher and advertiser technology suite is capable of optimizing the format of an advertisement for seamless placement on content publishers websites and apps. This involves four major steps: Targeting the right users, optimizing the creative content for the target, scoring the content quality, and allowing the advertiser to bid on the actual ad placement in a real-time auction.

All four steps are necessary to optimize an advertiser’s return on marketing investment. But this requires real-time capabilities in the following three areas:

- **Creative optimization:** Choosing the best performing content variant from a seemingly infinite number of variations in thumbnails, headlines, descriptions etc.
- **Spend tracking:** Advertisers expect automatic adjustment (“programmatic” in advertising parlance) to real-time bidding algorithms to achieve their campaign goals given their parameters and budget. A required feature of Sharethrough’s platform is to provide real-time adjustments into how content engagement consumes an advertising budget.
- **Operational monitoring:** When expected behaviour falls outside of positive or negative norms (e.g. traffic spikes during the Oscars or lowered spend), these need to be understood and addressed in a timely manner to answer the question - “Is this event expected and/or acceptable?”

Better creative content and optimal placement translate into better consumer engagement and higher conversion, but Sharethrough needs to measure the business impact of these optimizations in real time.

## Technology Challenge

The technology that Sharethrough was using prior to Spark was not able to accommodate the short feedback cycles required to meet these three objectives.

After migrating from Amazon Elastic [MapReduce](https://www.databricks.com/glossary/mapreduce) in 2010, we deployed the Cloudera Distribution of Hadoop on Amazon Web Services, primarily for batch use cases such as Extract, Transform and Load (ETL). These batch runs are used for intermittent performance reporting and billing throughout the day, with delays on the order of hours, not minutes. After the launch of our new platform in 2013, it became apparent that Hadoop was not well suited to serve Sharethrough’s increasingly real-time needs.

Sharethrough’s data processing pipeline relies on Apache Flume to write web server log data into [HDFS](https://www.databricks.com/glossary/hadoop-distributed-file-system-hdfs) in 64MB increments based on the default HDFS block size. Sharethrough runs a set of MapReduce jobs at periodic intervals with the resulting output written to a data warehouse using Sqoop.

This setup generated insights with a delay of more than one hour. Sharethrough was unable to update the models sooner than these existing batch workflows allowed. This meant that advertisers could not be sure that they had optimized the return on their content investment because any decisions were taken on data that was a few hours old.

## Solution

In the middle of 2013, we turned to Apache Spark and in particular Spark Streaming because we needed a system to process click stream data in real time.

In my Spark Summit 2014 [talk](https://www.youtube.com/watch?v=0QXzKqMPgWQ&index=2&list=PL-x35fyliRwimkfjeg9CEFUSDIE1F7qLS), I highlighted the reasons for choosing Spark:

“We found Spark Streaming to be a perfect fit for us because of its easy integration into the Hadoop ecosystem, powerful functional programming API, low-friction interoperability with our existing batch workflows and broad ecosystem endorsement.”

Spark is compatible with our existing investments in Hadoop. This means that existing HDFS files can be used as an input for Spark computations, and Spark can use HDFS for persistent storage.

At the same time, Spark makes it easy for developers lacking an understanding of the various elements of Hadoop to become productive. While Spark integrates with Hadoop, it does not require knowledge of HDFS, MapReduce or the various Hadoop processing engines. At Sharethrough, much of the backend code is written using Scala, and therefore blends into Spark very naturally since Spark supports the Scala APIs.

This allows our developers to work at the level of the actual business logic and data pipeline that specify what has to happen. Spark then figures out how this has to happen, coordinating lower-level tasks such as data movement and recovery. The resulting code is quite concise due to the Spark API.

We’re using Spark for streaming now but the opportunity to also use Spark for batch processing is really appealing to us. Spark provides a unified development environment and runtime across both batch and real-time workloads, allowing reusability between batch and streaming jobs. It also makes it much easier to combine arriving real-time data with historical data in one analysis.

Finally, the community support available with Spark is quite helpful, from mailing lists and an ecosystem of code contributors all the way to companies like Cloudera, MapR and Datastax that offer professional support.

## Deployment in Detail

Sharethrough runs Spark on 10 AWS m1.xlarge nodes, ingests 200 GB per day and is using Mesos for cluster management.

Following the principles of the Lambda architecture, Sharethrough uses Hadoop for the batch layer of its architecture, what we call the “cold path”, and Spark for the “hot path” real-time layer.

In the hot path, Flume writes out all the clickstream data to RabbitMQ. Next, Spark reads from RabbitMQ at a (configurable) batch size of five seconds. The resulting output updates the predictive models that run our business. The end-to-end process completes within a few seconds, including the Spark processing time and the time taken by Flume to transmit the data to RabbitMQ.

Because of API consistency, our engineers design and test locally in a simple batch mode and then run the same job in production using streaming mode. This enables the system to achieve the desired optimization required for real-time bidding.

Going forward, we aim to simplify the upstream components of our data pipeline using Amazon Kinesis. Kinesis would supplant existing queueing systems like RabbitMQ by connecting to all sources such as web servers, machine logs or mobile devices. Kinesis would then form the central hub from which all applications including Spark can pull data. Spark support for Kinesis was added as part of the recent Spark 1.1 release in September 2014.

## Value Realized

Spark delivers on our business objectives of improving creative optimization, spend tracking and operational monitoring. Spark makes it easier to deliver ads on budget, which is particularly critical for campaigns that may only run for a few days. Spend can be tracked and operational issues adjusted in real-time. For instance, if Sharethrough releases code that does not render well on some third-party sites, this can now be detected and fixed immediately.

But Spark also creates value for our technical team. Engineers can conduct and learn from real-time experiments much more quickly than before. Code re-use and testing is another significant benefit. Because of the higher abstraction level and unified programming model of Spark, Sharethrough can much more easily reuse the code from one job to create another job in a modular fashion just by replacing a few lines of code. This results in much cleaner looking code, which is easier to debug, test, reuse and maintain. Furthermore we can use a single analytics cluster to provide both real-time stream processing as well as batch analytic workflows without the operational and resource overhead of supporting two different clusters with different latency requirements.

## To Learn More:

1. [https://www.youtube.com/watch?v=0QXzKqMPgWQ&index=2&list=PL-x35fyliRwimkfjeg9CEFUSDIE1F7qLS](https://www.youtube.com/watch?v=0QXzKqMPgWQ&index=2&list=PL-x35fyliRwimkfjeg9CEFUSDIE1F7qLS)
2. [https://www.databricks.com/dataaisummit](https://www.databricks.com/dataaisummit)
