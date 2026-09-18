# On-Demand Webinar: Granular Demand Forecasting At Scale

- Source: https://www.databricks.com/blog/2020/02/21/on-demand-webinar-granular-demand-forecasting-at-scale.html
- Published: 2020-02-21
- Authors: Rob Saker, Bilal Obeidat, Bryan Smith, Navin Albert
- Categories: engineering, solutions, open-source, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

We recently hosted a live webinar — [How Starbucks Forecasts Demand at Scale with Facebook Prophet and Databricks](https://www.databricks.com/explore/retail-demand-forecasting/how-starbucks-forecasts-demand) — During this webinar we learnt why Demand Forecasting is critical to Retail/ CPG firms and how it enables 22 other use cases. Brendan O'Shaughnessy, Data Science Manager at Starbucks walked us through how Starbucks does demand forecasting at scale. We also did a step by step demo on how to perform fine-grained demand forecasts on a day/store/SKU level with Databricks and Facebook's Prophet

Slide deck for webinar [available here](https://www.slideshare.net/NavinAlbert/how-starbucks-forecasts-demand-at-scale-with-facebook-prophet-and-databricks).

## Why Granular Demand Forecasting and How Starbucks does it?

Performing fine-grained forecasts on day-store-SKU is beyond the ability of legacy, data warehousing based forecasting tools. Demand for products varies by product, store and day, and yet traditional demand forecasting solutions perform their forecasts at the aggregate market, week and promo group levels.

With the introduction of the Databricks Unified Data Analytics Platform, retailers are able to see double-digit improvements in their forecast accuracy. They can perform fine-grained forecasts at the SKU, store and day as well as include hundreds of additional features to improve the accuracy of models. They can further enhance their forecasts with localization and the easy inclusion of additional data sets. And they're running these forecasts daily, providing their planners and retail operations team with timely data for better execution.

In this webinar, we reviewed:

- How to perform fine-grained demand forecasts on a day/store/SKU level with Databricks
- How to forecast time series data precisely using [Facebook's Prophet](https://facebook.github.io/prophet/)
- Also, how [Starbucks](https://www.starbucks.com/?utm_term=starbucks&gclid=EAIaIQobChMI1cq9t_vd5wIVoxx9Ch1M8AQaEAAYASAAEgLwIPD_BwE&utm_campaign=BR+-+Brand+-+High+Volume+-+Desktop+-+Exact&utm_medium=cpc&utm_source=google) does custom forecasting with relative ease
- How to train a large number of models using the defacto distributed data processing engine, [Apache Spark™](https://spark.apache.org/)
- Finally, we then presented this data to analysts and managers using [BI tools](https://en.wikipedia.org/wiki/Business_intelligence) to enable the decision making required to drive the required business outcomes

At the end of the webinar, we held a Q&A. Below are the questions and answers:

**Q: What model versioning techniques do you apply to show how models are being improved over time?**

Many of our customers use [MLflow](https://mlflow.org/) to track their experiments. They can use [MLflow](https://mlflow.org/) to track various parameters associated with these models and compare performance metrics across models. This is helpful in tracking improvements as well as libraries they are using to draw insights. [MLflow](https://mlflow.org/) helps take these models from experimentation to production faster.

**Q: Why use UDFs instead of [MLlib](https://spark.apache.org/mllib/)? Is this in order to access [SciKit](https://scikit-learn.org/stable/) learn models?**

We are using [UDFs](https://docs.databricks.com/spark/latest/spark-sql/udf-python.html) so we have the flexibility to leverage any number of libraries. [Facebook Prophet](https://facebook.github.io/prophet/) is very popular right now, but there are numerous libraries we can use for time series. Some are more appropriate in some scenarios than others. So by using UDFs, we get ultimate flexibility while still leveraging parallelization.

**Q: How does [Delta Lake](https://delta.io/) help with Demand Forecasting?**

There are a lot of questions around if I am going to go big, how much is this going to cost me? One thing we clearly want to do is take advantage of the cloud and leverage those resources, run our forecasts at scale as quickly and aggressively as possible. And then when we want to release those resources back to the cloud provider, so we are not paying for that. When I do that, what do I do with my forecasts? I don't want to lose the insights that I draw from running the models. Those results are in a [data frame](https://spark.apache.org/docs/latest/sql-programming-guide.html), which means they ultimately reside in memory. So what we do is, we persist that data and store it. Our preferred format is [Delta Lake](https://delta.io/). [Delta Lake](https://delta.io/) is going to allow me to quickly interact with this data and open it up as a table. By persisting that data, I now have the option to bring a scaled-down cluster to that data, to allow for interactive query. I can use [BI tools](https://en.wikipedia.org/wiki/Business_intelligence) to make these models available to store or distribution managers.

**Q: Facebook's Prophet is a good solution for seasonal time series. How about non-seasonal time series? How is forecasting accuracy determined?**

I agree [Facebook Prophet](https://facebook.github.io/prophet/) works well with seasonal data. With [UDFs](https://docs.databricks.com/spark/latest/spark-sql/udf-python.html) you can use [ARIMA](https://en.wikipedia.org/wiki/Autoregressive_integrated_moving_average) and other common libraries as well. You could also try [RMSE](https://en.wikipedia.org/wiki/Root-mean-square_deviation) and other techniques to figure out which works better for you. Prophet comes with its own tools to determine accuracy as well.

In our blog post, the information that Bilal demoed is carefully documented. In the post, we create a second UDF, where we calculate evaluation metrics. You can use any number of ways to evaluate this and bring them back for consideration as you look at your forecast results.

## Additional Retail/CPG and Demand Forecasting Resources

- Sign-up for a [free trial](https://www.databricks.com/try-databricks) and download these notebooks to start experimenting:
  - [Time Series Forecasting Notebook](https://pages.databricks.com/rs/094-YMS-629/images/Fine-Grained-Time-Series-Forecasting.html?_ga=2.243950405.1545315667.1582041023-1748556641.1581715136)
- [Take a self-guided tour](https://www.databricks.com/explore/retail-demand-forecasting) of our Demand Forecasting resources.
- Read our recent blog [Fine-Grained Time Series Forecasting At Scale With Facebook Prophet And Apache Spark](https://www.databricks.com/blog/2020/01/27/time-series-forecasting-prophet-spark.html) to learn how [Databricks Unified Data Analytics Platform](https://www.databricks.com/product/data-lakehouse) addresses challenges in a timely manner and at a level of granularity that allows the business to make precise adjustments to product inventories
- Download our [Guide to Data Analytics and AI at Scale for Retail and CPG](https://pages.databricks.com/data-science-at-scale-retail.html?_ga=2.10110837.1545315667.1582041023-1748556641.1581715136)
- Visit our [Retail and CPG page](https://www.databricks.com/solutions/industries/retail-industry-solutions) to learn how Dollar Shave Club and Zalando are innovating with Databricks
