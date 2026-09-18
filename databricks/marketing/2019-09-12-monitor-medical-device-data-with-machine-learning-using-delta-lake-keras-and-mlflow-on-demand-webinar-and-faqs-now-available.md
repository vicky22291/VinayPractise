# Monitor Medical Device Data with Machine Learning using Delta Lake, Keras and MLflow: On-Demand Webinar and FAQs now available!

- Source: https://www.databricks.com/blog/2019/09/12/monitor-medical-device-data-with-machine-learning-using-delta-lake-keras-and-mlflow-on-demand-webinar-and-faqs-now-available.html
- Published: 2019-09-12
- Authors: Michael Ortega, Frank Austin Nothaft
- Categories: data-streaming, company, events
- Images: 1 total, 0 extracted as architecture

On August 20th, our team hosted a live webinar—[Automated Monitoring of Medical Device Data with Data Science](https://pages.databricks.com/201908-WB-Automated-Monitoring-of-Medical-Device-Data_Reg.html)—with Frank Austin Nothaft, PhD, Technical Director of Healthcare and Life Sciences, and Michael Ortega, Senior Industry and Solutions Marketing Manager.

By applying machine learning to medical device data, healthcare organizations can automate patient monitoring, reduce repair costs with preventative maintenance, and gather new insights on patient health outside of a clinical setting. However, most healthcare organizations attempting to build ML pipelines on these large datasets face numerous challenges such as scaling legacy infrastructure, building reliable streaming pipelines and developing models efficiently. In this webinar, we shared how to overcome these challenges with Databricks and popular open-source technologies including a live demo of a deep learning model on streaming medical device data.

[Watch the replay](https://pages.databricks.com/201908-WB-Automated-Monitoring-of-Medical-Device-Data_Reg.html) to learn how to:

- Build a streaming pipeline for EKG data using Structured Streaming and Delta Lake
- Improve data consistency guarantees while eliminating data engineering bottlenecks
- Interactively query streaming EKG data in real-time
- Rapidly train a deep learning model over terabytes of waveforms
- Track and manage the entire model lifecycle in MLFlow, allowing analysis traceability

We demonstrated these concepts using these notebooks and tutorials:

- Notebook: [Download and preprocess data](https://www.databricks.com/notebooks/iot-medical/stage-date.htm)
- Notebook: [Train and tune a neural network](https://www.databricks.com/notebooks/iot-medical/deep-learning.htm)
- Notebook: [Create a streaming dataset](https://www.databricks.com/notebooks/iot-medical/stream-data.htm)
- Notebook: [Run inference on continuously arriving data](https://www.databricks.com/notebooks/iot-medical/read-stream.htm)

If you’d like free access to the [Databricks Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse) and try our notebooks on it, you can access a free trial ([AWS](https://www.databricks.com/try-databricks) | [Azure](https://www.databricks.com/product/azure)).

Toward the end, we held a Q&A and below are the questions and answers.

**Q: How exactly does WFDB help in this use case? Is the WFDB data stored within Databricks or on a different server?**

[WFDB](https://wfdb.readthedocs.io/en/latest/) is a standard file format for exchanging biomedical waveform data. In this example, WFDB is the interchange file format that the EKG data arrived in, and the data is stored in the [Databricks File System (DBFS)](https://docs.databricks.com/data/databricks-file-system.html). DBFS is a thin layer to manage metadata about data stored in the customers’ [Azure Blob Storage on Azure Databricks](https://docs.microsoft.com/en-us/azure/databricks/data/databricks-file-system#databricks-file-system) or [S3 on Databricks on AWS](https://docs.databricks.com/data/databricks-file-system.html). In the workflow we demonstrated, we start by transforming the data from WFDB into a Delta Lake table.

**Q: How do you determine the window size? And does the size affect performance?**

We based our choice of the window size of 2,048 samples off of a recent blog analyzing this dataset. Intuitively, 2,048 samples is approximately 2 heartbeats at the sampling rate used in this dataset.

**Q: Was any signal processing done on the data before ingestion?**

In this example, we used data collected from the open-access [PTB Diagnostic ECG database](https://physionet.org/content/ptbdb/1.0.0/). Limited signal processing was performed when the data was acquired. We did not perform additional signal processing after downloading the data.

**Q: Does Databricks provide auto-keras support?**

[auto-keras](https://autokeras.com/) is a python library for automating neural network model architecture optimization using the [Keras](https://keras.io/) deep learning library, which is preinstalled into the Databricks [ML Runtime](https://www.databricks.com/product/machine-learning-runtime)  ([AWS](https://docs.databricks.com/applications/machine-learning/train-model/tensorflow.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/tensorflow)). auto-keras can be installed using Databricks library management features ([AWS](https://docs.databricks.com/libraries/index.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/libraries/)) and used on a Databricks cluster. Beyond auto-keras, we support a wide range of AutoML capabilities, which we covered in a recent [blog](https://www.databricks.com/blog/2019/08/20/automl-on-databricks-augmenting-data-science-from-data-prep-to-operationalization.html).

**Q: How do you monitor the clusters and where can I see the metrics for each job?**

The Spark UI is displayed both inline within notebooks when a Spark job is running, and can be accessed on the Databricks cluster UI ([AWS](https://docs.databricks.com/clusters/clusters-manage.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/clusters/clusters-manage#clusters-sparkui)). Additionally, we make available a large range of metrics, such as the metrics output by Ganglia ([AWS](https://docs.databricks.com/clusters/configure.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/clusters/configure#cluster-performance)).

**NEXT STEPS**

- Watch the [webinar replay](https://pages.databricks.com/201908-WB-Automated-Monitoring-of-Medical-Device-Data_Reg.html) to learn more
- Start exploring our deep learning pipeline for medical device data with notebooks from our webinar:
  - [Download and preprocess data](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/1839019694868427/3745355415939796/1720491171398644/latest.html)
  - [Train and tune a neural network](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/1839019694868427/3745355415939821/1720491171398644/latest.html)
  - [Create a streaming dataset](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/1839019694868427/3745355415939817/1720491171398644/latest.html)
  - [Run inference on continuously arriving data](https://databricks-prod-cloudfront.cloud.databricks.com/public/4027ec902e239c93eaaa8714f173bcfc/1839019694868427/3745355415939852/1720491171398644/latest.html)
- Get started with a [free trial](https://www.databricks.com/try-databricks)of Databricks
