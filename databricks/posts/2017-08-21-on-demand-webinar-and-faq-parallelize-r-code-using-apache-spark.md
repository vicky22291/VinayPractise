# On-Demand Webinar and FAQ: Parallelize R Code Using Apache Spark

- Source: https://www.databricks.com/blog/2017/08/21/on-demand-webinar-and-faq-parallelize-r-code-using-apache-spark.html
- Published: 2017-08-21
- Authors: Hossein Falaki, Jules Damji
- Categories: engineering, open-source, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

On August 15th, Data Science Central hosted a live webinar—Parallelize R Code Using Apache Spark—with Databricks’ [Hossein Falaki](https://www.linkedin.com/in/falaki). This webinar introduced [SparkR](https://docs.databricks.com/spark/latest/sparkr/overview.html) concepts, architecture, and a range of new APIs introduced as part of SparkR in Apache Spark 2.x, providing data scientists and statisticians with new capabilities to distribute their existing computation across a Spark cluster.

With the release of Spark 2.0, and subsequent releases, the R API officially supports executing user code on distributed data. This is done primarily through a family of apply() functions.

[DSC Webinar Series: Parallelize R Code Using Apache® Spark™](https://vimeo.com/229780417) from [Tim Matteson](https://vimeo.com/datasciencecentral) on [Vimeo](https://vimeo.com).

If you missed the webinar, you can view it now as well peruse the [slides here](https://www.slideshare.net/databricks/parallelize-r-code-using-apache-spark). Also, we demonstrated two R notebooks:

- [Notebook 1](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/346827/4305245754572172/936056/latest.html)
- [Notebook 2](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/346827/10732546791101/936056/latest.html)

If you’d like free access to Databricks' [Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try the R notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

Toward the end, we held a Q & A, and below are all the questions and their answers.

*If I can use R on top of Spark, why do I need a separate ML library which seems limited right now?*

Although it is possible to implement a wide range of functionality using apply() functions, there are many algorithms that require distributed optimization implementation. Examples include generalized linear models or tree-based models. For these use-cases, you can use SparkR’s ML functionality.

*Regarding spark.lapply: Is necessary to explicitly load the libraries to the workers, and, to "push" shared variables? Something like `clusterEvalQ` and `clusterExport` in the parallel R package?*

Yes, you need to explicitly load libraries on workers. As for variables, you don’t necessarily need to “push” them to workers. This would work fine if the variables are small SparkR’s closure capture will easily take care of them. It is recommended to push auxiliary data to workers directly (using the data plane) if they are large.

*Does each worker in spark lapply work on a partition of the original list or on the whole original list? What are the main differences between `lapply` and `dapply` beside the fact that one works on list and the other works on a dataframe?*

- When using `spark.lapply()` each worker will operate on a single value of the input list.*
- `spark.lapply()` ships its arguments to workers over the control plane. However, `dapply()` and
`gapply()` rely on Spark’s data plane.

*How is it determined which worker works on which data? Which part of the data the worker each get with their closure?*

When using `dapply()` you cannot control which worker gets to process what part of the data. However, with `gapply()` you can make sure that each worker processes all data associated with a specific key.

*Can `gapply()/dapply()` be used for functions or tasks like training a model?*

If the training process can be implemented in parallel or there are ways to combine partial results (from different workers) into a final model, you can use `dapply()/gapply()` for model training.

*Can you give an example of when `dapply()` would actually be useful?*

When using simple transformations that are agnostic to data grouping, you can use `dapply()` or `dapplyCollect()`.

*Are these R Workers part of Microsoft R Server or part of Spark binaries?*

No. SparkR is an open source project which is part of Apache Spark.

*In the `spark.lapply()`, can we not point to a network path for `.libPath()` so we don't have to install.packages() on each node?*

You can.

*When package is missing in worker, does it import from an already downloaded package in driver or from CRAN mirror?*

You need to explicitly install third-party packages on the workers.

*Is possible to share the notebook you have just shown in this webinar?*

Yes, please see the links (Notebook 1 and Notebook 2) above in the post.

*Can we only use SparkR on the Databricks platform? Or can we use it in RStudio as well?*

You can use SparkR in other platforms as well.

*If we have a large data set around 15~16 million, which function do you recommend lappy, `dapply()` or `gapply()`?*

Do not use `spark.lapply()` to distribute your data. First, parallelize your data as a `SparkDataFrame,` and then use `dapply()` or `gapply()` depending on your use case.

*Can SparkR be used for distributed scoring of records for prediction using a model?*

Yes. You can distribute the model object to all workers (for example by persisting to disk and reading from disk), and then you can use `dapply()/gapply()` to score your data against the model in parallel.

*Where is the result dataframe instance stored/resided as the result of parallel processing? Is it distributed over cluster or held by master's memory?*

If you use `dapplyCollect()/gapplyCollect()`, the result is returned as a local `data.frame` object. Otherwise, when using `dapply()/gapply()`, the result is a distributed object stored on all the workers.

`dapply()` (unlike `dapplyCollect()`) will do lazy execution, right?

Yes, `dapply()` and `gapply()` are lazy.
