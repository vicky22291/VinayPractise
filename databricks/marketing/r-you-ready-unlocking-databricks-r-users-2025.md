# R You Ready? Unlocking Databricks for R Users in 2025

- Source: https://www.databricks.com/blog/r-you-ready-unlocking-databricks-r-users-2025
- Published: 2025-02-18
- Authors: Rafi Kurlansik, Zac Davies
- Categories: engineering
- Images: 2 total, 0 extracted as architecture

**Key takeaways**

- A comprehensive R Developer's Guide to Databricks, covering fundamental concepts, tutorials, and advanced topics like operating Shiny apps on the platform.
- The brickster package on CRAN, offering Databricks REST API wrappers, utility functions, and RStudio integrations for improved workflow.
- Expanded ecosystem support, including packages like odbc, sparklyr, mall, pins, orbital, chattr, ellmer, and pal, providing enhanced functionality for data operations and AI model interactions on Databricks.

As we welcome the new year, we're thrilled to announce several new resources for R users on Databricks: a comprehensive developer guide, the release of [`brickster`](https://github.com/databrickslabs/brickster) on CRAN, migration guides from `SparkR` to `sparklyr`, and expanding support for Databricks in the R ecosystem—particularly in generative AI, thanks to our strong ongoing partnership with [Posit](https://posit.co/use-cases/databricks/).

## R Developer’s Guide to Databricks

For **R users**, we’ve created the [R Developer’s Guide to Databricks](https://www.databricks.com/sites/default/files/2025-02/developers-guide-R.pdf). This guide provides instructions on how to perform your usual R workflows on Databricks and scale them using the platform's capabilities. **For admins**, it offers best practices for managing secure and cost-effective infrastructure, tailored to the needs and preferences of R users.

The guide is systematically organized, starting with the fundamental concepts and architecture of the Databricks Data + AI Platform, followed by a hands-on tutorial to bring these concepts to life. It provides detailed instructions for setting up your development environment, whether using the Databricks code editor or IDEs like RStudio, Positron, or VS Code, with sections on developer tools and package management. Next, it explores scaling R code using Apache Spark™ and Databricks Workflows. The guide concludes with advanced topics, including operating Shiny apps on Databricks.

## brickster

[brickster](https://github.com/databrickslabs/brickster) is the R package built for R developers by an R developer - now on [CRAN](https://cran.r-project.org/web/packages/brickster/index.html)!

`brickster` wraps Databricks REST APIs that are of greatest interest to R users such as Databricks Workflows, file system operations and cluster management. It also includes a rich set of utility functions and integrations with RStudio, bringing Databricks to you. It’s well documented with vignettes for [job automation](https://databrickslabs.github.io/brickster/articles/managing-jobs.html) and [cluster management](https://databrickslabs.github.io/brickster/articles/cluster-management.html), and examples for each function.

Let’s consider two examples of how `brickster` can bring Databricks to RStudio. First, the `open_workspace()` function lets you browse the Databricks Workspace directly from the RStudio Connections Pane:

Second, for the most immersive developer experience, check out the `db_repl()` function. It creates a local [REPL](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop) (read-eval-print loop) where every command executes remotely on Databricks in the language of your choice.

Whether you're a rookie or a power user, if you work with Databricks from an IDE, give `brickster` a try—it’s worth it.

## SparkR deprecation and migration guide to sparklyr

`SparkR` and `sparklyr` are both R packages designed to work with Apache Spark™, but differ significantly in design, syntax, and integration with the broader R ecosystem. This complexity can be confusing to R users new to Spark, so beginning with Apache Spark™ 4.x `SparkR` will be deprecated, and `sparklyr` will become the sole recommended package. To aid users in code migration from one to the other, we have compiled another guide that illustrates the differences between each package, including many specific function mappings.

You can find the guide on GitHub [here](https://zacdav-db.github.io/dbrx-r-compendium/chapters/data-eng/sparkr-migration.html).

## Databricks support in the R ecosystem

In addition to [`brickster`](https://github.com/databrickslabs/brickster), the broader R ecosystem is increasing support for working with Databricks.

| Package | Support for Databricks |
|---|---|
| odbc | The new `odbc::databricks()` function simplifies connecting to SQL Warehouses (see here for more). |
| sparklyr | Works with Databricks Connect V2, and with SparkR being deprecated in Spark 4.0, `sparklyr` will become the primary package for using Spark in R. |
| mall | Allows you to call Databricks SQL AI Functions from R. Example usage here. |
| pins | UC Volume backed pins! Seamless integration with pins package. |
| orbital | Run tidymodels predictions on Spark DataFrames |
| chattr | Support added for Databricks Foundation Models API (see here for more). |
| ellmer | Simple interface for chats with foundation models hosted on Databricks or models available through AI Gateway. |
| pal | Provides a library of ergonomic LLM assistants designed to help you complete repetitive, hard-to-automate tasks quickly. Any model supported by `ellmer` is supported by `pal`.(GitHub) |

## What’s Next

As we step into a new year, the future for R users on Databricks has never looked brighter. With the release of the [comprehensive R Developers’ Guide](https://www.databricks.com/sites/default/files/2025-02/developers-guide-R.pdf), the introduction of the powerful [`brickster`](https://github.com/databrickslabs/brickster) package, and an ever-expanding ecosystem of R tools supporting Databricks, there’s never been a better time to explore, build, and scale your data & AI work on the platform. We especially want to thank [Posit](https://posit.co/use-cases/databricks/) for their continued support of the R ecosystem on Databricks – expect to see more great things from this partnership in the coming months. Cheers to a productive and innovative year ahead!
