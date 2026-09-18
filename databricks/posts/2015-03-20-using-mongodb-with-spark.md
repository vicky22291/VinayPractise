# Using MongoDB with Apache Spark

- Source: https://www.databricks.com/blog/2015/03/20/using-mongodb-with-spark.html
- Published: 2015-03-20
- Authors: Matt Kalan
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

***Update August 4th 2016:**
 Since this original post, MongoDB has released a new Databricks-certified connector for Apache Spark. See the [updated blog post](https://www.databricks.com/blog/2016/07/21/the-new-mongodb-connector-for-apache-spark-in-action-building-a-movie-recommendation-engine.html) for a tutorial and notebook on using the new MongoDB Connector for Apache Spark.*

---

*This is a guest blog from Matt Kalan, a Senior Solution Architect at [MongoDB](https://www.mongodb.com/)*

---

## Introduction

The broad spectrum of data management technologies available today makes it difficult for users to discern hype from reality. While I know the immense value of [MongoDB](https://www.mongodb.com/) as a real-time, distributed operational database for applications, I started to experiment with Apache Spark because I wanted to understand the options available for analytics and batch operations.

I started with a simple example of taking 1-minute time series intervals of stock prices with the opening (first) price, high (max), low (min), and closing (last) price of each time interval and turning them into 5-minute intervals (called OHLC bars).   The 1-minute data is stored in MongoDB and is then processed in Spark via the MongoDB Hadoop Connector, which allows MongoDB to be an input or output to/from Spark.

One might imagine that a more typical example is that you record this market data in MongoDB for real-time purposes but then potentially run the analytical models in another environment offline. Of course the models would be way more complicated – this is just as a Hello World level example. I chose OHLC bars just because that was the data I found easily.

## Summary

**Use case**: aggregating 1-minute intervals of stock prices into 5-minute intervals

**Input**: 1-minute stock prices intervals in a MongoDB database

**Simple Analysis:** performed with Spark

**Output: **5-minute stock price intervals in Spark and optionally write back into MongoDB

**Steps to set up the environment:**

- **Set up Spark environment** – I installed Spark v1.2.0 in a VM on my Mac laptop
- **Download sample data** – I acquired these data points in [1 minute](http://www.google.com/url?q=http%3A%2F%2Fwww.barchartmarketdata.com%2Fdata-samples%2Fmstf.csv&sa=D&sntz=1&usg=AFQjCNErKsHfV7l6PKvm6igSQIpuVbfabQ) increments
- **Install MongoDB on the VM** – I easily installed MongoDB with yum on CentOS with instructions from [this page](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-red-hat/)
- **Start MongoDB **– a default configuration file is installed by yum so you can just run this to start on localhost and the default port *27017* :

- **Load sample data** – [mongoimport](https://docs.mongodb.com/database-tools/mongoimport/) allows you to load CSV files directly as a flat document in MongoDB. The command is simply this:

- **Install MongoDB Hadoop Connector** – You can download the Hadoop Connector jar at: [Using the MongoDB Hadoop Connector with Spark](https://github.com/mongodb/mongo-hadoop/wiki/Spark-Usage). If you use the Java interface for Spark, you would also download the MongoDB Java Driver jar. Any jars that you download can be added to Spark using the --jars option to the PySpark command. I used Python with Spark below (called PySpark).

For the following examples, here is what a document looks like in the MongoDB collection (via the Mongo shell). You start the Mongo shell simply with the command “mongo” from the /bin directory of the MongoDB installation.

## Spark Example

For my initial foray into Spark, I opted to use Python with the interactive shell command “PySpark”. This gave me an interactive Python environment for leveraging Spark classes. Python appears to be popular among quants because it is a more natural language to use for interactive querying compared to Java or Scala. I was able to successfully read from MongoDB in Spark, but make sure you upgrade to Spark v1.2.2 or v1.3.0 to address a bug in earlier versions of PySpark.

The benefits of Spark were immediately evident, and in line with what you would expect in an interactive environment – queries return quickly, much faster than Hive, due in part to the fact they are not compiled to MapReduce. While the latency is still higher than MongoDB’s internal querying and aggregation framework, there are more options for distributed, multi-threaded analysis with Spark, so it clearly has a role to play for data analytics.

### set up parameters for reading from MongoDB via Hadoop input format

config = {"mongo.input.uri": "mongodb://localhost:27017/marketdata.minbars"}
 inputFormatClassName = "com.mongodb.hadoop.MongoInputFormat"

### these values worked but others might as well

keyClassName = "org.apache.hadoop.io.Text"
 valueClassName = "org.apache.hadoop.io.MapWritable"

### read the 1-minute bars from MongoDB into Spark RDD format

minBarRawRDD = sc.newAPIHadoopRDD(inputFormatClassName, keyClassName, valueClassName, None, None, config)

### configuration for output to MongoDB

config["mongo.output.uri"] = "mongodb://localhost:27017/marketdata.fiveminutebars"
 outputFormatClassName = "com.mongodb.hadoop.MongoOutputFormat"

### takes the verbose raw structure (with extra metadata) and strips down to just the pricing data

minBarRDD = minBarRawRDD.values()

import calendar, time, math

dateFormatString = '%Y-%m-%d %H:%M'

### sort by time and then group into each bar in 5 minutes

groupedBars = minBarRDD.sortBy(lambda doc: str(doc["Timestamp"])).groupBy(lambda doc (doc["Symbol"], math.floor(calendar.timegm(time.strptime(doc["Timestamp"], dateFormatString)) / (5*60))))

### define function for looking at each group and pulling out OHLC

### assume each grouping is a tuple of (symbol, seconds since epoch) and a resultIterable of 1-minute OHLC records in the group

### write function to take a (tuple, group); iterate through group; and manually pull OHLC

def ohlc(grouping):
 low = sys.maxint
 high = -sys.maxint
 i = 0
 groupKey = grouping[0]
 group = grouping[1]
 for doc in group:
 #take time and open from first bar
 if i == 0:
 openTime = doc["Timestamp"]
 openPrice = doc["Open"]

resultRDD = groupedBars.map(ohlc)

resultRDD.saveAsNewAPIHadoopFile("file:///placeholder", outputFormatClassName, None, None, None, None, config)

I saw the appeal of Spark from my first introduction. It was pretty easy to use. It is also especially nice in that it has operations that run on all elements in a list or a matrix of data. I can also see the appeal of having statistical capabilities like R, but in which the data can be distributed across many nodes easily (there is a Spark project for R as well).

Spark is certainly new, and I had to use Spark v1.2.2 or later due to a bug ([SPARK-5361](https://issues.apache.org/jira/browse/SPARK-5361)) that initially prevented me from writing from PySpark to a Hadoop file (writing to Hadoop & MongoDB in Java & Scala should work). Another drawback I encountered was the difficulty to visualize data during an interactive session in PySpark. It reminded me of my college days being frustrated debugging matrices representing ray traces in Matlab, before they added better tooling. Likewise there are still challenges in displaying the data in the RDD structures; while there is a function collect() for creating lists that are more easily printable, some elements such as iterables remain difficult to display.

## Key Takeaways of Using MongoDB with Spark

### Spark is easy to integrate with MongoDB

Overall it was useful to see how data in MongoDB can be accessed via Spark. In retrospect, I spent more time manipulating the data than I did integrating them with MongoDB, which is what I had hoped. I also started with a pre-configured VM on a single node instead of setting up the environment. I have since learned of the Databricks Cloud, which I expect would make a larger installation easy.

### Many real-world applications exist

A real-life scenario for this kind of data manipulation is storing and querying real-time, intraday market data in MongoDB. Prices update throughout the current day, allowing users to querying them in real-time. Using Spark, after the end of day (even if the next day begins immediately like with FX), individual ticks can be aggregated into structures that are more efficient to access, such as these OHLC bars, or large documents with arrays of individual ticks for the day, by ticker symbol. This approach gives great write throughput during the day for capture, as well as blazing fast access to weeks, month, or years of prices. There are users of MongoDB whose systems follow this approach, and who have dramatically reduced latency for analytics, as well as reduced their hardware footprint. By storing the aggregated data back in MongoDB, you can index the data flexibly and retrieve it quickly.

For more information, you can visit:

- [Documentation for Using MongoDB with Spark](https://github.com/mongodb/mongo-hadoop/wiki/Spark-Usage)
- [MongoDB Overview](https://www.mongodb.com/what-is-mongodb)
- [MongoDB Big Data White Paper](https://www.mongodb.com/collateral/big-data-examples-and-guidelines-enterprise-decision-maker)
- [Download MongoDB Enterprise Edition](https://www.mongodb.com/try/download/enterprise)
- [Download MongoDB Community Edition](https://www.mongodb.com/try)
