# Simple Steps to Distributed Deep Learning: On-Demand Webinar and FAQ Now Available!

- Source: https://www.databricks.com/blog/2019/03/11/simple-steps-to-distributed-deep-learning-on-demand-webinar-and-faq-now-available.html
- Published: 2019-03-11
- Authors: Yifan Cao, Bagrat Amirbekian, Cyrielle Simeone
- Categories: platform, product, data-science-machine-learning
- Images: 1 total, 0 extracted as architecture

[Try this notebook in Databricks](https://pages.databricks.com/rs/094-YMS-629/images/final%20-%20simple%20steps%20to%20distributed%20deep%20learning.html)

On February 12th, we hosted a live webinar—[Simple Steps to Distributed Deep Learning on Databricks](https://pages.databricks.com/201901-StepsToDeepLearning.html)—with Yifan Cao, Senior Product Manager, Machine Learning and Bago Amirbekian, Machine Learning Software engineer at Databricks.

In this webinar, we covered some of the latest innovations brought into the Databricks Unified Analytics Platform for Machine Learning, specifically distributed deep learning.

In particular, we talked about:

- How distributed deep learning works and existing frameworks, specifically Horovod.
- How Databricks is making it easy for data scientists to migrate their single-machine workloads to distributed workloads, at all stages of a deep learning project.
- A demo of distributed deep learning training using some of our latest capabilities, including Databricks Runtime for Machine Learning and HorovodRunner.

We demonstrated some of these concepts from data prep to model building and inference, using Keras (TensorFlow backend), Horovod, TensorBoard, and PySpark on Databricks, and here is a link to our notebook to get started today:

- [Simple Steps to Distributed Deep Learning Demo Notebook](https://pages.databricks.com/rs/094-YMS-629/images/final%20-%20simple%20steps%20to%20distributed%20deep%20learning.html)

If you’d like free access [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a [free trial here](https://www.databricks.com/try-databricks).

Toward the end, we held a Q&A, and below are the questions and their answers.

**Q: Based on your experience of working with your customers, what do you see as the biggest challenges to adopting distributed DL?**

We see two types of challenges based on our experiences: organizational and technical.

Organizationally, the majority of our enterprise customers are early in adopting Deep Learning. These early adopters focus on exploring use cases and proving the business value with sample datasets. For these customers who have proven business value, in almost every single case, they are looking for a scalable and easy-to-use solution for distributed Deep Learning. We expect increasingly more customers looking for distributed DL solutions, because a considerable number of enterprise customers started their Deep Learning initiatives within the last 1-2 years.

On the technical front, we generally see three types of questions for distributed DL. First, many customers ask about data I/O during training. We recommend our customers to preprocess raw data and save to a persistent storage, and then use a high-performance FUSE mount (see our published solutions) to access data during training. Second, many distributed DL solutions tend to be low-level and not scalable. We built HorovodRunner, focusing on ease-of-use and scalability while achieving performance parity with single node DL training. Finally, tuning performance becomes ever more important, and the tradeoffs are different in a distributed context. For instance, an user might prefer a smaller network with less regularization than a big network with high regularization for performance. We are exploring solutions to make it easy & efficient for our users to tune distributed DL models.

**Q: Regarding to Tensorflow/Keras access Blob/S3 via mount point: would it be possible to ingest data without mounting? For example, if my data is not inside a single Azure container, it would be a challenging to mount blobs/containers.**

Yes, it is possible to read data directly from Blob/S3 without mounting. However, the read & write throughput would not be nearly as good as a mount that is optimized for high-performance data access, which is important for distributed DL training.

**Q: How do you chose the parameters for models, like steps, epochs, etc?**

Parameters such as model architecture, batch size, and learning rate tend to have the important impact on DL training model performance. Epochs usually don’t matter as much, as long as the users run enough epochs and are satisfied with the model performance.

You can watch our [Deep Learning Fundamentals Series](https://www.databricks.com/tensorflow/deep-learning) to learn more.

**Q: What is the size limit for DBFS?**

DBFS is an optimized interface to S3. So, it inherits the same limits as you would using S3. Per S3 [FAQ](https://aws.amazon.com/s3/faqs/), the total number of objects that can be stored is unlimited, and individual objects can range from 0 to 5TB in size.

**Q: How much efficiency loss is there due to parallelization? (How much more CPU time needed to converge?)**

Scaling efficiency depends on several factors, including model architecture and parameters. Efficiency loss is due to communication overhead across the distributed network during model training. In our tests of scaling efficiency using HorovodRunner, the average scaling efficiency is 70-80%.

**Q: How to load a Keras deep learning model on Apache Spark cluster workers rather than drivers, and how to score that model using the workers?**

We recommend use MLflow to load and deploy models. You can find details [here](https://docs.databricks.com/applications/mlflow/models.html).

**Q: What does MPI command mean?**

[MPI](https://hpc-tutorials.llnl.gov/mpi/) is a standard interface for communication between distributed workers. Implementations of MPI have long been used in high-performance computing contexts. The open-sourced Horovod is implemented using MPIs. One key benefit of HorovodRunner is that it abstracts the execution of complicated MPI commands. With HorovodRunner, users don’t need to know MPIs and can still distribute DL training.
