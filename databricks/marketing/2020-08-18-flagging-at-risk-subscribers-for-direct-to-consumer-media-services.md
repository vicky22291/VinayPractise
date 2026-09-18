# Flagging at-risk subscribers for direct-to-consumer media services

- Source: https://www.databricks.com/blog/2020/08/18/flagging-at-risk-subscribers-for-direct-to-consumer-media-services.html
- Published: 2020-08-18
- Authors: Hector Leano, Steve Sobel
- Categories: engineering, data-engineering, data-science-machine-learning, open-source
- Images: 0 total, 0 extracted as architecture

>  “The biggest problem for streaming services is not so much getting new members, it's holding them. It's the churn factor.” Tom Rogers, Executive Chairman at WinView, Inc and former NBC Cable President [on CNBC](https://twitter.com/cnbc/status/1283865752181846016?s=12)

As more content owners monetize their content libraries through direct-to-consumer (D2C) streaming services, their biggest challenge isn’t getting new customers in the door: With no upfront costs like truck roll or set-top boxes, digital services can easily generate free trials to their apps or channel (if selling through a channel platform like Prime Video Channels or Roku Channels).

But this ease of sampling is a double edged sword. With no 2-year commitments locking customers in, subscribers can cancel anytime with a few clicks, whether before rolling-to-pay, or when their sports or show season ends. Driving a relevant, 1:1 experience with consumers across all channels and at all times is now table stakes for many in the direct-to-consumer space as they look to reduce churn and win the war for attention for their subscription services.

But rather than broad save offers, what if you could segment subscribers by behavior so that you proactively send at risk customers an  offer before they go to cancel? What if that offer was personalized to their estimated [customer lifetime value](https://www.databricks.com/blog/2020/06/03/customer-lifetime-value-part-1-estimating-customer-lifetimes.html) to ensure positive ROI? More broadly, what are the insights  customer behavior can reveal about your product and content in order to improve the customer experience and increase value subscribers get every month? Databricks customer Showtime, for example, [analyzed their D2C data](https://www.databricks.com/customers/showtime) to revamp their production schedule to ensure there was no off-season to their new release schedule in order to keep subscribers year round to maximize their customer lifetime value.

## Introducing the Churn Prediction Modeling Solution Accelerator

Based on best practices of subscription services across industries ranging from digital media to retail to financial services, we have released [a solution accelerator allowing enterprises to better understand not only when but also why customers leave subscription services](https://www.databricks.com/blog/2020/07/15/analyzing-customer-attrition-in-subscription-models.html). In this blog we walk through the general consumer lifecycle issues facing subscription-based businesses, and provide pre-built notebooks and sample data to jumpstart data science teams in media companies tasked with reducing subscriber churn rates. While the sample customer data looks at signup source and offer types, you can customize the machine learning models and analytics tools to your own unique viewers so you can analyze churn risk based on:

- when and how often they access subscription content
- specific content or kinds of content consumed
- quality of service events
- type of devices used to access content
- depth of engagement (e.g., do they watch full screen, how much do they watch)
- referral source performance
- and just about any other user behavior data tagged in your data lake

[Link to the churn prediction solution accelerator](https://www.databricks.com/blog/2020/07/15/analyzing-customer-attrition-in-subscription-models.html)

You can also watch our [on-demand workshop](https://www.databricks.com/blog/2020/08/07/on-demand-virtual-workshop-predicting-churn-to-improve-customer-retention.html)where we walk through the customer churn analysis  solution accelerator.
