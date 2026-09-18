# What’s New for Apache Spark on Kubernetes in Apache Spark 2.4 Release

- Source: https://www.databricks.com/blog/2018/09/26/whats-new-for-apache-spark-on-kubernetes-in-the-upcoming-apache-spark-2-4-release.html
- Published: 2018-09-26
- Authors: Yinan Li
- Categories: solutions, engineering, open-source
- Images: 0 total, 0 extracted as architecture

**UPDATED: 11/12/2018**

*This is a community blog from [Yinan Li](https://www.linkedin.com/in/yinan-li-91a3b214/), a software engineer at Google, working in the Kubernetes Engine team. He is part of the group of companies that have contributed to Kubernetes support in the [Apache Spark 2.4.0.](https://spark.apache.org/releases/spark-release-2-4-0.html)*

Since the Kubernetes cluster scheduler backend was initially introduced in [Apache Spark 2.3](https://www.databricks.com/blog/2018/02/28/introducing-apache-spark-2-3.html), the community has been working on a few important new features that make Spark on Kubernetes more usable and ready for a broader spectrum of use cases. The [Apache Spark 2.4](https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html) release comes with a number of new features, some of which are highlighted below:

- Support for running containerized PySpark and SparkR applications on Kubernetes.
- Client mode support that allows users to run interactive applications and notebooks.
- Support for mounting certain types of Kubernetes [volumes](https://kubernetes.io/docs/concepts/storage/volumes/).

Below we will take a deeper look into each of the new features.

## PySpark Support

Soon to be released Spark 2.4 now supports running PySpark applications on Kubernetes. Both Python 2.x and 3.x are supported, and the major version of Python can be specified using the new configuration property `spark.kubernetes.pyspark.pythonVersion`, which can have value 2 or 3 but defaults to 2. Spark ships with a [Dockerfile](https://github.com/apache/spark/blob/branch-2.4/resource-managers/kubernetes/docker/src/main/dockerfiles/spark/bindings/python/Dockerfile) of a base image with the Python binding that is required to run PySpark applications on Kubernetes. Users can use the Dockerfile to build a base image or customize it to build a custom image.

## Spark R Support

Spark on Kubernetes now supports running R applications in the Spark 2.4. Spark ships with a Dockerfile of a base image with the R binding that is required to run R applications on Kubernetes. Users can use the [Dockerfile](https://github.com/apache/spark/blob/branch-2.4/resource-managers/kubernetes/docker/src/main/dockerfiles/spark/bindings/R/Dockerfile) to build a base image or customize it to build a custom image.

## Client Mode Support

As one of the most requested features since the 2.3.0 release, client mode support is now available in the upcoming Spark 2.4. The client mode allows users to run interactive tools such as spark-shell or notebooks in a pod running in a Kubernetes cluster or on a client machine outside a cluster. Note that in both cases, users are responsible for properly setting up connectivity from the executors running in pods inside the cluster to the driver. When the driver runs in a pod in the cluster, the recommended way is to use a Kubernetes headless service to allow executors to connect to the driver using the FQDN of the driver pod. When the driver runs outside the cluster, however, it’s important for users to make sure that the driver is reachable from the executor pods in the cluster. For more detailed information on the client mode support, please refer to the documentation when Spark 2.4 is officially released.

## Other Notable Changes

In addition to the new features highlighted above, the Kubernetes cluster scheduler backend in the upcoming Spark 2.4 release has also received a number of bug fixes and improvements.

- A new configuration property `spark.kubernetes.executor.request.cores` was introduced for configuring the physical CPU request for the executor pods in a way that conforms to the Kubernetes [convention](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu). For example, users can now use fraction values or millicpus like 0.5 or 500m. The value is used to set the CPU request for the container running the executor.
-

The Spark driver running in a pod in a Kubernetes cluster no longer uses an [init-container](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) for downloading remote application dependencies, e.g., jars and files on remote HTTP servers, HDFS, AWS S3, or Google Cloud Storage. Instead, the driver uses spark-submit in client mode, which automatically fetches such remote dependencies in a Spark idiomatic way.

-

Users can now specify image pull secrets for [pulling Spark images from private container registries](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/), using the new configuration property `spark.kubernetes.container.image.pullSecrets.`

-

Users are now able to [use Kubernetes secrets as environment variables through a secretKeyRef](https://kubernetes.io/docs/concepts/configuration/secret/#using-secrets-as-environment-variables). This is achieved using the new configuration options `spark.kubernetes.driver.secretKeyRef.[EnvName]` and `spark.kubernetes.executor.secretKeyRef.[EnvName]` for the driver and executor, respectively.

-

The Kubernetes scheduler backend code running in the driver now manages executor pods using a level-triggered mechanism and is more robust to issues talking to the Kubernetes API server.

## Conclusion and Future Work

First of all, we would like to express huge thanks to [Apache Spark](https://www.databricks.com/spark/about) and Kubernetes community contributors from multiple organizations (Bloomberg, Databricks, Google, Palantir, PepperData, Red Hat, Rockset and others) who have put tremendous efforts into this work and helped get Spark on Kubernetes this far. Looking forward, the community is working on or plans to work on features that further enhance the Kubernetes scheduler backend. Some of the features that are likely available in future Spark releases are listed below.

- Support for using a [pod template](https://issues.apache.org/jira/browse/SPARK-24434) to customize the driver and executor pods. This allows maximum flexibility for customization of the driver and executor pods. For example, users would be able to mount arbitrary volumes or [ConfigMaps](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/) using this feature.
- Dynamic resource allocation and external shuffle service.
- Support for Kerberos authentication, e.g., for accessing secure HDFS.
- Better support for local application dependencies on submission client machines.
- Driver resilience for Spark Streaming applications.
