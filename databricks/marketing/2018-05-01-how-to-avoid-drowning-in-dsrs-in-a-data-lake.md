# How to Avoid Drowning in GDPR Data Subject Requests in a Data Lake

- Source: https://www.databricks.com/blog/2018/05/01/how-to-avoid-drowning-in-dsrs-in-a-data-lake.html
- Published: 2018-05-01
- Authors: Justin Olsson, Sr. Legal Counsel, Michael Armbrust
- Categories: product, engineering, company
- Images: 0 total, 0 extracted as architecture

[Get an early preview of O'Reilly's new ebook](https://www.databricks.com/resources/ebook/delta-lake-running-oreilly?itm_data=avoiddrowningdsrsdatalake-blog-oreillydlupandrunning) for the step-by-step guidance you need to start using Delta Lake.

---

With GDPR enforcement rapidly approaching (May 25, 2018), many companies are still trying to figure out how to comply.  A big pain point, particularly for companies who utilize [data lakes](https://www.databricks.com/discover/data-lakes/introduction) to store vast amounts of data, is how to comply with one of the main requirements under the GDPR - data subject requests, also known as “DSRs”.

**What is a DSR?**

One of the most operationally significant parts of the GDPR for companies is the data subject request.  The GDPR provides all European data subjects (that is, any individual person located in Europe) with a set of enumerated rights related to their personal data including the right to:

-
  - access (i.e., the right to know what personal data a controller or processor has about the individual),
  - rectification (i.e., the right to update incorrect personal data),

- erasure (i.e., the right to be forgotten), and
- portability (i.e., the right to export personal data in a machine-readable format).

Companies have, unless the request is “complex” or “numerous”, thirty days from receipt of the data subject request to comply with the request (keeping in mind any applicable exceptions).

**So what’s the big deal?**

Finding data in a data lake is hard; being sure that you’ve found all data about a particular individual is *very* hard. And many data lakes do not even enable users to perform “delete” operations, even once the data is located, so actually removing it may be practically impossible. In the best case, finding and removing such data is computationally difficult, expensive, and time consuming.  And if a company receives more than just a few data subject requests in a short period of time, the resources spent to comply with the requests could be significant. Further, failure to comply with the GDPR could result in significant penalties, potentially as high as €20 million (or even more - up to 4% of a company’s global annual revenues).

**So that sounds bad. Is there anything that can be done?**

Fortunately, Databricks offers a solution. Enter Databricks Delta, a unified data management system built into the Databricks platform, that brings data reliability and performance optimizations to cloud data lakes.

Databricks Delta’s structured data management system adds transactional capabilities to your data lake that enable you to easily and quickly search, modify, and clean your data using standard SQL DML statements (e.g. DELETE, UPDATE, MERGE INTO). To accomplish this, first ingest your raw data into Delta tables which adds metadata to your files. Once ingested, you can easily search and modify individual records within your Delta tables to meet DSR obligations. The final step is to make Delta your single source of truth by erasing any underlying raw data. This removes any lingering records from your raw data sets. We suggest setting up a retention policy with AWS or Azure of thirty days or less to automatically remove raw data so that no further action is needed to delete the raw data to meet DSR response timelines under the GDPR.

**Can you provide an example of how this works?**

Let’s say your organization received a DSR to delete information related to Justin Olsson ([jdo@databricks.com](mailto:jdo@databricks.com)). After ingesting your raw data into Delta tables, Databricks Delta would enable you to find and delete information related to user [jdo@databricks.com](mailto:jdo@databricks.com) by running two commands:

The first command identifies records that have the string "[jdo@databricks.com](mailto:jdo@databricks.com)" stored in the column email, accounting for varying case (e.g., [JDO@databricks.com](mailto:JDO@databricks.com) would also match), and deletes the data containing these records, rewriting the respective underlying files with the user’s data removed. The second command cleans up the Delta table, removing any stale records that have been logically deleted and those that are outside of the default retention period (e.g., 7 days).

After running these commands, and waiting for your default retention period to delete the underlying raw files, you would be able to state that you had removed records relating to the user [jdo@databricks.com](mailto:jdo@databricks.com) from your data lake.

**Okay, that sounds great , but if I put my data in a Delta table, won’t I be locked in?  What if I want to go somewhere else?**

Nope! Databricks Delta is architected with portability in mind. Databricks Delta uses an open file format (parquet) and you can at any time (either if you ever decide to stop using Delta or if you need to output data to a system that cannot read Delta tables) quickly and easily convert your data back into a format that can be read by other tools.  While doing so, particularly on an ongoing basis, would leave you with the additional DSR obligation of deleting or exporting any personal data that might be contained in the data that was moved out of Databricks Delta, it too will have benefitted from flowing through Databricks Delta, as it will be in a much more structured format, dramatically simplifying that process as well.

**Learn more and watch a live demo**

Watch our on-demand webinar, [**Is Your Data Lake GDPR Ready? How to Avoid Drowning in Data Requests**](https://pages.databricks.com/Reg-EU-WB-GDPR.html), for a  demo and tips for overcoming the challenges of DSRs in a big data world.

This webinar will cover:

- The GDPR requirements of data subject requests
- The challenges big data and data lakes create for organizations
- How Databricks improves data lake management and makes it possible to surgically find and modify or remove individual records
- Best practices for GDPR data governance
- Live demo on how to easily fulfill data requests with Databricks

**[Watch](https://pages.databricks.com/Reg-EU-WB-GDPR.html) the recorded session now.**
