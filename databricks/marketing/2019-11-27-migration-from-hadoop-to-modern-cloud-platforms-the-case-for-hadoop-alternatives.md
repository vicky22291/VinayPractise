# Migration from Hadoop to Modern Cloud Platforms: The Case for Hadoop Alternatives

- Source: https://www.databricks.com/blog/2019/11/27/migration-from-hadoop-to-modern-cloud-platforms-the-case-for-hadoop-alternatives.html
- Published: 2019-11-27
- Authors: Anand Venugopal, James Nguyen
- Categories: open-source, company
- Images: 1 total, 0 extracted as architecture

Companies rely on their big data and [analytics platforms](https://www.databricks.com/product/data-lakehouse) to support innovation and digital transformation strategies. However, many [Hadoop](https://www.databricks.com/glossary/hadoop)users struggle with complexity, unscalable infrastructure, excessive maintenance overhead and overall, unrealized value. We help customers navigate their Hadoop migrations to modern cloud platforms such as Databricks and our partner products and solutions, and in this post, we’ll share what we’ve learned.

## **Challenges with Hadoop Architectures**

Teams migrate from Hadoop for a variety of reasons. It’s often a combination of “push” and “pull”: limitations with existing Hadoop systems are pushing teams to explore Hadoop alternatives, and they’re also being pulled by the new possibilities enabled by modern cloud data architectures. While the architecture requirements vary for different teams, we’ve seen a number of common factors with customers looking to leave Hadoop.

- **Poor data reliability and scalability:** A pharmaceutical company had data-scalability issues with its [Hadoop clusters](https://www.databricks.com/glossary/hadoop-cluster), which could not scale up for research projects or scale down to reduce costs. A consumer brand company was tired of its Hadoop jobs failing, leaving its data in limbo and impacting team productivity.
- **Time and resource costs:** One retail company was experiencing excessive operational burdens given the time and headcount required to maintain, patch, and upgrade complicated Hadoop systems. A media start-up suffered reduced productivity because of the amount of time spent configuring its systems instead of getting work done for the business.
- **Blocked projects:** A logistics company wanted to do more with its data, but the company’s Hadoop-based data platform couldn’t keep up with it’s business goals—the team could only process a sample of their imaging data, and they had advanced network computations that couldn’t be finished within a reasonable period of time. Another manufacturing company had data stuck in different silos, some in HPC clusters, other on Hadoop, which was hindering important deep learning projects for the business.

Beyond the technical challenges, we’ve also had customers raise concerns around the long term viability of the technology and the business stability of its vendors. Google, whose seminal 2004 [paper on MapReduce](https://static.googleusercontent.com/media/research.google.com/en//archive/mapreduce-osdi04.pdf) underpinned the open-source development of Apache Hadoop, has stopped using MapReduce altogether, as [tweeted](https://twitter.com/uhoelzle/status/1177360023976067077) by Google SVP Urs Hölzle: “... R.I.P. MapReduce. After having served us well since 2003, today we removed the remaining internal codebase for good…” These technology shifts are reflected by the [consolidation](https://techcrunch.com/2019/01/03/cloudera-and-hortonworks-finalize-their-merger/) and [purchase](https://www.informationweek.com/big-data-analytics/hpe-emerges-to-rescue-mapr-customers) activity in the space that Hadoop-focused vendors have seen.  This collection of concerns has inspired many companies to re-evaluate their Hadoop investments to see if the technology still meets their needs.

## **Shift toward Modern Cloud Data Platforms**

Data platforms built for cloud-native use can deliver significant gains compared to legacy Hadoop environments, which “pull” companies into their cloud adoption. This also includes customers that have tried to use Hadoop in the cloud. Here are some results from a customer that migrated to Databricks from a cloud based Hadoop service.

- Up to 50% performance improvement in data processing job runtime
- 40% lower monthly infrastructure cost
- 200% greater data processing throughput
- Security environment credentials centralized across six global teams
- Fifteen AI and ML initiatives unblocked and accelerated

Hadoop was not designed to run natively in cloud environments, and while cloud-based Hadoop services certainly have improvements compared to their on-premises counterparts, both still lag compared to modern data platforms architected to run natively in the cloud, in terms of both performance and their ability to address more sophisticated data use cases. On-premise Hadoop customers that we’ve worked with have seen improvements even greater than those noted above.

## **Managing Change: Hadoop to Cloud Migration Principles**

While migrating to a modern cloud data platform can be daunting, the customers we’ve worked with often consider the prospect of staying with their existing solutions to be even worse. The pain of staying where they were was significantly worse than the costs of migrating. We’ve worked hard to streamline the migration process across various dimensions:

- **Managing Complexity and Scale:** Metadata movement, Workload Migration, Data Migration
- **Manage Quality and Risk: **Methodology, Project Plans, Timelines, Technology Mappings
- **Manage Cost and Time:** Partners and Professional Services bringing experience and training

## **Future Proofing Your Cloud Analytics Projects**

Cloud migration decisions are as much about business decisions as they are about technology. They force companies to take a hard look at what their current systems deliver, and evaluate what they need to achieve their goals, whether they’re measured in petabytes of data processed, customer insights uncovered, or business financial targets.

With clarity on these goals comes important technical details, such as mapping technology components from on-premises models to cloud models, evaluating cloud resource utilization and cost-to-performance, and structuring a migration project to minimize errors and risks. If you want to learn more, check out my [on-demand webinar](https://pages.databricks.com/201911-WB-Hadoop-Spark-Modernize-Analytics-Architecture_03.On-demandpage.html) to explore cloud migration concepts, data modernization best practices, and migration product demos.
