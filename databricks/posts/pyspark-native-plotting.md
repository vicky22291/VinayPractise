# PySpark Native Plotting

*Create visualizations directly from PySpark DataFrames with ease*

- Source: https://www.databricks.com/blog/pyspark-native-plotting
- Published: 2025-06-09
- Authors: Xinrong Meng, Ruifeng Zheng
- Categories: engineering, open-source
- Images: 1 total, 0 extracted as architecture

**Key takeaways**

- Introduction to PySpark Native Plotting: This blog explains the need for built-in visualization capabilities in PySpark, aligning with the functionality users expect from Pandas API on Spark and native pandas DataFrames.
- Key Features and Capabilities: We explain various supported plot types, how PySpark plotting leverages efficient data processing strategies (e.g., sampling, global metrics), and integration with Plotly for visualizations.
- Practical Example: We demonstrate PySpark plotting with a practical example, guiding readers through creating and customizing visualizations, and highlighting actionable insights derived from the plots.

## Introduction

We’re thrilled to introduce native plotting in PySpark with Databricks Runtime 17.0 ([release notes](https://docs.databricks.com/aws/en/release-notes/runtime/17.0)), an exciting leap forward for data visualization. No more jumping between tools just to visualize your data; now, you can create beautiful, intuitive plots directly from your PySpark DataFrames. It’s fast, seamless, and built right in. This long-awaited feature makes exploring your data easier and more powerful than ever.

Working with big data in PySpark has always been powerful, especially when it comes to transforming and analyzing large-scale datasets. While PySpark DataFrames are built for scale and performance, users previously needed to convert them into [Pandas API on Apache Spark™](https://docs.databricks.com/aws/en/pandas/pandas-on-spark) DataFrames to generate plots. But this extra step made visualization workflows more complicated than they needed to be. The difference in structure between PySpark and pandas-style DataFrames often led to friction, slowing down the process of exploring data visually.

### Example

Here’s an example of using PySpark Plotting to analyze Sales, Profit, and Profit Margins across various product categories.

We start with a DataFrame containing sales and profit data for different product categories, as shown below:

Our goal is to visualize the relationship between Sales and Profit, while also incorporating Profit Margin as an additional visual dimension to make the analysis more meaningful. Here is the code to create the plot:

Note that “fig” is of type “plotly.graph_objs._figure.Figure”. We can enhance its appearance by updating the layout using existing Plotly functionalities. The adjusted figure looks like this:

From the figure, we can observe clear relationships between sales and profits across different categories. For instance, Electronics shows high sales and profits with a relatively moderate profit margin, indicating strong revenue generation but room for improved efficiency.

## Features of PySpark Plotting

### User Interface

The user interacts with PySpark Plotting by calling the plot property on a PySpark DataFrame and specifying the desired type of plot either as a submethod or by setting the “kind” parameter. For instance:

or equivalently:

This design aligns with the interfaces of Pandas API on Apache Spark and native pandas, providing a consistent and intuitive experience for users already familiar with pandas plotting.

### Supported Plot Types

PySpark Plotting supports a variety of common chart types, such as line, bar (including horizontal), area, scatter, pie, box, histogram, and density/KDE plots. This enables users to visualize trends, distributions, comparisons, and relationships directly from PySpark DataFrames.

### Internals

The feature is powered by [Plotly](https://pypi.org/project/plotly/) (version 4.8 or later) as the default visualization backend, offering rich, interactive plotting capabilities, while native [pandas](https://pandas.pydata.org/) is used internally to process data for most plots.

Depending on the plot type, data processing in PySpark Plotting is handled through one of three strategies:

- **Top N Rows:** The plotting process uses a limited number of rows from the DataFrame (default: 1000). This can be configured using the “spark.sql.pyspark.plotting.max_rows” option, making it efficient for quick insights. That applies to bar plots, horizontal bar plots, and pie plots.
- **Sampling:** Random sampling effectively represents the overall distribution without processing the entire dataset. This ensures scalability while maintaining representativeness. This applies to area plots, line plots, and scatter plots.
- **Global Metrics:** For box plots, histograms, and density/KDE plots, calculations are performed on the entire dataset. This allows for an accurate representation of data distributions, ensuring statistical correctness.

This approach respects the Pandas API on Apache Spark plotting strategies for each plot type, with additional performance improvements:

- Sampling: Previously, two passes over the entire dataset were required—one to compute the sampling ratio and another to perform the actual sampling. We implemented a new method based on reservoir sampling, reducing it to a single pass.
- Subplots: For cases where each column corresponds to a subplot, we now compute metrics for all columns together, improving efficiency.
- ML-based plots: We introduced dedicated internal SQL expressions for these plots, enabling SQL-side optimizations such as code generation.

## Conclusion

PySpark Native Plotting bridges the gap between PySpark and intuitive data visualization. This feature empowers PySpark users to create high-quality plots directly from their PySpark DataFrames, making data analysis faster and more accessible than ever. Feel free to try out this feature on Databricks Runtime 17.0 to enhance your data visualization experience!

Ready to explore more? Check out the PySpark API documentation for detailed guides and examples.
