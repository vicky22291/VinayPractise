# Accelerating Machine Learning on Databricks: On-Demand Webinar and FAQ Now Available!

- Source: https://www.databricks.com/blog/2019/02/04/accelerating-machine-learning.html
- Published: 2019-02-04
- Authors: Hossein Falaki, Adam Conway
- Categories: platform, product, solutions, engineering, data-science-machine-learning, company
- Images: 2 total, 0 extracted as architecture

*Free Edition has replaced Community Edition, offering enhanced features at no cost. Start using *[*Free Edition *](https://login.databricks.com/?intent=SIGN_UP&amp;signup_experience_step=EXPRESS&amp;provider=DB_FREE_TIER&amp;dbx_source=www)*today.*
 

[Try this notebook in Databricks](https://pages.databricks.com/rs/094-YMS-629/images/Keras%2BTensorFlow.html?mkt_tok=eyJpIjoiWlRrMk9XSm1NakUyWkRsbCIsInQiOiJFZURSRllpOFwvYjdLRnZGVEZiTnlaSkdVSWVyMmxhUktBM0RERUhYSEFXcHpmV1N3aXZSZlVoNEwzZnNGS1NlaEZXQUNrXC9velpEWXhhVmJYVkN6Rk1BPT0ifQ%3D%3D)

On January 15th, we hosted a live webinar—[Accelerating Machine Learning on Databricks](https://pages.databricks.com/201812-US-WB-AcceleratingML-Databricks.html)—with Adam Conway, VP of Product Management, Machine Learning, at Databricks and Hossein Falaki, Software Development Engineer and Data Scientist at Databricks.

In this webinar, we covered some of the latest innovations brought into the Databricks Unified Analytics Platform for Machine Learning. In particular, we talked about how to:

- Get started quickly using the Databricks Runtime for Machine Learning, that provides a pre-configured Databricks clusters including the most popular ML frameworks and libraries, Conda support, performance optimizations, and more.
- Track, tune, and manage models, from experimentation to production, with MLflow, an open-source framework for the end-to-end Machine Learning lifecycle that allows data scientists to track experiments, share and reuse projects, and deploy models quickly, locally or in the cloud.
- Scale up deep learning training workloads from a single machine to large clusters for the most demanding applications using the new HorovodRunner.

We demonstrated some of these concepts using Keras (TensorFlow backend) and PyTorch on Databricks, and here is a link to our notebook to get started today:

- [Use Keras with TensorFlow on a single node on Databricks](https://pages.databricks.com/rs/094-YMS-629/images/Keras%2BTensorFlow.html?mkt_tok=eyJpIjoiWlRrMk9XSm1NakUyWkRsbCIsInQiOiJFZURSRllpOFwvYjdLRnZGVEZiTnlaSkdVSWVyMmxhUktBM0RERUhYSEFXcHpmV1N3aXZSZlVoNEwzZnNGS1NlaEZXQUNrXC9velpEWXhhVmJYVkN6Rk1BPT0ifQ%3D%3D)
- [From single node to distributed training with PyTorch on Databricks](https://pages.databricks.com/rs/094-YMS-629/images/PyTorch.html?mkt_tok=eyJpIjoiWlRrMk9XSm1NakUyWkRsbCIsInQiOiJFZURSRllpOFwvYjdLRnZGVEZiTnlaSkdVSWVyMmxhUktBM0RERUhYSEFXcHpmV1N3aXZSZlVoNEwzZnNGS1NlaEZXQUNrXC9velpEWXhhVmJYVkN6Rk1BPT0ifQ%3D%3D)

If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

You can now register to our next webinar—[Simple Steps to Distributed Deep Learning](https://pages.databricks.com/201901-StepsToDeepLearning.html)—with Yifan Cao, Senior Product Manager at Databricks.

Toward the end, we held a Q&A, and below are the questions and their answers, grouped by topics.

### Fundamentals

**Q: How can I try Databricks?**

You can try Databricks Community Edition or Standard 14-days Trial at [https://www.databricks.com/try-databricks](https://www.databricks.com/try-databricks).

**Q: Are the features for Azure Databricks the same as on AWS?**

Yes, part of our strategy is to provide a cross-cloud experience, and we are committed to product parity between Azure Databricks and running Databricks on AWS.

**Q: Will the Databricks Runtime for Machine Learning be available for free?**

Yes, you can sign-up to our free 14-days Standard trial or our Community Edition at [https://www.databricks.com/try-databricks](https://www.databricks.com/try-databricks) to get started.

**Q: What is the cost of running the Databricks clusters? Do customers have to be on a payment plan with Amazon to use their clusters on EC2 and other services or do they pay to Databricks based on the usage?**

Please visit our [pricing page](https://www.databricks.com/product/pricing) for more information on our different plans, for AWS and Azure. Our licensing model is based on actual usage.

**Q: I would really like to see more examples of how you (and other customers) are organizing continuous ETL and data collection operations in Databricks, since this is always the most difficult part of productionizing data science operations.**

[Here](https://www.databricks.com/session/keynote-from-apple) is a recent talk from the Spark+AI Summit, where Dominique Brezinski (Apple) and Michael Armbrust (Databricks) give a walkthrough of a streaming ETL scenario using Databricks Delta with demos. Don't miss our [YouTube playlist](https://www.youtube.com/watch?v=9JVNxoyLI7Y&list=PLTPXxbhUt-YXpryFaZkCr72JxDYP-XEcQ) for more success stories!

### Apache SparkTM

**Q: For those who might be interested in learning more about the Spark source code. Besides going over the GitHub project, what would you recommend to get started learning?**

For data scientists looking to apply Apache Spark™’s advanced analytics techniques and deep learning models at scale, we recommend [The Data Scientist's Guide to Apache SparkTM](https://www.databricks.com/p/ebook/the-data-scientists-guide-to-apache-spark). [Spark: The Definitive Guide](https://pages.databricks.com/definitive-guide-spark.html) is also a good resource to dive deeper. After learning about the API the best places to start learning are source code and developer mailing lists.

**Q: In respect to the Spark and big data architecture, for the data that doesn't fit in the memory of a single machine, and if we want to use spark to reduce training time -- in this scenario does the training happen for the entire dataset across multiple machines (across clusters) - Master & Worker nodes?**

Yes, by partitioning your data you can make sure all training examples get used for the training of DNN. See this paper for more details: [https://arxiv.org/abs/1802.05799](https://arxiv.org/abs/1802.05799)

**Q: If yes, does the Spark architecture consider the RAMs across multiple machines as part of a single memory and multiple CPU's/cores across clusters similar to CPU/cores in a single machine?**

The HorovodRunner examples that was demoed during the webinar is using a new scheduling paradigm recently added to Spark, called BarrierMode. For more details, please tune into our next webinar on [Simple Steps to Distributed Deep Learning](https://pages.databricks.com/201901-StepsToDeepLearning.html?utm_source=KDNuggets&utm_medium=Email&utm_campaign=701610000008q1LAAQ).

**Q: Is there any distinct advantage of using Scala instead of PySpark, as there are companies that ask for Data Scientists/ML Engineers with Scala experience ?**

We find customers and strong usage on both Scala and Python. Each language has its own advantages and community.

### Data Preparation

**Q: Since we have seen that Data Scientists seem to spend a large amount of their time cleaning poor quality data, what is used to 'prepare quality data' - Is this an integrated tool on the platform?**

Databricks provides built-in connectors to virtually any data sources, and the ability for data engineers to run ETL processes in Java, Scala, SQL, R, or Python using shared workspaces, notebooks, APIs, production jobs and workflows. Data scientist can easily perform [data exploration](https://youtu.be/mPTzJDs0EkI) with simple access to their data, shared notebooks, and built-in [visualization](https://youtu.be/YMrFnqSGD2s) tools. Finally, with [Databricks Delta](https://www.databricks.com/product/delta-lake-on-databricks), data teams can now build the next gen data pipelines, unify batch and streaming analytics at massive scale and draw on capabilities such as ACID transactions, efficient upserts (for addressing late arriving and changing records), schema enforcement and version management (for rollbacks) to ensure they are working with quality data.

**Q: Can Databricks read data from external storage, such as blob storage?**

Yes, Spark is built to read data from external distributed storage systems, most notably blob storage systems such as S3 and Azure Blob Storage.

**Q: Does Databricks have any graphical interface (drag and drop) for building the data pipelines / ETL workflows for data extraction?**

Databricks has an integration with [Talend](https://www.databricks.com/partners/talend) for users requiring drag and drop capabilities. The Integration between Talend Cloud and Databricks’ Unified Analytics Platform enables data engineers to perform data processing at large-scale using the powerful Apache Spark platform. Through this integration, users can access the scale and cloud benefits through a drag and drop interface, instead of manually coding data engineering jobs. The Talend Cloud integration is supported on both Microsoft Azure and on AWS.

**Q: How can I use the PIVOT function in SQL notebook?**

You can execute any SQL query in Databricks notebooks either using %sql or passing the query to the sql() command.

**Q: Is it possible to create a data pipeline with SQL or it is only to query the data? eventually, are this SQL pipelines optimized?**

Yes, users can create data pipelines with just SQL on Databricks.

### Model Building

**Q: Any idea about what proportion of the code is being written in R compared to Python on Databricks?**

A large fraction of our customers use R to program Spark Jobs.

**Q: Does MLflow document the data set that is being fed to the ML model to create the scoring parameters?**

Yes, MLflow helps track both small and large data that was used to train models. Small data can be captured in a versioned way by MLflow's MLProject abstraction which supports Git for file versioning. Large data can be captured by storing the name of the data file (e.g. a parquet file) as an MLflow Run parameter or tag. Additionally, since Databricks Delta Time Travel (in Private Preview now) provides the ability to efficiently save snapshots of big data, MLflow can also save a link to Delta snapshot of large data. This integration means that an ML developer can capture data lineage as part of their model training even for large data!

**Q: Is there an integration between Github/Bitbucket and Databricks workspace? Can I clone my Git repository into Databricks?**

Yes, version control for notebooks can be setup using GitHub. Read more about this in our [documentation](https://docs.databricks.com/notebooks/github-version-control.html). While you can currently git clone a repository onto a Databricks driver node via a notebook or shell script, Databricks does not currently provide access to complete git repositories in the Databricks Workspace UI. However, that feature is on our roadmap for 2019.

**Q: Is MLflow integrated into Databricks?**

It is easy to use Open Source MLflow from inside of Databricks notebooks and clusters. We have also released a [Private Preview](https://docs.databricks.com/applications/mlflow/index.html) of a hosted MLflow tracking service including integrations with Databricks Notebooks, Databricks File System, etc. Additionally, we have released support for [MLflow Remote Execution on Databricks](https://mlflow.org/docs/latest/projects.html#remote-execution-on-databricks). Signed up at [https://www.databricks.com/product/managed-mlflow](https://www.databricks.com/product/managed-mlflow) for future updates!

**Q: The MLflow UI is not compatible with Windows as of this moment, is there an estimated date for MLflow to become fully compatible with Windows?**

Windows is not fully supported or tested currently but we welcome open source collaborations and contributions for it!

**Q: Can you send SparkDataFrames straight to Keras on Horovod?**

We recommend spark-tensorflow-connector for saving SparkDataFrame to TFRecord files. Another tool to do this is the Petastorm package. You can find more details about it [here](https://github.com/uber/petastorm).

**Q: Are SparkDataFrames being fed into the HorvodRunner function?**

With HorovodRunner we recommend you partition and save your SparkDataFrame on distributed storage and then use an DL capable FUSE client (goofys on AWS, orblobfuse one Azure) to load data into each worker for deep learning training.

**Q: How do you parallelize the optimizer run in your demo?**

[Horovod](https://github.com/horovod/horovod) provides easy to use facilities to convert your single-node optimizer to a distributed optimizer. We recommend you tune in for our follow-up webinar [Simple Steps to Distributed Deep Learning](https://pages.databricks.com/201901-StepsToDeepLearning.html?utm_source=KDNuggets&utm_medium=Email&utm_campaign=701610000008q1LAAQ) for more details.

**Q: How can we install packages that are not yet supported in the Databricks Runtime for Machine Learning? **

Additional libraries can be installed by following the steps in our [documentation](https://docs.databricks.com/libraries/index.html#id1).

**Q: What if the end product the stakeholder needs is a UI or a dynamic dashboard, how do we do that with Databricks?**

Databricks provides simple ways for data scientists to create dynamic dashboards that stay up to date. See it in action [here](https://vimeo.com/165348629).

### Productionizing ML

**Q: Are there any webinars on Productionizing using Databricks?**

There are a number of great [Databricks webinars](https://www.databricks.com/resources?_sft_resource_type=webinars) available; ones that focus on Productionizing Machine Learning include (but are not limited to) [Productionizing Apache Spark™ MLlib Models for Real-time Prediction Serving](https://pages.databricks.com/Reg-Real-time-Prediction-Serving.html)

**Q: How can we generate API's of the machine learning models we build on Databricks?**

The MLflow Model component provides a flexible mechanism to deploy models to popular model serving systems including Databricks (for batch scoring with Spark), Amazon SageMaker, and Azure Machine Learning. MLflow also supports exporting Spark models as self-contained applications via MLeap for low latency serving. Finally, the `mlflow serve` command spins up a flask web server which presents a low latency RESTful API for inference.
