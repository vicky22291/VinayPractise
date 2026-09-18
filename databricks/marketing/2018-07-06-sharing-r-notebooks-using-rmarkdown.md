# Sharing R Notebooks using RMarkdown

- Source: https://www.databricks.com/blog/2018/07/06/sharing-r-notebooks-using-rmarkdown.html
- Published: 2018-07-06
- Authors: Hanyu Cui, Hossein Falaki
- Categories: announcements, product, partners, engineering, data-science-machine-learning, company
- Images: 8 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

*At Databricks, we are thrilled to announce the integration of RStudio with the Databricks *[*Unified Analytics*](https://www.databricks.com/glossary/what-is-unified-analytics)* Platform. You can try it out now with this RMarkdown notebook (Rmd | *[*HTML*](https://docs.databricks.com/_static/notebooks/knn-regression-rstudio-databricks.html)*).*

****Introduction****
Databricks Unified Analytics Platform now supports RStudio Server ([press release](https://www.databricks.com/blog/2018/06/27/rstudio-integration.html)). Users often ask if they can move notebooks between RStudio and Databricks workspace using RMarkdown -- the most popular dynamic R document format. The answer is yes, you can easily export any Databricks R notebook as an RMarkdown file, and vice versa for imports. This allows you to effortlessly share content between a Databricks R notebook and RStudio, combining the best of both environments.

****What is RMarkdown****
[RMarkdown](https://rmarkdown.rstudio.com/) is the dynamic document format [RStudio](https://www.rstudio.com/) uses. It is normal Markdown plus embedded R (or any other language) code that can be executed to produce outputs, including tables and charts, within the document. Hence, after changing your R code, you can just rerun all code in the RMarkdown file rather than redo the whole run-copy-paste cycle. And an RMarkdown file can be directly exported into multiple formats, including HTML, PDF,  and Word.

****Exporting an R Notebook to RMarkdown****
To export an R notebook to an RMarkdown file, first open up the notebook, then select **File > Export >RMarkdown** (

), as shown in the figure below.

This will create a snapshot of your notebook and serialize it as an RMarkdown which will be downloaded to your browser.

You can then launch RStudio and upload the exported RMarkdown file. Below is a screenshot:

****Importing RMarkdown files as Databricks Notebooks****
Importing an RMarkdown file is no different than importing any other file types. The easiest way to do so is to right-click where you want it to be imported and select Import (

) in the context menu:

A dialog box would pop up, just as would with importing any other file types. Importing from both a file and a URL are supported:

You can also click next to a folder’s name, at the top of the workspace area, and select **Import** (

):

****Conclusion****
Using RMarkdown, content can be easily shared between a Databricks R notebook and RStudio. That completes the seamless integration of RStudio in Databricks’ Unified Platform. You are welcome to try it out on the [Databricks Community Edition](https://www.databricks.com/try-databricks) for free. 

****Read More****
To read more about our efforts with SparkR on Databricks, we refer you to the following assets:

- [Parallelizing Large Simulations with Apache SparkR on Databricks](https://www.databricks.com/blog/2017/06/23/parallelizing-large-simulations-apache-sparkr-databricks.html)
- [On-Demand Webinar and FAQ: Parallelize R Code Using Apache Spark](https://www.databricks.com/blog/2017/08/21/on-demand-webinar-and-faq-parallelize-r-code-using-apache-spark.html)
- [Benchmarking Big Data SQL Platforms in the Cloud](https://www.databricks.com/blog/2017/07/12/benchmarking-big-data-sql-platforms-in-the-cloud.html)
- [Using sparklyr in Databricks](https://www.databricks.com/blog/2017/05/25/using-sparklyr-databricks.html)
