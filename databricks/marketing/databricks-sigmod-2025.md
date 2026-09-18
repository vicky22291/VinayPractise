# Databricks at SIGMOD 2025

*Databricks is proud to be a platinum sponsor of SIGMOD 2025 in Berlin, Germany. Learn more about our accepted papers and engineering opportunities.*

- Source: https://www.databricks.com/blog/databricks-sigmod-2025
- Published: 2025-06-16
- Authors: Sam Plecque, Tim Januschowski
- Categories: engineering, data-warehousing
- Images: 0 total, 0 extracted as architecture

**Key takeaways**

- Databricks is a platinum sponsor at SIGMOD 2025
- Visit our booth to meet the team
- A review of our accepted publications

Databricks is proud to be a platinum sponsor of SIGMOD 2025. The conference runs from June 22 to 27 in Berlin, Germany.

The host city of SIGMOD 2025 is also home to one of Databricks’ four R&D hubs in Europe, alongside Aarhus, Amsterdam, and Belgrade.

The Berlin office plays a central role in Databricks’ research, part of which is showcased at SIGMOD, contributing to our three accepted papers. Principal Engineer [Martin Grund](https://www.linkedin.com/in/mgrund/) is the lead author of two, while Berlin Site Lead [Tim Januschowski](https://www.linkedin.com/in/tim-januschowski/), together with several Berlin-based engineers, co-authored the paper on Unity Catalog. These contributions offer a glimpse into the core systems and strategic work happening in Berlin, where we're actively hiring across all experience levels.

## Visit our Booth

Stop by booth #3 from June 22 to 27 to meet members of the team, learn about our latest work and the uniquely collaborative Databricks culture, and chat about the future of data systems!

## Accepted Publications

### Accepted Industry Papers

#### **[Databricks Lakeguard](https://www.databricks.com/sites/default/files/2025-06/databricks-lakeguard-supporting-fine-grained-access-control-multi-user-capabilities-apache-spark-workloads.pdf): Supporting fine-grained access control and multi-user capabilities for Apache Spark workloads.**

Enterprises want to apply fine-grained access control policies to manage increasingly complex data governance requirements. These rich policies should be uniformly applied across all their workloads. In this paper, we present Databricks Lakeguard, our implementation of a unified governance system that enforces fine-grained data access policies, row-level filters, and column masks across all of an enterprise’s data and AI workloads. Lakeguard builds upon two main components: First, it uses Spark Connect, a JDBC-like execution protocol, to separate the client application from the server and ensure version compatibility. Second, it leverages container isolation in Databricks’ cluster manager to securely isolate user code from the core Spark engine. With Lakeguard, a user’s permissions are enforced for any workload and in any supported language, SQL, Python, Scala, and R on multi-user compute. This work overcomes fragmented governance solutions, where fine-grained access control could only be enforced for SQL workloads, while big data processing with frameworks such as Apache Spark relied on coarse-grained governance at the file level with cluster-bound data access.

#### **[Unity Catalog](https://www.databricks.com/sites/default/files/2025-06/unity-catalog-open-universal-governance-lakehouse-beyond.pdf): Open and Universal Governance for the Lakehouse and Beyond**

Enterprises are increasingly adopting the Lakehouse architecture to manage their data assets due to its flexibility, low cost, and high performance. While the catalog plays a central role in this architecture, it remains underexplored, and current Lakehouse catalogs exhibit key limitations, including inconsistent governance, narrow interoperability, and lack of support for data discovery. Additionally, there is growing demand to govern a broader range of assets beyond tabular data, such as unstructured data and AI models, which existing catalogs are not equipped to handle. To address these challenges, we introduce Unity Catalog (UC), an open and universal Lakehouse catalog developed at Databricks that supports a wide variety of assets and workloads, provides consistent governance, and integrates efficiently with external systems, all with strong performance guarantees. We describe the primary design challenges and how UC’s architecture meets them, and share insights from usage across thousands of customer deployments that validate its design choices. UC’s core APIs and both server and client implementations have been available as open source since June 2024.

### Accepted Demo Papers

#### **[Blink twice](https://www.databricks.com/sites/default/files/2025-06/blink-twice-automatic-workload-pinning-regression-detection-versionless-apache-spark-retries.pdf) - automatic workload pinning and regression detection for Versionless Apache Spark using retries.**

For many users of Apache Spark, managing Spark version upgrades is a significant interruption that typically involves a time-intensive code migration. This is mainly because in Spark, there is no clear separation between the application code and the engine code, making it hard to manage them independently (dependency clashes, use of internal APIs). In Databricks’ Serverless Spark offering, we introduced Versionless Spark where we leverage Spark Connect to fully decouple the client application from the Spark engine which allows us to seamlessly upgrade Spark engine versions. In this paper, we show how our infrastructure built around Spark Connect automatically upgrades and remediates failures in automated Spark workloads without any interruption. Using Versionless Spark, Databricks users’ Spark workloads run indefinitely, and always on the latest version based on a fully managed experience while retaining nearly all of the programmability of Apache Spark.

## Join our Team

We’re hiring! [Check out our open jobs](https://www.databricks.com/company/careers/open-positions?department=Engineering&amp%3Blocation=all) and join our growing engineering teams around the world.
