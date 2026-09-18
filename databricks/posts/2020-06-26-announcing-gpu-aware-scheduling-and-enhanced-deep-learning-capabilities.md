# Announcing GPU-aware scheduling and enhanced deep learning capabilities

- Source: https://www.databricks.com/blog/2020/06/26/announcing-gpu-aware-scheduling-and-enhanced-deep-learning-capabilities.html
- Published: 2020-06-26
- Authors: Lu Wang
- Categories: engineering, data-science-machine-learning, open-source
- Images: 0 total, 0 extracted as architecture

> Databricks is pleased to announce the release of Databricks Runtime 7.0 for Machine Learning (Runtime 7.0 ML) which provides preconfigured GPU-aware scheduling and adds enhanced deep learning capabilities for training and inference workloads.

## Preconfigured GPU-aware scheduling

Project Hydrogen is a major Apache Spark™ initiative to bring state-of-the-art artificial intelligence (AI) and Big Data solutions together. Its last major project, accelerator-aware scheduling, is made available in Apache Spark 3.0 by a collaboration among developers at Databricks, NVIDIA, and other community members.

In Runtime 7.0 ML, Databricks preconfigures GPU-aware scheduling for you on GPU clusters. The default configuration uses one GPU per task, which is ideal for distributed inference workloads and distributed training if you use all GPU nodes. If you want to do distributed training on a subset of nodes, Databricks recommends setting spark.task.resource.gpu.amount to the number of GPUs per worker node in the cluster Spark configuration, to help reduce communication overhead during distributed training.

For PySpark tasks, Databricks automatically remaps assigned GPU(s) to indices 0, 1, …. Under the default configuration that uses one GPU per task, your code can simply use the default GPU without checking which GPU is assigned to the task. This is ideal for distributed inference. See our model inference examples ([AWS](https://docs.databricks.com/applications/machine-learning/model-inference/dl-model-inference.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/model-inference/dl-model-inference)).

For the distributed training tasks with HorovodRunner ([AWS](https://docs.databricks.com/applications/machine-learning/train-model/distributed-training/horovod-runner.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/train-model/distributed-training/horovod-runner)), users do not need to do any modifications when migrating their training code from older versions to the new release.

## Simplified data conversion to Deep Learning frameworks

Databricks Runtime 7.0 ML includes Petastorm 0.9.2 to simplify data conversion from Spark DataFrame to TensorFlow and PyTorch. Databricks contributed a new Spark Dataset Converter API to Petastorm to convert a Spark DataFrame to a TensorFlow Dataset or a PyTorch DataLoader. For more details, check out [the blog post for Petastorm in Databricks](https://www.databricks.com/blog/2020/06/16/simplify-data-conversion-from-apache-spark-to-tensorflow-and-pytorch.html) and our user guide ([AWS](https://docs.databricks.com/applications/machine-learning/load-data/petastorm.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/load-data/petastorm)).

## NVIDIA TensorRT for high-performance inference

Databricks Runtime 7.0 ML now also includes NVIDIA TensorRT. TensorRT is an SDK that focuses on optimizing pre-trained networks to run efficiently for inferencing especially with GPUs. For example, you can optimize performance of the pre-trained model by using reduced-precision (e.g. FP16 instead of FP32) for production deployments of deep learning inference applications. For example, for a pre-trained TensorFlow model, the model can be optimized with the following python snippet

After a deep learning model is optimized with TensorRT, it can be used for inference just as unoptimized models. See our example notebook for using TensorRT with TensorFlow ([AWS](https://docs.databricks.com/applications/machine-learning/model-inference/resnet-model-inference-tensorrt.html#model-inference-using-tensorflow-and-tensorrt)| [Azure](https://docs.microsoft.com/en-us/azure/databricks/applications/machine-learning/model-inference/resnet-model-inference-tensorrt)).

To achieve the best performance and cost for reduced-precision inference workloads, we highly recommend using TensorRT with the newly supported G4 instance types on AWS.

## Support for TensorFlow 2

Runtime 7.0 ML includes TensorFlow 2.2. TensorFlow 2 contains many new features as well as major breaking changes. If you are migrating from TensorFlow 1.x, Databricks recommends reading TensorFlow’s official [migration guide](https://www.tensorflow.org/guide/migrate) and [Effective TensorFlow 2](https://www.tensorflow.org/guide/effective_tf2). If you have to stay with TensorFlow 1.x, you can enable %pip and downgrade TensorFlow, e.g., to 1.15.3, using the following command in a Python notebook:

`%pip install tensorflow==1.15.3`

## Resources

- Databricks Runtime 7.0 ML release notes ([AWS](https://docs.databricks.com/release-notes/runtime/7.0ml.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/7.0ml))
- Databricks Runtime 7.0 release notes ([AWS](https://docs.databricks.com/release-notes/runtime/7.0.html) | [Azure](https://docs.microsoft.com/en-us/azure/databricks/release-notes/runtime/7.0))
- [Introducing Apache Spark 3.0](https://www.databricks.com/blog/2020/06/18/introducing-apache-spark-3-0-now-available-in-databricks-runtime-7-0.html)
