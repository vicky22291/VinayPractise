# A Comprehensive Look at Dates and Timestamps in Apache Spark™ 3.0

- Source: https://www.databricks.com/blog/2020/07/22/a-comprehensive-look-at-dates-and-timestamps-in-apache-spark-3-0.html
- Published: 2020-07-22
- Authors: Maxim Gekk, Wenchen Fan, Hyukjin Kwon
- Categories: engineering, open-source
- Images: 4 total, 0 extracted as architecture

Apache Spark is a very popular tool for processing structured and unstructured data. When it comes to processing structured data, it supports many basic data types, like integer, long, double, string, etc. Spark also supports more complex data types, like the `Date` and `Timestamp`, which are often difficult for developers to understand. In this blog post, we take a deep dive into the Date and Timestamp types to help you fully understand their behavior and how to avoid some common issues. In summary, this blog covers four parts:

1. The definition of the Date type and the associated calendar. It also covers the calendar switch in Spark 3.0.
2. The definition of the Timestamp type and how it relates to time zones. It also explains the detail of time zone offset resolution, and the subtle behavior changes in the new time API in Java 8, which is used by Spark 3.0.
3. The common APIs to construct date and timestamp values in Spark.
4. The common pitfalls and best practices to collect date and timestamp objects on the Spark driver.

## Date and calendar

The definition of a `Date` is very simple: It's a combination of the *year*, *month* and *day* fields, like (year=2012, month=12, day=31). However, the values of the year, month and day fields have constraints, so that the date value is a valid day in the real world. For example, the value of month must be from 1 to 12, the value of day must be from 1 to 28/29/30/31 (depending on the year and month), and so on.

These constraints are defined by one of many possible calendars. Some of them are only used in specific regions, like the [Lunar calendar](https://en.wikipedia.org/wiki/Lunar_calendar). Some of them are only used in history, like the [Julian calendar](https://en.wikipedia.org/wiki/Julian_calendar). At this point, the [Gregorian calendar](https://en.wikipedia.org/wiki/Gregorian_calendar) is the de facto international standard and is used almost everywhere in the world for civil purposes. It was introduced in 1582 and is extended to support dates before 1582 as well. This extended calendar is called the [Proleptic Gregorian calendar](https://en.wikipedia.org/wiki/Proleptic_Gregorian_calendar).

Starting from version 3.0, Spark uses the Proleptic Gregorian calendar, which is already being used by other data systems like pandas, R and Apache Arrow. Before Spark 3.0, it used a combination of the Julian and Gregorian calendar: For dates before 1582, the Julian calendar was used, for dates after 1582 the Gregorian calendar was used. This is inherited from the legacy `java.sql.Date` API, which was superseded in Java 8 by `java.time.LocalDate`, which uses the Proleptic Gregorian calendar as well.

Notably, the Date type does not consider time zones.

## Timestamp and time zone

The `Timestamp` type extends the Date type with new fields: *hour*, *minute*, *second (which can have a fractional part) *and together with a global (session scoped) time zone. It defines a concrete time instant on Earth. For example, (year=2012, month=12, day=31, hour=23, minute=59, second=59.123456) with session timezone UTC+01:00. When writing timestamp values out to non-text data sources like Parquet, the values are just instants (like timestamp in UTC) that have no time zone information. If you write and read a timestamp value with different session timezone, you may see different values of the hour/minute/second fields, but they are actually the same concrete time instant.

The hour, minute and second fields have standard ranges: 0–23 for hours and 0–59 for minutes and seconds. Spark supports fractional seconds with up to microsecond precision. The valid range for fractions is from 0 to 999,999 microseconds.

At any concrete instant, we can observe many different values of wall clocks, depending on time zone.

And conversely, any value on wall clocks can represent many different time instants. The time zone offset allows us to unambiguously bind a local timestamp to a time instant. Usually, time zone offsets are defined as offsets in hours from Greenwich Mean Time (GMT) or [UTC+0](https://en.wikipedia.org/wiki/UTC%C2%B100:00) ([Coordinated Universal Time](https://en.wikipedia.org/wiki/Coordinated_Universal_Time)). Such a representation of time zone information eliminates ambiguity, but it is inconvenient for end users. Users prefer to point out a location around the globe such as `America/Los_Angeles` or `Europe/Paris`.

This additional level of abstraction from zone offsets makes life easier but brings its own problems. For example, we now have to maintain a special time zone database to map time zone names to offsets. Since Spark runs on the JVM, it delegates the mapping to the Java standard library, which loads data from the [Internet Assigned Numbers Authority Time Zone Database (IANA TZDB)](https://www.iana.org/time-zones). Furthermore, the mapping mechanism in Java's standard library has some nuances that influence Spark's behavior. We focus on some of these nuances below.

Since Java 8, the JDK has exposed a new API for date-time manipulation and time zone offset resolution, and Spark migrated to this new API in version 3.0. Although the mapping of time zone names to offsets has the same source, IANA TZDB, it is implemented differently in Java 8 and higher versus Java 7.

As an example, let's take a look at a timestamp before the year 1883 in the

`America/Los_Angeles` time zone: `1883-11-10 00:00:00`. This year stands out from others because on November 18, 1883, all North American railroads switched to a new standard time system that henceforth governed their timetables.
 Using the Java 7 time API, we can obtain time zone offset at the local timestamp as -08:00:

Java 8 API functions return a different result:

Prior to November 18, 1883, time of day was a local matter, and most cities and towns used some form of local solar time, maintained by a well-known clock (on a church steeple, for example, or in a jeweler's window). That's why we see such a strange time zone offset.

The example demonstrates that Java 8 functions are more precise and take into account historical data from IANA TZDB. After switching to the Java 8 time API, Spark 3.0 benefited from the improvement automatically and became more precise in how it resolves time zone offsets.

As we mentioned earlier, Spark 3.0 also switched to the Proleptic Gregorian calendar for the date type. The same is true for the timestamp type. The [ISO SQL:2016](https://blog.ansi.org/2018/10/sql-standard-iso-iec-9075-2016-ansi-x3-135/) standard declares the valid range for timestamps is from `0001-01-01 00:00:00` to `9999-12-31 23:59:59.999999`. Spark 3.0 fully conforms to the standard and supports all timestamps in this range. Comparing to Spark 2.4 and earlier, we should highlight the following sub-ranges:

1. `0001-01-01 00:00:00..1582-10-03 23:59:59.999999`. Spark 2.4 uses the Julian calendar and doesn't conform to the standard. Spark 3.0 fixes the issue and applies the Proleptic Gregorian calendar in internal operations on timestamps such as getting year, month, day, etc. Due to different calendars, some dates that exist in Spark 2.4 don't exist in Spark 3.0. For example, 1000-02-29 is not a valid date because 1000 isn't a leap year in the Gregorian calendar. Also, Spark 2.4 resolves time zone name to zone offsets incorrectly for this timestamp range.
2. `1582-10-04 00:00:00..1582-10-14 23:59:59.999999`. This is a valid range of local timestamps in Spark 3.0, in contrast to Spark 2.4 where such timestamps didn't exist.
3. `1582-10-15 00:00:00..1899-12-31 23:59:59.999999`. Spark 3.0 resolves time zone offsets correctly using historical data from IANA TZDB. Compared to Spark 3.0, Spark 2.4 might resolve zone offsets from time zone names incorrectly in some cases, as we showed above in the example.
4. `1900-01-01 00:00:00..2036-12-31 23:59:59.999999`. Both Spark 3.0 and Spark 2.4 conform to the ANSI SQL standard and use Gregorian calendar in date-time operations such as getting the day of the month.
5. `2037-01-01 00:00:00..9999-12-31 23:59:59.999999`. Spark 2.4 can resolve time zone offsets and in particular daylight saving time offsets incorrectly because of the JDK bug #8073446. Spark 3.0 does not suffer from this defect.

One more aspect of mapping time zone names to offsets is overlapping of local timestamps that can happen due to daylight saving time (DST) or switching to another standard time zone offset. For instance, on `3 November 2019, 02:00:00` clocks were turned backward 1 hour to `01:00:00`. The local timestamp

`2019-11-03 01:30:00` America/Los_Angeles can be mapped either to `2019-11-03 01:30:00 UTC-08:00` or `2019-11-03 01:30:00 UTC-07:00`. If you don't specify the offset and just set the time zone name (e.g., `'2019-11-03 01:30:00 America/Los_Angeles'`), Spark 3.0 will take the earlier offset, typically corresponding to "summer." The behavior diverges from Spark 2.4 which takes the "winter" offset. In the case of a gap, where clocks jump forward, there is no valid offset. For a typical one-hour daylight saving time change, Spark will move such timestamps to the next valid timestamp corresponding to "summer" time.

As we can see from the examples above, the mapping of time zone names to offsets is ambiguous, and it is not one to one. In the cases when it is possible, we would recommend specifying exact time zone offsets when making timestamps, for example `timestamp` `'2019-11-03 01:30:00 UTC-07:00'`.

Let's move away from zone name to offset mapping, and look at the ANSI SQL standard. It defines two types of timestamps:

1. `TIMESTAMP WITHOUT TIME ZONE` or `TIMESTAMP` - Local timestamp as (YEAR, MONTH, DAY, HOUR, MINUTE, SECOND). These kinds of timestamps are not bound to any time zone, and actually are wall clock timestamps.
2. `TIMESTAMP WITH TIME ZONE` - Zoned timestamp as (YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, TIMEZONE_HOUR, TIMEZONE_MINUTE). The timestamps represent an instant *in the UTC time zone* + a time zone offset (in hours and minutes) associated with each value.

The time zone offset of a `TIMESTAMP WITH TIME ZONE` does not affect the physical point in time that the timestamp represents, as that is fully represented by the UTC time instant given by the other timestamp components. Instead, the time zone offset only affects the default behavior of a timestamp value for display, date/time component extraction (e.g. `EXTRACT`), and other operations that require knowing a time zone, such as adding months to a timestamp.

Spark SQL defines the timestamp type as `TIMESTAMP WITH SESSION TIME ZONE`, which is a combination of the fields (`YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`, `SESSION TZ`) where the `YEAR` through `SECOND` field identify a time instant in the UTC time zone, and where `SESSION TZ` is taken from the SQL config `spark.sql.session.timeZone`. The session time zone can be set as:

- Zone offset `'(+|-)HH:mm'`. This form allows us to define a physical point in time unambiguously.
- Time zone name in the form of region ID `'area/city'`, such as `'America/Los_Angeles'`. This form of time zone info suffers from some of the problems that we described above like overlapping of local timestamps. However, each UTC time instant is unambiguously associated with one time zone offset for any region ID, and as a result, each timestamp with a region ID based time zone can be unambiguously converted to a timestamp with a zone offset.

By default, the session time zone is set to the default time zone of the *Java** virtual machine*.

Spark's `TIMESTAMP WITH SESSION TIME ZONE` is different from:

1. `TIMESTAMP WITHOUT TIME ZONE`, because a value of this type can map to multiple physical time instants, but any value of `TIMESTAMP WITH SESSION TIME ZONE` is a concrete physical time instant. The SQL type can be emulated by using one fixed time zone offset across all sessions, for instance UTC+0. In that case, we could consider timestamps at UTC as local timestamps.
2. `TIMESTAMP WITH TIME ZONE`, because according to the SQL standard column values of the type can have different time zone offsets. That is not supported by Spark SQL.

We should notice that timestamps that are associated with a global (session scoped) time zone are not something newly invented by Spark SQL. RDBMSs such as Oracle provide a similar type for timestamps too: [TIMESTAMP WITH LOCAL TIME ZONE](https://docs.oracle.com/cd/E11882_01/server.112/e10729/ch4datetime.htm#i1006169).

## Constructing dates and timestamps

Spark SQL provides a few methods for constructing date and timestamp values:

1. Default constructors without parameters: `CURRENT_TIMESTAMP()` and `CURRENT_DATE()`.
2. From other primitive Spark SQL types, such as `INT`, `LONG`, and `STRING`
3. From external types like Python `datetime` or Java classes `java.time.LocalDate/Instant`.
4. Deserialization from data sources CSV, JSON, Avro, Parquet, ORC or others.

The function `MAKE_DATE` introduced in Spark 3.0 takes three parameters: `YEAR`, `MONTH` of the year, and `DAY` in the month and makes a `DATE` value. All input parameters are implicitly converted to the `INT` type whenever possible. The function checks that the resulting dates are valid dates in the Proleptic Gregorian calendar, otherwise it returns `NULL`. For example in PySpark:

To print DataFrame content, let's call the `show()` action, which converts dates to strings on executors and transfers the strings to the driver to output them on the console:

Similarly, we can make timestamp values via the `MAKE_TIMESTAMP` functions. Like `MAKE_DATE`, it performs the same validation for date fields, and additionally accepts time fields `HOUR (0-23)`, `MINUTE (0-59)` and `SECOND (0-60)`. `SECOND` has the type `Decimal`(precision = 8, scale = 6) because seconds can be passed with the fractional part up to microsecond precision. For example in PySpark:

As we did for dates, let's print the content of the `ts` DataFrame using the `show()` action. In a similar way, show() converts timestamps to strings but now it takes into account the session time zone defined by the SQL config `spark.sql.session.timeZone`. We will see that in the following examples.

Spark cannot create the last timestamp because this date is not valid: 2019 is not a leap year.

You might notice that we didn't provide any time zone information in the example above. In that case, Spark takes a time zone from the SQL configuration `spark.sql.session.timeZone` and applies it to function invocations. You can also pick a different time zone by passing it as the last parameter of `MAKE_TIMESTAMP`. Here is an example in PySpark:

As the example demonstrates, Spark takes into account the specified time zones but adjusts all local timestamps to the session time zone. The original time zones passed to the `MAKE_TIMESTAMP` function will be lost because the `TIMESTAMP WITH SESSION TIME ZONE` type assumes that all values belong to one time zone, and it doesn't even store a time zone per every value. According to the definition of the `TIMESTAMP WITH SESSION TIME ZONE`, Spark stores local timestamps in the UTC time zone, and uses the session time zone while extracting date-time fields or converting the timestamps to strings.

Also, timestamps can be constructed from the `LONG` type via casting. If a `LONG` column contains the number of seconds since the epoch 1970-01-01 00:00:00Z, it can be cast to Spark SQL's `TIMESTAMP`:

Unfortunately, this approach doesn't allow us to specify the fractional part of seconds. In the future, Spark SQL will provide special functions to make timestamps from seconds, milliseconds and microseconds since the epoch: `timestamp_seconds()`, `timestamp_millis()` and `timestamp_micros()`.

Another way is to construct dates and timestamps from values of the `STRING` type. We can make literals using special keywords:

or via casting that we can apply for all values in a column:

The input timestamp strings are interpreted as local timestamps in the specified time zone or in the session time zone if a time zone is omitted in the input string. Strings with unusual patterns can be converted to timestamp using the `to_timestamp()` function. The supported patterns are described in [Datetime Patterns for Formatting and Parsing](https://spark.apache.org/docs/latest/sql-ref-datetime-pattern.html):

The function behaves similarly to `CAST` if you don't specify any pattern.

For usability, Spark SQL recognizes special string values in all methods above that accept a string and return a timestamp and date:

- **epoch** is an alias for date '1970-01-01' or timestamp `'1970-01-01 00:00:00Z'`
- **now** is the current timestamp or date at the session time zone. Within a single query it always produces the same result.
- **today** is the beginning of the current date for the `TIMESTAMP` type or just current date for the `DATE` type.
- **tomorrow** is the beginning of the next day for timestamps or just the next day for the `DATE` type.
- **yesterday** is the day before current one or its beginning for the `TIMESTAMP` type.

For example:

One of Spark's great features is creating `Datasets` from existing collections of external objects at the driver side, and creating columns of corresponding types. Spark converts instances of external types to semantically equivalent internal representations. PySpark allows to create a `Dataset` with `DATE` and `TIMESTAMP` columns from Python collections, for instance:

PySpark converts Python's datetime objects to internal Spark SQL representations at the driver side using the system time zone, which can be different from Spark's session time zone settings `spark.sql.session.timeZone`. The internal values don't contain information about the original time zone. Future operations over the parallelized dates and timestamps value will take into account only Spark SQL sessions time zone according to the `TIMESTAMP WITH SESSION TIME ZONE` type definition.

In a similar way as we demonstrated above for Python collections, Spark recognizes the following types as external date-time types in Java/Scala APIs:

- java.sql.Date and java.time.LocalDate as external types for Spark SQL's DATE type
- java.sql.Timestamp and java.time.Instant for the TIMESTAMP type.

There is a difference between `java.sql.*` and `java.time.*` types. The `java.time.LocalDate` and `java.time.Instant` were added in Java 8, and the types are based on the Proleptic Gregorian calendar — the same calendar that is used by Spark from version 3.0. The `java.sql.Date` and `java.sql.Timestamp` have another calendar underneath — the hybrid calendar (Julian + Gregorian since `1582-10-15`), which is the same as the legacy calendar used by Spark versions before 3.0. Due to different calendar systems, Spark has to perform additional operations during conversions to internal Spark SQL representations, and rebase input dates/timestamp from one calendar to another. The rebase operation has a little overhead for modern timestamps after the year 1900, and it can be more significant for old timestamps.

The example below shows making timestamps from Scala collections. In the first example, we construct a `java.sql.Timestamp` object from a string. The `valueOf` method interprets the input strings as a local timestamp in the default JVM time zone which can be different from Spark's session time zone. If you need to construct instances of `java.sql.Timestamp` or `java.sql.Date` in specific time zone, we recommend to have a look at [`java.text.SimpleDateFormat`](https://docs.oracle.com/javase/7/docs/api/java/text/SimpleDateFormat.html) (and its method setTimeZone) or [`java.util.Calendar`](https://docs.oracle.com/javase/7/docs/api/java/util/Calendar.html)**.**

Similarly, we can make a DATE column from collections of `java.sql.Date` or `java.LocalDate`. Parallelization of `java.LocalDate` instances is fully independent of either Spark's session time zone or JVM default time zone, but we cannot say the same about parallelization of `java.sql.Date` instances. There are nuances:

1. `java.sql.Date` instances represent local dates at the default JVM time zone on the driver
2. For correct conversions to Spark SQL values, the default JVM time zone on the driver and executors must be the same.

To avoid any calendar and time zone related issues, we recommend Java 8 types `java.LocalDate/Instant` as external types in parallelization of Java/Scala collections of timestamps or dates.

## Collecting dates and timestamps

The reverse operation for parallelization is collecting dates and timestamps from executors back to the driver and returning a collection of external types. For example above, we can pull the DataFrame back to the driver via the `collect()` action:

Spark transfers internal values of dates and timestamps columns as time instants in the UTC time zone from executors to the driver, and performs conversions to Python datetime objects in the system time zone at the driver, **not** using Spark SQL session time zone. `collect()` is different from the `show()` action described in the previous section. `show()` uses the session time zone while converting timestamps to strings, and collects the resulted strings on the driver.

In Java and Scala APIs, Spark performs the following conversions by default:

- Spark SQL's `DATE` values are converted to instances of `java.sql.Date`.
- Timestamps are converted to instances of `java.sql.Timestamp`.

Both conversions are performed in the default JVM time zone on the driver. In this way, to have the same date-time fields that we can get via `Date.getDay()`, `getHour()`, etc. and via Spark SQL functions `DAY`, `HOUR`, the default JVM time zone on the driver and the session time zone on executors should be the same.

Similarly to making dates/timestamps from `java.sql.Date/Timestamp`, Spark 3.0 performs rebasing from the Proleptic Gregorian calendar to the hybrid calendar (Julian + Gregorian). This operation is almost free for modern dates (after the year 1582) and timestamps (after the year 1900), but it could bring some overhead for ancient dates and timestamps.

We can avoid such calendar-related issues, and ask Spark to return `java.time` types, which were added since Java 8. If we set the SQL config `spark.sql.datetime.java8API.enabled` to true, the `Dataset.collect()` action will return:

- `java.time.LocalDate` for Spark SQL's `DATE` type
- `java.time.Instant` for Spark SQL's `TIMESTAMP` type

Now the conversions don't suffer from the calendar-related issues because Java 8 types and Spark SQL 3.0 are both based on the Proleptic Gregorian calendar. The `collect()` action doesn't depend on the default JVM time zone any more. The timestamp conversions don't depend on time zone at all. Regarding to date conversion, it uses the session time zone from the SQL config `spark.sql.session.timeZone`. For example, let's look at a Dataset with `DATE` and  `TIMESTAMP` columns, set the default JVM time zone to Europe/Moscow, but the session time zone to `America/Los_Angeles`.

The `show()` action prints the timestamp at the session time `America/Los_Angeles`, but if we collect the Dataset, it will be converted to `java.sql.Timestamp` and printed at `Europe/Moscow` by the `toString` method:

Actually, the local timestamp 2020-07-01 00:00:00 is 2020-07-01T07:00:00Z at UTC. We can observe that if we enable Java 8 API and collect the Dataset:

The `java.time.Instant` object can be converted to any local timestamp later independently from the global JVM time zone. This is one of the advantages of `java.time.Instant` over `java.sql.Timestamp`. The former one requires changing the global JVM setting, which influences other timestamps on the same JVM. Therefore, if your applications process dates or timestamps in different time zones, and the applications should not clash with each other while collecting data to the driver via Java/Scala `Dataset.collect()` API, we recommend switching to Java 8 API using the SQL config `spark.sql.datetime.java8API.enabled`.

## Conclusion

In this blog post, we described Spark SQL `DATE` and `TIMESTAMP` types. We showed how to construct date and timestamp columns from other primitive Spark SQL types and external Java types, and how to collect date and timestamp columns back to the driver as external Java types. Since version 3.0, Spark switched from the hybrid calendar, which combines Julian and Gregorian calendars, to the Proleptic Gregorian calendar (see [SPARK-26651](https://issues.apache.org/jira/browse/SPARK-26651) for more details). This allowed Spark to eliminate many issues such as we demonstrated earlier. For backward compatibility with previous versions, Spark still returns timestamps and dates in the hybrid calendar (`java.sql.Date` and `java.sql.Timestamp`) from the collect like actions. To avoid calendar and time zone resolution issues when using the Java/Scala's collect actions, Java 8 API can be enabled via the SQL config `spark.sql.datetime.java8API.enabled`. Try it out today [free on Databricks](https://www.databricks.com/try-databricks) as part of our Databricks Runtime 7.0.

O'Reilly Learning Spark Book

Free 2nd Edition includes updates on Spark 3.0, including the new Python type hints for Pandas UDFs, new date/time implementation, etc.

[Free Download](https://www.databricks.com/p/ebook/the-big-book-of-data-engineering?itm_data=blog-link-learningspark)
