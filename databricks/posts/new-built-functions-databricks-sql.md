# New Built-in Functions for Databricks SQL

- Source: https://www.databricks.com/blog/new-built-functions-databricks-sql
- Published: 2023-01-20
- Authors: Daniel Tenedorio, Entong Shen, Serge Rielau
- Categories: engineering
- Images: 1 total, 0 extracted as architecture

Built-in functions extend the power of SQL with specific transformations of values for common needs and use cases. For example, the LOG10 [function](https://docs.databricks.com/sql/language-manual/functions/log10.html) accepts a numeric input argument and returns the logarithm with base 10 as a double-precision floating-point result, and the LOWER [function](https://docs.databricks.com/sql/language-manual/functions/lower.html) accepts a string and returns the result of converting each character to lowercase.

As part of our [commitment](https://www.databricks.com/blog/2021/11/16/evolution-of-the-sql-language-at-databricks-ansi-standard-by-default-and-easier-migrations-from-data-warehouses.html) to making it easy to migrate your data warehousing workloads to the Databricks lakehouse platform, we have carefully designed and launched dozens of new built-in functions into the core ANSI compliant Standard SQL dialect over the last year. The open-source Apache Spark community has also made significant contributions to this area, which we have integrated into Databricks runtime as well. In this blog post we mention a useful subset of these new functions and describe, with examples, how they may prove useful for your data processing journeys over the coming days. Please enjoy!

## Process strings and search for elements

Use Databricks SQL to quickly inspect and process strings with new functions in this category. You can quickly check if a string [contains](https://docs.databricks.com/sql/language-manual/functions/contains.html) a substring, inspect its [length](https://docs.databricks.com/sql/language-manual/functions/len.html), [split](https://docs.databricks.com/sql/language-manual/functions/split_part.html) strings, and check for [prefixes](https://docs.databricks.com/sql/language-manual/functions/startswith.html) and [suffixes](https://docs.databricks.com/sql/language-manual/functions/endswith.html).

Use [regular expression operations](https://docs.databricks.com/sql/language-manual/functions/regexp_instr.html) to compare strings against patterns, or specialized functions to convert to or from [numbers](https://docs.databricks.com/sql/language-manual/functions/to_number.html) using specialized formats, and to and from [URL](https://docs.databricks.com/sql/language-manual/functions/url_encode.html) patterns.

## Compare numbers and timestamps

Get into the details by [extracting bits](https://docs.databricks.com/sql/language-manual/functions/bit_get.html) and perform conditional logic on integers and floating-point numbers. Convert floating point numbers to integers by rounding [up](https://docs.databricks.com/sql/language-manual/functions/ceil.html) or [down](https://docs.databricks.com/sql/language-manual/functions/floor.html) with an optional target scale, or compare numbers for [equality](https://docs.databricks.com/sql/language-manual/functions/equal_null.html) with support for NULL values.

Work with temporal values using new strongly-typed conversions. [Cast](https://docs.databricks.com/sql/language-manual/functions/cast.html) input expression to or from one of the INTERVAL data types, query the [current date](https://docs.databricks.com/sql/language-manual/functions/curdate.html), or [add](https://docs.databricks.com/sql/language-manual/functions/dateadd.html) and [subtract](https://docs.databricks.com/sql/language-manual/functions/timestampdiff.html) to dates and timestamps.

## Work with arrays, structs, and maps

Make sophisticated queries for your structured and semi-structured data with the [array](https://docs.databricks.com/sql/language-manual/data-types/array-type.html), [struct](https://docs.databricks.com/sql/language-manual/data-types/struct-type.html), and [map](https://docs.databricks.com/sql/language-manual/data-types/map-type.html) types. Construct new array values with the [array](https://docs.databricks.com/sql/language-manual/functions/array.html) constructor, or inspect existing arrays to see if they [contain specific values](https://docs.databricks.com/sql/language-manual/functions/array_contains.html) or figure out what their [positions](https://docs.databricks.com/sql/language-manual/functions/array_position.html) are. Check [how many elements](https://docs.databricks.com/sql/language-manual/functions/array_size.html) are in an array, or extract specific [elements](https://docs.databricks.com/sql/language-manual/functions/get.html) by [index](https://docs.databricks.com/sql/language-manual/functions/element_at.html).

Maps are a powerful data type that support inserting unique keys associated with values and efficiently extracting them later. Use the [map](https://docs.databricks.com/sql/language-manual/functions/map.html) constructor to create new map values and then [look up values](https://docs.databricks.com/sql/language-manual/functions/map_contains_key.html) later as needed. Once created, you can [concatenate](https://docs.databricks.com/sql/language-manual/functions/map_concat.html) them together, or extract their [keys](https://docs.databricks.com/sql/language-manual/functions/map_keys.html) or [values](https://docs.databricks.com/sql/language-manual/functions/map_values.html) as arrays.

## Perform error-safe computation

Enjoy the benefits of standard SQL with ANSI mode while also preventing your long running ETL pipelines from returning errors with new error-safe functions. Each such function returns NULL instead of raising an exception. For example, take a look at [try_add](https://docs.databricks.com/sql/language-manual/functions/try_add.html), [try_subtract](https://docs.databricks.com/sql/language-manual/functions/try_subtract.html), [try_multiply](https://docs.databricks.com/sql/language-manual/functions/try_multiply.html), and [try_divide](https://docs.databricks.com/sql/language-manual/functions/try_divide.html). You can also perform [casts](https://docs.databricks.com/sql/language-manual/functions/try_cast.html), compute [sums](https://docs.databricks.com/sql/language-manual/functions/try_sum.html) and [averages](https://docs.databricks.com/sql/language-manual/functions/try_avg.html), and safely [convert](https://docs.databricks.com/sql/language-manual/functions/try_to_binary.html) values to and from [numbers](https://docs.databricks.com/sql/language-manual/functions/try_to_number.html) and [timestamps](https://docs.databricks.com/sql/language-manual/functions/try_to_timestamp.html) using custom formatting options.

## Aggregate groups of values together in new ways

Make data-driven decisions by asking questions about groups of values using new *built-in aggregate functions*. For example, you can now return [any value](https://docs.databricks.com/sql/language-manual/functions/any_value.html) in a group, concatenate groups into [arrays](https://docs.databricks.com/sql/language-manual/functions/array_agg.html), and compute histograms. You can also perform statistical calculations by querying the [median](https://docs.databricks.com/sql/language-manual/functions/median.html) or [mode](https://docs.databricks.com/sql/language-manual/functions/mode.html) of a group, or get specific by looking up any arbitrary [percentile](https://docs.databricks.com/sql/language-manual/functions/percentile_cont.html).

The new `regr_*` family of functions help you ask [questions](https://docs.databricks.com/sql/language-manual/functions/regr_avgx.html) about the [values](https://docs.databricks.com/sql/language-manual/functions/regr_avgy.html) of a [group](https://docs.databricks.com/sql/language-manual/functions/regr_count.html) where the input expression(s) are NOT NULL.

Each of these can also be invoked as a [window function](https://docs.databricks.com/sql/language-manual/sql-ref-window-functions.html) using the OVER clause.

## Use encryption

Protect access to your data by [encrypting](https://docs.databricks.com/sql/language-manual/functions/aes_encrypt.html) it at rest and [decrypting](https://docs.databricks.com/sql/language-manual/functions/aes_decrypt.html) it when needed. These functions use the [Advanced Encryption Standard (AES)](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard) to convert values to and from their encrypted equivalents.

## Apply introspection

Programmatically query properties of your Databricks cluster or configuration with SQL. For example, you can ask about the [current version](https://docs.databricks.com/sql/language-manual/functions/current_version.html) of your Databricks SQL or Databricks Runtime environment. You can also now use SQL to return the [list of secret keys](https://docs.databricks.com/sql/language-manual/functions/list_secrets.html) populated so far within the [Databricks secret service](https://docs.databricks.com/security/secrets/index.html) which the current user is authorized to see, and request to [extract specific secret values](https://docs.databricks.com/sql/language-manual/functions/secret.html) by scope and key.

## Build yourself a geospatial lakehouse

Efficiently process and query vast geospatial datasets at scale. In this section, we describe new SQL functions now available for organizing and processing data in this way, along with examples of how to call the functions with different input data types. For a more detailed background, please refer to the separate dedicated "[Processing Geospatial Data at Scale With Databricks](https://www.databricks.com/blog/2019/12/05/processing-geospatial-data-at-scale-with-databricks.html)" blog post.

This is a geospatial visualization of taxi dropoff locations in New York City with cell colors indicating aggregated counts therein.

As of today, Databricks now supports a new collection of geospatial functions operating over [H3](https://www.uber.com/blog/h3/) cells. Each H3 cell represents a unique region of space on the planet at some resolution, and has its own associated unique cell ID represented as a BIGINT or hexadecimal STRING expression. The boundaries of these cells can convert to open formats including [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON), a standard designed for representing simple geographical features using JSON, or [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry), an open text based format for expressing geospatial data using strings (along with [WKB](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary), its binary equivalent).

You can inspect the distance between points by [querying](https://docs.databricks.com/sql/language-manual/functions/h3_distance.html) the H3 cells that are within (grid) distance k of the origin cell. The set of these H3 cells is called the *k-ring* of the origin cell. It is possible to convert input H3 cell IDs to or from their [equivalent](https://docs.databricks.com/sql/language-manual/functions/h3_h3tostring.html) hexadecimal [string representations](https://docs.databricks.com/sql/language-manual/functions/h3_stringtoh3.html).

Furthermore, you can now compute an ARRAY of H3 cell IDs (represented as [BIGINTs](https://docs.databricks.com/sql/language-manual/functions/h3_polyfillash3.html) or [STRINGs](https://docs.databricks.com/sql/language-manual/functions/h3_polyfillash3string.html)) corresponding to hexagons or pentagons that are contained by the input area geography. The [try_ versions](https://docs.databricks.com/sql/language-manual/functions/h3_try_polyfillash3.html) return NULL instead of raising errors.

You can compute the [parent](https://docs.databricks.com/sql/language-manual/functions/h3_toparent.html) or [child](https://docs.databricks.com/sql/language-manual/functions/h3_tochildren.html) H3 cell of the input H3 cell at the specified resolution, or check whether one H3 cell is a [child](https://docs.databricks.com/sql/language-manual/functions/h3_ischildof.html) of another. Representing polygons as (potentially exploded) arrays of H3 cells and points via their H3 cells of containment supports performing very efficient spatial analytics operating on the H3 cells as opposed to original geographic objects. Also, please refer to our recent blog that describes how to perform [spatial analytics at any scale](https://www.databricks.com/blog/2022/12/13/spatial-analytics-any-scale-h3-and-photon.html) and how to [supercharge spatial analytics using H3](https://www.databricks.com/blog/2023/01/12/supercharging-h3-geospatial-analytics.html).

Finally, you can [validate](https://docs.databricks.com/sql/language-manual/functions/h3_validate.html) H3 cells by returning the input value of type BIGINT or STRING if it corresponds to a valid H3 cell ID.

## Databricks SQL lets you do anything

Standards compliance and easy migration came to Databricks SQL previously with the birth of [ANSI mode](https://www.databricks.com/blog/2021/11/16/evolution-of-the-sql-language-at-databricks-ansi-standard-by-default-and-easier-migrations-from-data-warehouses.html), and it already sets the [world record in performance](https://www.databricks.com/blog/2021/11/02/databricks-sets-official-data-warehousing-performance-record.html). With the addition of this wide array of new built-in functions, SQL workloads now have significant newfound expressibility on the lakehouse.

Now feel free to chop up strings, aggregate values, manipulate dates, [analyze geographies](https://www.databricks.com/blog/2019/12/05/processing-geospatial-data-at-scale-with-databricks.html), and more. And if some functionality is missing from these built-ins, check out [Python user-defined functions](https://www.databricks.com/blog/2022/07/22/power-to-the-sql-people-introducing-python-udfs-in-databricks-sql.html) and [SQL user-defined functions](https://www.databricks.com/blog/2021/10/20/introducing-sql-user-defined-functions.html) to define your own logic that behaves the same way at call sites as the built-ins.

Thanks for using Databricks SQL, and happy querying!
