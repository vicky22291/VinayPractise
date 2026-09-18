# Introducing Built-in Image Data Source in Apache Spark 2.4

- Source: https://www.databricks.com/blog/2018/12/10/introducing-built-in-image-data-source-in-apache-spark-2-4.html
- Published: 2018-12-10
- Authors: Tomas Nykodym, Weichen Xu
- Categories: solutions, engineering, open-source
- Images: 1 total, 1 extracted as architecture

## Introduction

With recent advances in deep learning frameworks for image classification and object detection, the demand for standard image processing in Apache Spark has never been greater. Image handling and preprocessing have their specific challenges - for example, images come in different formats (eg., jpeg, png, etc.), sizes, and color schemes, and there is no easy way to test for correctness (silent failures).

An image data source addresses many of these problems by providing the standard representation you can code against and abstracts from the details of a particular image representation.

Apache Spark 2.3 provided the **ImageSchema.readImages** API (see Microsoft’s [post Image Data Support in Apache Spark](https://docs.microsoft.com/en-us/archive/blogs/machinelearning/image-data-support-in-apache-spark)), which was originally developed in the[MMLSpark library](https://github.com/microsoft/SynapseML). In [Apache Spark 2.4](https://www.databricks.com/blog/2018/11/08/introducing-apache-spark-2-4.html), it’s much easier to use because it is now a built-in data source. Using the image data source, you can load images from directories and get a DataFrame with a single image column.

This blog post describes what an image data source is and demonstrates its use in [Deep Learning Pipelines](https://www.databricks.com/blog/2017/06/06/databricks-vision-simplify-large-scale-deep-learning.html) on the Databricks [Unified Analytics Platform](https://www.databricks.com/product/data-lakehouse).

## Image Import

Let’s examine how images can be read into Spark via image data source. In [PySpark](https://www.databricks.com/glossary/pyspark), you can import images as follows:

Similar APIs exist for Scala, Java, and R.

With an image data source, you can import a nested directory structure (for example, use a path like `/path/to/dir/**`). For more specific images, you can use partition discovery by specifying a path with a partition directory (that is, a path like `/path/to/dir/date=2018-01-02/category=automobile`).

## Image Schema

Images are loaded as a DataFrame with a single column called “image.” It is a struct-type column with the following fields:

While most of the fields are self-explanatory, some deserve a bit of explanation:

**nChannels**: The number of color channels. Typical values are 1 for grayscale images, 3 for colored images (e.g., RGB), and 4 for colored images with alpha channel.

**Mode**: Integer flag that provides information on how to interpret the data field. It specifies the data type and channel order the data is stored in. The value of the field is expected (but not enforced) to map to one of the [OpenCV](https://opencv.org/) types displayed below. OpenCV types are defined for 1, 2, 3, or 4 channels and several data types for the pixel values.

A Mapping of Type to Numbers in OpenCV (data types x number of channels):

**Summary:** OpenCV data types are mapped to numeric values according to the number of image channels.

**Components:**

- CV_8U type
- CV_8S type
- CV_16U type
- CV_16S type
- CV_32S type
- CV_32F type
- CV_64F type
- C1, C2, C3, and C4 channel columns

**Flows:**

- none

**Numbers:** 1, 2, 3, 4, 8, 16, 24, 25, 26, 27, 28, 29, 30, 0, 9, 17, 2, 10, 18, 3, 11, 19, 4, 12, 20, 5, 13, 21, 6, 14, 22

```mermaid
%% OpenCV data type to channel count numeric mapping
flowchart TD
  A[CV 8U: C1 0, C2 8, C3 16, C4 24]
  B[CV 8S: C1 1, C2 9, C3 17, C4 25]
  C[CV 16U: C1 2, C2 10, C3 18, C4 26]
  D[CV 16S: C1 3, C2 11, C3 19, C4 27]
  E[CV 32S: C1 4, C2 12, C3 20, C4 28]
  F[CV 32F: C1 5, C2 13, C3 21, C4 29]
  G[CV 64F: C1 6, C2 14, C3 22, C4 30]
  H[C1: one channel]
  I[C2: two channels]
  J[C3: three channels]
  K[C4: four channels]

  classDef client fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
  classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
  classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
  classDef cache fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
  classDef queue fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
  classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
  classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
  classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111

  class A,B,C,D,E,F,G service
  class H,I,J,K client
```

<sub>source image: https://www.databricks.com/wp-content/uploads/2018/12/Screen-Shot-2018-12-10-at-9.19.49-AM.png</sub>

**data**: Image data stored in a binary format. Image data is represented as a 3-dimensional array with the dimension shape (height, width, nChannels) and array values of type t specified by the mode field. The array is stored in row-major order.

### Channel Order

Channel order specifies the ordering in which the colors are stored. For example, if you have a typical three channel image with red, blue, and green components, there are six possible orderings. Most libraries use either RGB or BGR. Three (four) channel OpenCV types are expected to be in BGR(A) order.

## Code Sample

[Deep Learning Pipelines](https://www.databricks.com/blog/2017/06/06/databricks-vision-simplify-large-scale-deep-learning.html) provides an easy way to get started with ML for using images. Starting from version 0.4, [Deep Learning Pipelines](https://spark-packages.org/package/databricks/spark-deep-learning) uses the image schema described above as its image format, replacing former image schema format defined within the Deep Learning Pipelines project.

In this Python example, we use transfer learning to build a custom image classifier:

**Note**: For Deep Learning Pipelines developers, the new image schema changes the ordering of the color channels to BGR from RGB. To minimize confusion, some of the internal APIs now require you to specify the ordering explicitly.

## What’s Next

It would be helpful if you could sample the returned DataFrame via `df.sample`, but sampling is not optimized. To improve this, we need to push down the sampling operator to the image data source so that it doesn’t need to read every image file. This feature will be added in DataSource V2 in the future.

New image features are planned for future releases in Apache Spark and Databricks, so stay tuned for updates. You can also try the deep learning [example notebook](https://docs.databricks.com/data/data-sources/image.html) in [Databricks Runtime 5.0 ML](https://docs.databricks.com/release-notes/runtime/5.0ml.html).

## Read More

For further reading on Image Data Source, and how to use it:

- Read our documentation on Image Data Source for [Azure](https://docs.microsoft.com/en-us/azure/databricks/data/data-sources/image) and [AWS](https://docs.microsoft.com/en-us/azure/databricks/data/data-sources/image).
- Try the [example notebook](https://docs.databricks.com/data/data-sources/image.html) on [Databricks Runtime 5.0 ML](https://www.databricks.com/blog/2018/11/27/introducing-databricks-runtime-5-0-for-machine-learning.html).
- Learn about [Deep Learning Pipelines](https://docs.databricks.com/applications/machine-learning/train-model/deep-learning-pipelines.html).
- Visit the [Deep Learning Pipelines on GitHub](https://github.com/databricks/spark-deep-learning).

## Acknowledgments

Thanks to Denny Lee, Stephanie Bodoff, and Jules S. Damji for their contributions.
