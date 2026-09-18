# Introducing Python User-Defined Table Functions (UDTFs) in Unity Catalog

- Source: https://www.databricks.com/blog/introducing-python-user-defined-table-functions-udtfs-unity-catalog
- Published: 2025-11-17
- Authors: Shujing Yang, Allison Wang, Scott Van Woudenberg, Ruifeng Zheng, Sebastian Hillig, Daniel Tenedorio
- Categories: engineering, open-source
- Images: 1 total, 0 extracted as architecture

**Key takeaways**

- Python UDTFs in Unity Catalog offer a simple yet powerful way to create Python UDTFs once and call them from anywhere in your lakehouse (for example, SQL warehouses, Standard and Dedicated Clusters, Serverless compute, and more).
- Discover and govern them just like any other data assets in Unity Catalog.

Python UDFs let you build an abstraction layer of custom logic to simplify query construction. But what if you want to apply complex logic, such as running a large model or efficiently detecting patterns across rows in your table?

We previously introduced session-scoped [Python User-Defined Table Functions (UDTFs)](https://www.databricks.com/blog/introducing-python-user-defined-table-functions) to support more powerful custom query logic. UDTFs let you run robust, stateful Python logic over entire tables, making it easy to solve normally difficult problems in pure SQL.

## Why User-Defined Table Functions:

-

**Flexibly Process Any Dataset**

The declarative TABLE() keyword lets you pipe any table, view, or even a dynamic subquery directly into your UDTF. This turns your function into a powerful, reusable building block for any slice of your data. You can even use PARTITION BY, ORDER BY, and WITH SINGLE PARTITION to partition the input table into subsets of rows to be processed by independent function calls directly within your Python function.

-

**Run Heavy Initialization Just Once Per Partition**

With a UDTF, you can run expensive setup code, like loading a large ML model or a big reference file, just once for each data partition, not for every single row.

-

**Maintain Context Across Rows**

UDTFs can maintain states from one row to the next within a partition. This unique ability enables advanced analyses like time-series pattern detection and complex running calculations.

Even better, when UDTFs are defined in Unity Catalog (UC), these functions are accessible, discoverable, and executable by anyone with appropriate access. In short, you write once, and run everywhere.

We are excited to announce that UC Python UDTFs that are now available in Public Preview with Databricks Runtime 17.3 LTS, Databricks SQL, and Serverless Notebooks and Jobs.

In this blog, we will discuss some common use cases of UC Python UDTFs with examples and explain how you can use them in your data pipeline.

But first, why UDTFs with UC?

### The Unity Catalog Python UDTF Advantage

-

**Implement once in pure Python and call it from anywhere across sessions and workspaces**

Write your logic in a standard Python class and call Python UDTFs from SQL warehouses (with Databricks SQL Pro and Serverless), Standard and Dedicated UC clusters, and Lakeflow Declarative Pipelines.

-

**Discover using system tables or Catalog Explorer**

- **Share it among users, with full Unity Catalog governance**
-

**Grant and revoke permissions for Python UDTFs**

- **Secure execution with LakeGuard isolation**: Python UDTFs are executed in sandboxes with temporary disk and network access, preventing the possibility of interference from other workload.

## Quick Start: Simplified IP Address Matching

Let’s start with a common data engineering problem: matching IP addresses against a list of network CIDR blocks (for example, to identify traffic from internal networks). This task is awkward in standard SQL, as it lacks built-in functions for CIDR logic and packages.

UC Python UDTFs remove that friction. They let you bring Python’s rich libraries and algorithms directly into your SQL. We'll build a function that:

1. Takes a table of IP logs as input.
2. Efficiently loads a list of known network CIDRs just once per data partition.
3. For each IP address, it uses Python's powerful ipaddress library to check if it belongs to any of the known networks.
4. Returns the original log data, enriched with the matching network.

Let's start with some sample data containing both IPv4 and IPv6 addresses.

Next, we'll define and register our UDTF. Notice the Python class structure:

- The t TABLE parameter accepts an input table with any schema—the UDTF automatically adapts to process whatever columns are provided. This flexibility means you can use the same function across different tables without needing to modify the function signature, but it also requires careful checking of the schema of the rows.
- The __init__ method is perfect for heavy, one-time setup, like loading our large network list. This work takes place once per partition of the input table.
- The eval method processes each row, containing the core matching logic. This method executes exactly once for each row of the input partition being consumed by its corresponding instance of the IpMatcher UDTF class for that partition.
- The HANDLER clause specifies the name of the Python class that implements the UDTF logic.

Now that our ip_cidr_matcher is registered in Unity Catalog, we can call it directly from SQL using the TABLE() syntax. It's as simple as querying a regular table.

It outputs:

| log_id | ip_address | network | ip_version |
|---|---|---|---|
| log1 | 192.168.1.100 | 192.168.0.0/16 | 4 |
| log2 | 10.0.0.5 | 10.0.0.0/8 | 4 |
| log3 | 172.16.0.10 | 172.16.0.0/12 | 4 |
| log4 | 8.8.8.8 | null | 4 |
| log5 | 2001:db8::1 | 2001:db8::/32 | 6 |
| log6 | 2001:db8:85a3::8a2e:370:7334 | 2001:db8::/32 | 6 |
| log7 | fe80::1 | fe80::/10 | 6 |
| log8 | ::1 | ::1/128 | 6 |
| log9 | 2001:db8:1234:5678::1 | 2001:db8::/32 | 6 |

## Generating image captions with batch inference

This example walks through the setup and usage of a UC Python UDTF for batch image captioning using Databricks vision model serving endpoints. First, we create a table containing public image URLs from Wikimedia Commons:

This table contains 4 sample images: a nature boardwalk, an ant macro photo, a cat, and a galaxy.

And then we create a UC Python UDTF to generate image captions.

1. We first initialize the UDTF with the configuration, including batch size, Databricks API token, vision model endpoint, and workspace URL.
2. In the eval method, we collect the image URLs into a buffer. When the buffer reaches the batch size, we trigger batch processing. This ensures that multiple images are processed together in a single API call rather than individual calls per image.
3. In the batch processing method, we download all buffered images, encode them as base64, and send them to a single API request to Databricks VisionModel. The model processes all images simultaneously and returns captions for the entire batch.
4. The terminate method is executed exactly once at the end of each partition. In the terminate method, we process any remaining images in the buffer and yield all collected captions as results.

Please note to replace <workspace-url> with your actual Databricks workspace URL (for example, https://your-workspace.cloud.databricks.com).

To use the batch image caption UDTF, simply call it with the sample images table: Please note to replace your_secret_scope and api_token with the actual secret scope and key name for the Databricks API token

The output is:

| caption |
|---|
| Wooden boardwalk cutting through vibrant wetland grasses under blue skies |
| Black ant in detailed macro photography standing on a textured surface |
| Tabby cat lounging comfortably on a white ledge against a white wall |
| Stunning spiral galaxy with bright central core and sweeping blue-white arms against the black void of space. |

You can also generate image captions category by category:

The output is:

| caption |
|---|
| Black ant in detailed macro photography standing on a textured surface |
| Stunning spiral galaxy with bright center and sweeping blue-tinged arms against the black of space. |
| Tabby cat lounging comfortably on white ledge against white wall |
| Wooden boardwalk cutting through lush wetland grasses under blue skies |

## Future Work

We're actively working on extending Python UDTFs with even more powerful and performant features, including:

- **Polymorphic UDTFs in Unity Catalog** are functions whose output schemas are dynamically analyzed and resolved based on the input arguments. They are already supported in session-scoped Python UDTFs and are in progress for Python UDTFs in Unity Catalog.
- **Python Arrow UDTF**: A new Python UDTF API that enables data processing with native Apache Arrow record batch (iterator[Arrow.record_batch]) for significant performance boosts with large datasets.
