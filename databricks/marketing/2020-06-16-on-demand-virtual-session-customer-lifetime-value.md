# On-Demand Virtual Session: Customer Lifetime Value

- Source: https://www.databricks.com/blog/2020/06/16/on-demand-virtual-session-customer-lifetime-value.html
- Published: 2020-06-16
- Authors: Rob Saker, Bryan Smith, Hector Leano, Steve Sobel
- Categories: engineering, data-science-machine-learning, platform, open-source
- Images: 0 total, 0 extracted as architecture

Before you can provide personalized services and offers to your customers, you need to know who they are. In this virtual workshop, retail and media experts will demonstrate how to build advanced customer lifetime value (CLV) models. From there companies can provide the right investment into each customer in order to create personalized offers, save tactics, and experiences.

In this on-demand virtual session, Steve Sobel and Rob Saker talk about the need, impact and challenges of companies pursuing customer lifetime value, and why Databricks Unified Data Analytics Platform is optimal for helping to simplify how data is processed and analyzed for CLV. Then [Bryan Smith](https://www.databricks.com/blog/author/bryan-smith), Databricks Global Technical Leader for Retail, walks through different ways of calculating CLV using retail data, though this will be applicable across all industries looking to understand the value of each customer using historical behavioral patterns. There was strong audience participation during the session. We’ve provided written responses to questions below.

[Watch now](https://pages.databricks.com/202005-US-EV-VIRTUALWORKSHOP-RETAIL-ME-OD-thank-you-webinar.html)

**Notebooks from the webinar**

- [RFM segmentation](https://www.databricks.com/notebooks/Customer%20Lifetime%20Value%20Virtual%20Workshop/00%20RFM%20Segmentation.html) (Recency, Frequency, Monetary)
- [CLV Formula](https://www.databricks.com/notebooks/Customer%20Lifetime%20Value%20Virtual%20Workshop/01%20The%20CLV%20Formula.html) (Customer LIfetime Value)
- [BTYD Models](https://www.databricks.com/notebooks/Customer%20Lifetime%20Value%20Virtual%20Workshop/02%20The%20BTYD%20Models.html) (“Buy ‘til you die”)
- [Regression Models](https://www.databricks.com/notebooks/Customer%20Lifetime%20Value%20Virtual%20Workshop/03%20The%20Regression%20Models.html)

**Relevant blog posts**

- [Customer Lifetime Value Part 1: Estimating Customer Lifetime Values](https://www.databricks.com/blog/2020/06/03/customer-lifetime-value-part-1-estimating-customer-lifetimes.html)
- [Customer Lifetime Value Part 2: Estimating Future Spend](https://www.databricks.com/blog/2020/06/17/customer-lifetime-value-part-2-estimating-future-spend.html)

**Q&A from chat not answered live**

*Q: I understand CLV is important but shouldn’t there be an emphasis on VLC - Value to Customers as the customers see it... corporations create the churn because one arm does not know what the other arm is doing. What is your POV?*
 A: We absolutely agree. CLV is one slice of understanding the customer. It sits within a broad ecosystem of analysis.

*Q: How does customer value decline over time? isn’t that by definition monotonically increasing over time? or is the plot showing profit rather than value? Is there an underlying cost that makes the curve eventually bend downwards? or is it going downwards because the plot is about PREDICTED value and that can change as a function of events happening?*
 A: Cumulatively, the value of the customer increases to the point where they stop engaging you. The CLV curve graph shown is more about the value of that customer at their point in the lifestage. As an example, if we have a declining customer but my spend is stable, their relative value will decline.

*Q: What is Databricks actively doing with Microsoft to close gaps so that Delta Lake is fully available throughout the data ecosystem?*
 A: Delta Lake has been open sourced for about a year now.  We are seeing fantastic adoption of the Delta Lake pattern and technology by customers, vendors and within the open source community at large.  While we can't speak to specific MSFT roadmaps, they are one of our closest partners and we work closely with them on many platform integrations. Delta Lake and the modern data architecture are quickly becoming the de facto approach for modern data & AI organizations.

*Q: Any reason why we chose t-SNE over other clustering approaches? Why is t-SNE well suited to this problem space?*
 A: t-SNE like PCA is a dimension reduction technique.  We're simply using it to help us visualize our data in advance of clustering.  For actual clustering, we'll use k-means a bit later.  There are certainly other techniques we could use but just think of t-SNE (and PCA) as a feature engineering step that enables us to get to visualizations.

*Q: Is there a reason why we are not going with 4 clusters as it yields the similar y-value compared to 8 clusters?*
 A: The choice of cluster counts (k) is a bit subjective.  While we use the elbow technique with a silhouette score, there's always a balancing of the metrics with what is practical/useful.  I chose 8 but you could choose another number if that worked better for you.

*Q: What about gap statistic of selecting # of clusters?*
 A: We use silhouette scores to look at inter-cluster and intra-cluster distances but you could use other metrics that focused on one aspect or the other.

*Q: How do you productionalize this model?*
 A: In the blogs, we show how you can transform the CLV model into a function which you could use within batch ETL, streaming jobs or interactive queries. There are other ways to deploy the model too but hopefully this will give you an idea of how to approach the task.

*Q: Have you found any relation between your RFM segments and Sales (Pareto Rule)?*
 A: The reason we use segmentation techniques such as CLV is to avoid generalized rules. Even if true in aggregate, a rule-of-thumb such as “20% of your customers generate 80% of your sales,” is very broad. Not every customer has the same potential and it's critical you balance your engagement around an understanding of that potential value in order to maintain profitability. An approach such as CLV enables us to be precise with how we engage customers and maximize the ROI of our marketing dollars.

*Q: In a non contractual and continuous setting as this use case, we could use the pareto/NBD model to calculate the retention/survival rate. is this something you are considering?*
 A: Absolutely.  In the blog, we consider both the Pareto/NBD and the BG/NBD for this scenario.  We focused on just one in the webinar for expediency.

*Q: In BTYD models, can you incorporate seasonality? Some retail businesses have very seasonal distributions in order count*
 A: Not really. Instead, you might want to predict future spend using a regression technique like we demonstrate in the final notebook.

*Q: Have you used Koalas for getting the aggregates by any chance?*
 A: We haven't but it would certainly be an option to help make some of this more distributed in places.

*Q: What was the reason to filter the distribution
 A: It was an arbitrary value that cuts off outliers that make the histogram harder to render.  We keep the outliers in the model but just blocked them for this one visualization. *

*Q: Can we save these model results using mlflow?*
 A: Absolutely.  This is demonstrated in the blogs.

*Q: How do we validate the CLV result?*
 A: You can use a cutoff date, or hold out, prior to the end of our dataset to train our model to a point and then forecast the remainder of the data.  In the blogs, we address this practice.

*Q: Is there a way to evaluate the accuracy of this model?*
 A: The simple way is to validate all model assumptions and then calculate an MSE against the holdout set as demonstrated in the blogs.

*Q: I have encountered cases where fitting the model fails because of the distribution of the data set? Any suggestions on how to overcome this?*
 A: I've encountered some problems with the latest build of lifetimes that sounds similar to what you are describing. Notice in the notebooks that we are explicitly using the last build of the library.

*Q: We are noticing marked change in shopper (in-store and online) buying behavior.. So how do you recommend in running these models given Per March 2020 (covid) and post March 2020 period?*
 A: This is a really good question and relevant across more than just CLV. We’ve seen a big inflection point that may change the fundamental relationship with customers. Buying patterns have fundamentally shifted in ways we don’t fully understand yet, and may not understand until quarantine and recession patterns stabilize. Key inflection points that fundamentally change the behavior of consumers happen every 7-10 years.

One approach to answering this would be to isolate customer engagement data for the period of quarantine and beyond. The reliability of this model will not be as strong as longer running models, but it would reflect more of the current volatility. Comparing this to analysis of data prior to CLV might generate unique insights on key shifts in consumer behavior.

If you have a long enough history, you could also look for other extreme events that resemble the current period. What happened in the recession of 2008? Have you had any other large scale disruptions to consumption such as natural disasters, where behavior was disrupted and returned in a different way.

*Q: Is it possible to integrate explanatory characteristics of the customer into the BTYD model?*
 A: In the BTYD models, the answer is no. In survival models which are frequently employed in contractual situations, the Cox Proportional Hazards model is a popular choice for explaining why customers leave.

*Q: In this use case you are calculating the CLV of existing customers, What about the new customers who joined recently?*
 A: We include them as well.  Remember, the models consider individual "signals" in the context of population patterns.  With this in mind, they can make some pretty sizeable leaps for new customers (such that they look more like the general population) until more information comes in which can be used to tailor the curves to the individual.

*Q: Can we think about adding segmentation feature from the previous notebook as feature engineering for CLV?*
 A: Absolutely.  If you know you have segments that behave differently, you can build separate models for each.

*Q: For CLV, I saw that you were using pandas. Do you have suggestions for when the data doesn’t fit in memory?*
 A: The dataset that's used to build the pandas DF is often very large.  For that, we use Spark.  But then the resulting dataset is one record per customer. For many organizations, we can squeeze that data set into a pandas DF so that we can use these standard libraries. Remember, we only have a couple numeric features per entry so the summary dataset is pretty light.  If it was just too big, we might then do a random sample of the larger dataset to keep things manageable.

*Q: Is RMSE the best way to score this model?*
 A: It is *a* way. :-) You can really use any error metric you feel works well for you.  MAE or MAPE might work well.

*Q: In the DL approach we are not estimating the retention part? We assume that all customers will remain active. right?*
 A: In the regression techniques, we aren't; really addressing retention which is why they aren't true CLV predictors.  These are commonly referred to as alternative means of calculating CLV but we need to recognize they actually do something different (and still potentially useful).

*Q: When using keras were you using a gpu enabled cluster?*
 A: We didn't use GPUs here but we could have.

*Q: Have you had any experience with exploring auto-regressive models for predicting CLV?*
 A: We haven't but it might be worth exploring. We suspect they might fall into the "spend prediction" camp like our regression models instead of being CLV estimators.

*Q: Do you have model interpretability built into the platform(eg: SHAP, Dalex)*
 A: Not on this model.  It certainly would be interesting to explore but we simply didn't get to it for this demonstration.

*Q: Bryan just mentioned a pattern for partitioning data and running models in parallel across those partitions, saying it’s often used in forecasting. Can you please share that in your written follow-up to questions?*
 A: Sure. Check out our blog on "[Databricks Fine Grained Forecasting](https://www.databricks.com/blog/2020/01/27/time-series-forecasting-prophet-spark.html)".  That provides the most direct explanation of the pattern.

*Q: How do you include shopping channels in this modeling process?*
 A: You could segment on channel.  That said, you might want to explore how customers who operate cross-channel would be handled.

*Q: Do you have any good references/sources for learning more about enhancing an organizations clustering practices?*
 A: The Springer Open book "[Market Segmentation Analysis](https://idp.springer.com/authorize?response_type=cookie&client_id=springerlink&redirect_uri=http%3A%2F%2Flink.springer.com%2Fbook%2F10.1007%2F978-981-10-8818-6)" is a good read.

*Q: The lifetimes package in python uses maximum likelihood estimate for estimating the best fit. Have you tried using a bayesian approach using pymc3?*
 A: We haven't but it might be interesting to explore if it gives faster or more accurate results.

*Q: Would it be safe to say that the generative models you demonstrated adequately attempt to capture the realizations of renewal processes that often explain customer behavior? For example a gamma process?*
 A: The models make tailored generalizations and in that regard balance a bit of the individual with the population.  Remember that we're not necessarily looking for a perfect prediction at an individual level but instead seeking probable guidance for future investments that average out to be correct.

*Q: Does keras take Spark dataframe?*
 A: Not that we’re aware of.  We believe you must pass it pandas/numpy.

[Watch now](https://pages.databricks.com/202005-US-EV-VIRTUALWORKSHOP-RETAIL-ME-OD-thank-you-webinar.html)
