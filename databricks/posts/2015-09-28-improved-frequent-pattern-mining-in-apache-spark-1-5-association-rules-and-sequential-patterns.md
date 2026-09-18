# Improved Frequent Pattern Mining in Apache Spark 1.5: Association Rules and Sequential Patterns

- Source: https://www.databricks.com/blog/2015/09/28/improved-frequent-pattern-mining-in-apache-spark-1-5-association-rules-and-sequential-patterns.html
- Published: 2015-09-28
- Authors: Feynman Liang, Jiajin Zhang, Dandan Tu
- Categories: engineering, data-science-machine-learning, open-source
- Images: 0 total, 0 extracted as architecture

*We would like to thank Jiajin Zhang and Dandan Tu from Huawei for contributing to this blog.*

*To get started mining patterns from massive datasets, [download Apache Spark 1.5](https://spark.apache.org/downloads.html) or [sign up for a 14-day free trial of Databricks today](https://accounts.cloud.databricks.com/registration.html#signup).*

---

Discovering frequent patterns hiding in a big dataset has application across a broad range of use cases. Retailers may be interested in finding items that are frequently purchased together from a large transaction database. Biologists may be interested in frequent DNA or amino acid sequences. In Apache Spark 1.5, we have significantly improved Spark’s frequent pattern mining capabilities by adding algorithms for association rule generation and sequential pattern mining.

## Association rules generation

Association rules are generated from frequent itemsets, subsets of items that appear frequently across transactions. Frequent itemset mining was first added in Spark 1.3 using the Parallel FP-growth algorithm. Spark 1.4 adds a new Python API for FP-growth. We refer readers to [our previous blog post](https://www.databricks.com/blog/2015/04/17/new-mllib-algorithms-in-spark-1-3-fp-growth-and-power-iteration-clustering.html) for more details.

In addition to identifying frequent itemsets, we are often interested in learning [association rules](https://en.wikipedia.org/wiki/Association_rule_learning).

For example, in a retailer’s transaction database, a rule {toothbrush, floss} => {toothpaste} with a *confidence value* 0.8 would indicate that 80% of customers who buy a toothbrush and floss also purchase a toothpaste in the same transaction. The retailer could then use this information, put both toothbrush and floss on sale, but raise the price of toothpaste to increase overall profit.

Spark 1.5 adds support for distributed generation of association rules. Rule generation is done via a simple method call to [FPGrowthModel](https://spark.apache.org/docs/latest/mllib-frequent-pattern-mining.html#fp-growth) with a min confidence value, for example:

val transactions: RDD[Array[String]] = ...
 val model = new FPGrowth()
 .setMinSupport(0.2)
 .setNumPartitions(10)
 .run(transactions)
 val minConfidence = 0.8
 model.generateAssociationRules(minConfidence).collect().foreach {
 rule =>
 println(rule.antecedent.mkString(",") + " => " +
 rule.consequent.mkString(",")
 )
 }

## Sequential pattern mining

Unlike frequent itemsets, where the items in a transaction are unordered, sequential pattern mining takes the order of items into account. In many use cases ranging from text mining to [DNA sequence](https://www.databricks.com/glossary/dna-sequence) motif discovery, we care about the order in which items appear in a pattern.

Sequential pattern mining is widely used in Huawei, a Fortune Global 500 telecommunications company. For example, a mobile network of millions of users could generate several hundred GBs of session signaling data per day. Among the signaling sequences, we want to extract frequent sequential patterns like routing updates, activation failures, and broadcasting timeouts that could potentially lead to customer complaints. By identifying those patterns in real traffic, we can proactively reach out to customers with potential issues and help improve their experience.

Thanks to a collaboration between Databricks and Huawei, especially to Huawei for initiating the effort, sharing their use cases, and making significant code contribution, we are proud to announce support for parallel sequential pattern mining in Spark 1.5. This latest version ships with a parallel implementation of the PrefixSpan algorithm originally described by [Pei et al](https://ieeexplore.ieee.org/document/914830/).

## Example: mining frequent sequential sign language patterns

To demonstrate PrefixSpan, we will mine frequent sequential patterns from the American Sign Language database [provided by Boston University](https://www.bu.edu/). Running PrefixSpan to discover frequent sequential patterns requires only a few lines of code:

val sequences: RDD[Array[Array[String]]] = ...
 val prefixSpan = new PrefixSpan()
 .setMinSupport(0.6)
 .setMaxPatternLength(10)
 val patterns = prefixSpan.run(sequences)

From this, we discover that common sequential patterns in the database include:

where each item indicates a sign or a gesture. For details, please see [this gist](https://gist.github.com/feynmanliang/63a2835f6ba2bf35b85a).

## Implementation

We followed the PrefixSpan algorithm but made modifications to parallelize the algorithm in a novel way for running on Spark. At a high level, our algorithm iteratively extends the lengths of prefixes until its associated projected database (i.e. the set of all sequences with that given prefix) is small enough to fit on a single machine. We then process each of these projected databases locally and combine the results to yield all of the sequential patterns.

## What’s next?

The improvements to frequent pattern mining have been a collaboration between many Spark contributors. This work is pushing the limits on distributed pattern mining. Ongoing work includes: model import/export for [FPGrowth](https://issues.apache.org/jira/browse/SPARK-6724) and [PrefixSpan](https://issues.apache.org/jira/browse/SPARK-10386), a [Python API for PrefixSpan](https://issues.apache.org/jira/browse/SPARK-10028), [optimizing PrefixSpan for single-item itemsets](https://issues.apache.org/jira/browse/SPARK-10678), etc. To get involved, please check the [MLlib 1.6 roadmap](https://issues.apache.org/jira/browse/SPARK-10324).
