# On Demand Virtual Workshop: Predicting Churn to Improve Customer Retention

- Source: https://www.databricks.com/blog/2020/08/07/on-demand-virtual-workshop-predicting-churn-to-improve-customer-retention.html
- Published: 2020-08-07
- Authors: Hector Leano, Bryan Smith, Rob Saker, Steve Sobel
- Categories: engineering, data-engineering, data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

The proliferation of subscription models has increased across industries: from direct-to-consumer brands for shaving supplies and prepared meals to streaming media services, at-home fitness, auto insurance and even automobiles themselves. Consumers are flocking to these new offerings while moving away from long-term contracts, which for subscription-based businesses means they have to prove their value to their customers every month. From source of acquisition to devices used to detect frequency and type of interaction, which customer events signal an increased likelihood to churn versus renew in the near future? How do you decide the proper investment to save an at-risk subscriber from the risk of churning?

In short, how do you use customer behavior and interactions to predict churn and save your most valuable customers?

In this on-demand virtual workshop, learn how unified data analytics can bring data science, business analytics and engineering together to increase the precision in customer lifetime value and churn prediction models across industries like retail, media, telco, insurance, retail financial services, and others. Hear from innovative meat delivery subscription box ButcherBox around how this rapidly growing, digital-native brand is using customer data, such as user interactions and other data points, to better predict existing customer lifetime value and feed downstream supply chain analyses.

This virtual workshop will give you the opportunity to learn about:

- Using Survival Analysis to understand when and possibly why customers abandon subscription services
- Predicting customer churn at key stages in the subscription lifecycle

## Relevant blog posts

[Analyzing Customer Attrition in Subscription Models](https://www.databricks.com/blog/2020/07/15/analyzing-customer-attrition-in-subscription-models.html)

## Q&A 

*Q: How frequently do you update the models to evaluate or improve the models?*
 A. There is no predefined standard period for updating or rerunning the churn prediction models. The best advice we can offer is to run it as frequently as your business makes decisions about churn. Are you dealing with churn each week because you have weekly changes in payment or offer options? In that scenario, you would run this weekly.

*Q: How many of these survival models would you include multiple predictors?*
 A. All of these models include multiple predictors. Consider all the potential predictors that might offer value but be sure that predictors adhere to the Cox PH assumption of not being time-variant.  Also, carefully consider removing variables with strong collinearity as these will likely interfere with model calculations. Finally, use the statistical tests included in the notebooks to identify and remove any predictors that contribute no statistical value above the baseline.
*Q: Could you elaborate on data transformation challenges for survival models. If you have large datasets, you will find a challenge in creating the Nevada chart type of data, though it depends what model you build. Would need a little more details on data transformation challenges*
 A. The survival analysis routines expect the source data to be in very specific formats.  In the case of the Cox PH model, it is expected that each subscription has one record which includes the subscription duration (in days in our scenario) along with the status of the subscription at the end of that duration. Predictive features then follow with categorical features one-hot transformed.

*Q: What are some difficulties you might expect to encounter when doing survival analysis on high frequency consumers (grocery, frequency is usually a few days or a week)?*
 A. Data engineering is absolutely the biggest challenge. Remember that you want to summarize all of those interactions down to a single record for analysis. That is a ton of data crunching and most systems can’t handle that. Adding to that complexity is that you’ll want to iterate on which features to extract for that single record.

*Q: What is the difference between survival rate and **retention rate**? or are we just using it interchangeably?*
 A. For the sake of this webinar and accompanying blog posts we use customer retention and customer survival rate interchangeably :-)

*Q: How do you handle the number of observations? For example, day-30 signups might be 10x bigger than day-10 signups.*
 A. By stratifying these, we can calculate statistics for each of those stratas.  In the case of the Kaplan-Meier curves, we actually have 95% confidence intervals for each which will depend on the number of observations.  You can see this very clearly in the prior subscriptions K-M curve.
 HowQ: can we use these survival model output to calculate Customer Lifetime values?
 A. Once we have a predictive model, we can then identify the end dates of the periods for which we are calculating CLV and retrieve a retention ratio/survival probability. For example, if I were to calculate a three-year CLV on an annual basis, I would grab the retention rate at the 365, 730 and 1095 day points.

*Q: How long did it take for implementation of this approach (the whole architecture)? *
 A. This really depends on your organization. If you have the data available you could deploy our notebook and connect your data in a couple of days. We commonly do POCs with customers on this code and it never takes longer than 2 weeks.

*Q: Has your model considered the seasonality factor?*
 A.   There are machine learning models for CLV which consider seasonality but in general I’d very carefully examine what I’m trying to predict when seasonality becomes a consideration.  Often, when we start looking at seasonality we’re attempting to make a more precise revenue projection than what CLV is oriented around.

## Notebooks from the webinar

- [Survival Analysis 01: Data Prep](https://www.databricks.com/notebooks/survival_analysis/survival_analysis_01_data_prep.html)
- [Survival Analysis 02: Exploratory Analysis](https://www.databricks.com/notebooks/survival_analysis/survival_analysis_02_exploratory_analysis.html)
- [Survival Analysis 03: Modeling Hazards](https://www.databricks.com/notebooks/survival_analysis/survival_analysis_03_modeling_hazards.html)
- [Survival Analysis 04: Operationalization](https://www.databricks.com/notebooks/survival_analysis/survival_analysis_04_operationalization.html)

## Watch Webinar
