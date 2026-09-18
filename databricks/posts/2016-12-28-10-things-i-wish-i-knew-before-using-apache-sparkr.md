# 10 Things I Wish I Knew Before Using Apache SparkR

- Source: https://www.databricks.com/blog/2016/12/28/10-things-i-wish-i-knew-before-using-apache-sparkr.html
- Published: 2016-12-28
- Authors: Neil Dewar
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

*This is a guest post from [Neil Dewar](https://www.linkedin.com/in/ndewar), a senior data science manager at a global asset management firm. In this blog, Neil shares lessons learned using R and Apache Spark.*

If you know how to use R and are learning Apache Spark, then this blog post and notebook contain key tips to smooth out your road ahead.

**[Try this notebook in Databricks](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/8599738367597028/1792412399382575/3601578643761083/latest.html?utm_campaign=Open%20Source&utm_source=Databricks%20Blog)**

As the notebook explains:

>  I’m an R user. Certainly not an object oriented programmer, and no experience of distributed computing. As my team starts to explore options for distributed processing of big data, I took the task to evaluate SparkR. After much exploration, I eventually figured out that what's missing is the contextual advice for people who already know R, to help them understand what's different about SparkR and how to adapt your thinking to make best use of it. That's the purpose of this blog and notebook -- to document the "aha!" moments in a journey from R to SparkR. I hope my hard-earned discovery helps you get there faster!

The notebook lists 10 key pieces of knowledge, with code snippets and explanations, tailored for R users. Here is the list in brief; check out the [notebook](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/8599738367597028/1792412399382575/3601578643761083/latest.html?utm_campaign=Open%20Source&utm_source=Databricks%20Blog) to learn more!

[btn href="https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/8599738367597028/1792412399382575/3601578643761083/latest.html?utm_campaign=Open%20Source&utm_source=Databricks%20Blog" target="_blank"]View this Notebook[/btn]

 

1. **Apache Spark Building Blocks**. A high-level overview of Spark describes what is available for the R user.
2. **SparkContext, SQLContext, and SparkSession**. In Spark 1.x, SparkContext and SQLContext let you access Spark. In Spark 2.x, SparkSession becomes the primary method.
3. **A DataFrame or a data.frame?** Spark’s distributed DataFrame is different from R’s local data.frame. Knowing the differences lets you avoid simple mistakes.
4. **Distributed Processing 101**. Understanding the mechanics of Big Data processing helps you write efficient code—and not blow up your cluster’s master node.
5. **Function Masking**. Like all R libraries, SparkR masks some functions.
6. **Specifying Rows**. With Big Data and Spark, you generally select rows in DataFrames differently than in local R data.frames.
7. **Sampling**. Sample data in the right way, and use it as a tool for converting between big and small data.
8. **Machine Learning**. SparkR has a growing library of distributed ML algorithms.
9. **Visualization**.It can be hard to visualize big data, but there are tricks and tools which help.
10. **Understanding Error Messages**. For R users, Spark error messages can be daunting. Knowing how to parse them helps you find the relevant parts.
