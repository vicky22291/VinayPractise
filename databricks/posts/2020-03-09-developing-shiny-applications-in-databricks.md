# Developing Shiny Applications in Databricks

- Source: https://www.databricks.com/blog/2020/03/09/developing-shiny-applications-in-databricks.html
- Published: 2020-03-09
- Authors: Yifan Cao, Hossein Falaki
- Categories: engineering, solutions
- Images: 4 total, 0 extracted as architecture

> [Join our live webinar hosted by Data Science Central on March 12 to learn more](https://onlinexperiences.com/Launch/QReg/ShowUUID=342A525C-9556-4D26-901C-65FC5C45889F?ShowKey=82012&AffiliateData=Databricks)

We are excited to announce that you can now develop and test Shiny applications in Databricks! Inside the RStudio Server hosted on Databricks clusters, you can now import the Shiny package and interactively develop Shiny applications. Once completed, you can publish the Shiny application to an external hosting service, while continuing to leverage Databricks to access data securely and at scale.

## What is Shiny?

Shiny is an open-source R package for developing interactive R applications or dashboards. With Shiny, data scientists can easily create interactive web apps and user interfaces using R, even if they don’t have any web development experiences. During development, data scientists can also build Shiny apps to visualize data and gain insights.

Shiny is a popular framework among R developers because it allows them to showcase their work to a wider audience, and have direct business impact. Making Shiny available in Databricks has been a highly requested feature among our customers.

## Databricks for R Developers

As the [Unified Data Analytics Platform](https://www.databricks.com/product/data-lakehouse), Databricks brings together a variety of data users onto a single platform: data engineers, data scientists, data analysts, BI users, and more. The unification drives cross-functional collaboration, improves efficient use of resources, and ultimately leads enterprises to extract value from their datasets.

R as a programming language has an established track record of helping data scientists gain insights from data, and thus is well adopted by enterprise data science teams across many industries. R also boasts a strong open-source ecosystem with many popular packages readily available, including Shiny.

Serving R users is a critical piece to Databricks’s vision of being the Unified Data Analytics Platform. Since the start, Databricks has been introducing new features to serve the diverse needs of R developers:

- Databricks notebooks have supported R since 2015. Users can use R interchangeably with Python, Scala, and SQL in Databricks notebooks ([Blog](https://www.databricks.com/blog/2015/07/13/introducing-r-notebooks-in-databricks.html))
- We introduced support for using sparklyr in Databricks Notebooks in addition to SparkR. Users can use either sparklyr or SparkR in Databricks ([Blog](https://www.databricks.com/blog/2017/05/25/using-sparklyr-databricks.html))
- We enabled hosted RStudio Server inside Databricks so that users can work in the most popular R IDE while taking advantage of many Databricks features ([Blog](https://www.databricks.com/blog/2018/06/27/rstudio-integration.html))

## Adding Shiny to Databricks Ecosystem

We have now made it possible to use the Shiny package in the hosted RStudio server inside Databricks. If the RStudio is hosted on a cluster that uses Databricks Runtime (or Databricks Runtime ML) 6.2 or later, the Shiny install.packages are pre-installed --you can simply import “shiny” in RStudio. If you are using an earlier Runtime version, you can use Databricks Library UI [[AWS](https://docs.databricks.com/libraries/index.html#cran-package) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/libraries/#--cran-package)] to install the Shiny package from CRAN to the cluster, before importing it in RStudio.

Figure 1. Importing Shiny package in RStudio in Databricks

Apache Spark™ is optimally configured for all Databricks clusters. Based on your preference, you can seamlessly use either [SparkR](https://www.databricks.com/glossary/what-is-sparkr) or [sparklyr](https://www.databricks.com/glossary/sparklyr) while developing a Shiny application. Many R developers particularly prefer to use Spark to read data, as Spark offers scalability and connectors to many popular data sources.

Figure 2. Use Spark to read data while developing a Shiny application

When you run the command to run the Shiny application, the application will be displayed in a separate browser window. The Shiny application is running inside an RStudio’s R session. If you stop the R session, the Shiny application window will disappear. This workflow is meant for developers to interactively develop and test a Shiny application, not to host Shiny applications for a broad audience to consume.

Figure 3. A sample Shiny application

## Publishing to Shiny Server or Hosting Service

Once you complete a Shiny application, you can publish the application to a hosting service. Popular products that host Shiny applications include [shinyapps.io](https://www.shinyapps.io/) and [RStudio Connect](https://www.rstudio.com/products/connect/), or [Shiny Server](https://github.com/rstudio/shiny-server).

The hosting service can be outside of Databricks. The deployed Shiny applications can access data through Databricks by connecting to the JDBC/ODBC server [[AWS](https://docs.databricks.com/integrations/bi/jdbc-odbc-bi.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/integrations/bi/jdbc-odbc-bi)]. You can use the JDBC/ODBC driver, which is available on every Databricks cluster, to submit queries to the Databricks cluster. That way, you can continue to take advantage of the security and scalability of Databricks, even if the Shiny application is outside of Databricks.

In summary, with this new feature you can develop Shiny applications on Databricks. You can continue to leverage Databricks’ highly scalable and secure platform after you publish your Shiny application to a hosting service.

Figure 4. Publish a developed Shiny application to a hosting server

## Get Started with Shiny in Databricks

To learn more, don't miss our Shiny User Guide [[AWS](https://docs.databricks.com/spark/latest/sparkr/shiny-rstudio.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/spark/latest/sparkr/shiny-rstudio)] and join us on March 12 for a live webinar on "[Developing and testing Shiny apps](https://onlinexperiences.com/Launch/QReg/ShowUUID=342A525C-9556-4D26-901C-65FC5C45889F?ShowKey=82012&AffiliateData=Databricks)", hosted by Data Science Central, where we will demonstrate these new capabilities.

We are committed to continuing to enhance and expand our product support for R users, and looking forward to your feedback!
