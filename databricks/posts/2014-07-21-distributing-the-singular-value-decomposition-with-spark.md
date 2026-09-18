# Distributing the Singular Value Decomposition with Apache Spark

- Source: https://www.databricks.com/blog/2014/07/21/distributing-the-singular-value-decomposition-with-spark.html
- Published: 2014-07-21
- Authors: Li Pu, Reza Zadeh
- Categories: engineering, data-science-machine-learning, open-source
- Images: 0 total, 0 extracted as architecture

Guest post by Li Pu from Twitter and Reza Zadeh from Databricks on their recent contribution to Apache Spark's machine learning library.

---

The [Singular Value Decomposition (SVD)](https://en.wikipedia.org/wiki/Singular_value_decomposition) is one of the cornerstones of linear algebra and has widespread application in many real-world modeling situations. Problems such as recommender systems, linear systems, least squares, and many others can be solved using the SVD. It is frequently used in statistics where it is related to principal component analysis (PCA) and to correspondence analysis, and in signal processing and pattern recognition. Another usage is latent semantic indexing in natural language processing.

Decades ago, before the rise of distributed computing, computer scientists developed the single-core [ARPACK package](https://www.caam.rice.edu/software/ARPACK/) for computing the eigenvalue decomposition of a matrix. Since then, the package has matured and is in widespread use by the numerical linear algebra community, in tools such as SciPy, [GNU Octave](https://www.octave.org/doc/latest//External-Packages.html), and [MATLAB](https://www.mathworks.com/products/matlab.html).

An important feature of ARPACK is its ability to allow for arbitrary matrix storage formats. This is possible because it doesn't operate on the matrices directly, but instead acts on the matrix via prespecified operations, such as matrix-vector multiplies. When a matrix operation is required, ARPACK gives control to the calling program with a request for a matrix-vector multiply. The calling program must then perform the multiply and return the result to ARPACK.

By using the distributed-computing power of Spark, we can distribute the matrix-vector multiplies, and thus exploit the years of numerical computing expertise that have gone into building ARPACK, and the years of distributing computing expertise that have gone into Spark.

Since ARPACK is written in Fortran77, it cannot immediately be used on the Java Virtual Machine. However, through the [netlib-java](https://github.com/fommil/netlib-java) and [breeze](https://github.com/scalanlp/breeze) interfaces, we can use ARPACK on the JVM. This also means that low-level hardware optimizations can be exploited for any local linear algebraic operations. As with all linear algebraic operations within MLlib, we use hardware acceleration whenever possible.

We are building the linear algebra capabilities of [MLlib](https://spark.apache.org/docs/latest/mllib-dimensionality-reduction.html). Currently in Apache Spark 1.0 there is support for Tall and Skinny [SVD and PCA,](https://github.com/apache/spark/pull/88) and as of Apache Spark 1.1, we will have support for SVD and PCA [via ARPACK](https://github.com/apache/spark/pull/964).

## Example Runtime

A very popular matrix in the recommender systems community is the Netflix Prize Matrix. The matrix has 17,770 rows, 480,189 columns, and 100,480,507 non-zeros. Below we report results on several larger matrices (up to 16x larger) we experimented with at Twitter.

With the Spark implementation of SVD using ARPACK, calculating wall-clock time with 68 executors and 8GB memory in each, looking for the top 5 singular vectors, we can factorize larger matrices distributed in RAM across a cluster, in a few seconds.

| **Matrix size** | **Number of nonzeros** | **Time per iteration (s)** | **Total time (s)** |
|---|---|---|---|
| 23,000,000 x 38,000 | 51,000,000 | 0.2 | 10 |
| 63,000,000 x 49,000 | 440,000,000 | 1 | 50 |
| 94,000,000 x 4,000 | 1,600,000,000 | 0.5 | 50 |

Apart from being fast, SVD is also easy to run. Here is a [code snippet](https://gist.github.com/vrilleup/9e0613175fab101ac7cd) showing how to run it on sparse data loaded from a text file.
