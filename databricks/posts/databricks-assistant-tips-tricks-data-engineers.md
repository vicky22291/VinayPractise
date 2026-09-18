# Databricks Assistant Tips & Tricks for Data Engineers

- Source: https://www.databricks.com/blog/databricks-assistant-tips-tricks-data-engineers
- Published: 2024-05-02
- Authors: Jackie Zhang, Rafi Kurlansik, Richard Tomlinson
- Categories: product, engineering, data-engineering, tutorials
- Images: 11 total, 0 extracted as architecture

The generative AI revolution is transforming the way that teams work, and Databricks Assistant leverages the best of these advancements. It allows you to query data through a conversational interface, making you more productive inside your Databricks Workspace. The Assistant is powered by [DatabricksIQ, the Data Intelligence Engine for Databricks](https://www.databricks.com/product/databricksiq), helping to ensure your data is secured and responses are accurate and tailored to the specifics of your enterprise. [Databricks Assistant](https://www.databricks.com/product/databricks-assistant) lets you describe your task in natural language to generate, optimize, or debug complex code without interrupting your developer experience.

In this post, we expand on blog [5 tips to get the most out of your Databricks Assistant](https://www.databricks.com/blog/5-tips-get-most-out-your-databricks-assistant) and focus on how the Assistant can improve the life of Data Engineers by eliminating tedium, increasing productivity and immersion, and accelerating time to value. We will follow up with a series of posts focused on different data practitioner personas, so stay tuned for upcoming entries focused on data scientists, SQL analysts, and more.

## Ingestion

When working with Databricks as a data engineer, ingesting data into Delta Lake tables is often the first step. Let’s take a look at two examples of how the Assistant helps load data, one from APIs, and one from files in cloud storage. For each, we will share the prompt and results. As mentioned in the [5 tips blog](https://www.databricks.com/blog/5-tips-get-most-out-your-databricks-assistant), being specific in a prompt gives the best results, a technique consistently used in this article.

To get data from the [datausa.io](http://datausa.io/) API and load it into a Delta Lake table with Python, we used the following prompt:

*Make sure to use PySpark, and be concise! If the Spark DataFrame columns have any spaces in them, make sure to remove them from the Spark DF.*

> [image 1 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/PgFhUqrCUpiB6kYjBfrx-1itJuWuTj6K26PYnWRAgcx16cyLUxyDQkkS00gyXK1d-ikw_I5U6bDllYo6GzsbtMuWKx-5vXYepsLCXJ0S-8DU3je3I05CNNeaB07cckGO6FmjSRcWBetDEzAeGERqMtA: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/PgFhUqrCUpiB6kYjBfrx-1itJuWuTj6K26PYnWRAgcx16cyLUxyDQkkS00gyXK1d-ikw_I5U6bDllYo6GzsbtMuWKx-5vXYepsLCXJ0S-8DU3je3I05CNNeaB07cckGO6FmjSRcWBetDEzAeGERqMtA]

A similar prompt can be used to ingest JSON files from cloud storage into Delta Lake tables, this time using SQL:

*I have JSON files in a UC Volume here: /Volumes/rkurlansik/default/data_science/sales_data.json*

*Write code to ingest this data into a Delta Lake table.  Use SQL only, and be concise!*
 

> [image 2 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/9rx-SK9MO4jtw4Ei8Xwf4gKV4GOfXEUfbh3vfRLe61qMwxWjiKw3xINGR-IKVZv7v1zLXjVRFw7ONeZ_5QpZ8gBsiKh1NlBA1SjDykcFUXquuEkTr4lGIBngkIBV_EQswmiAH8KNxp2sx4_etboTnWc: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/9rx-SK9MO4jtw4Ei8Xwf4gKV4GOfXEUfbh3vfRLe61qMwxWjiKw3xINGR-IKVZv7v1zLXjVRFw7ONeZ_5QpZ8gBsiKh1NlBA1SjDykcFUXquuEkTr4lGIBngkIBV_EQswmiAH8KNxp2sx4_etboTnWc]

 

## Transforming data from unstructured to structured

Following [tidy data principles](https://vita.had.co.nz/papers/tidy-data.html), any given cell of a table should contain a single observation with a proper data type. Complex strings or nested data structures are often at odds with this principle, and as a result, data engineering work consists of extracting structured data from unstructured data.  Let’s explore two examples where the Assistant excels at this task - using regular expressions and exploding nested data structures. 

### Regular expressions

Regular expressions are a means to extract structured data from messy strings, but figuring out the correct regex takes time and is tedious. In this respect, the Assistant is a boon for all data engineers who struggle with regex. 

Consider this example using the *Title* column from the [IMDb dataset](https://www.kaggle.com/datasets/harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows):
 

**

> [image 3 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/HYJhuxawjvny939SqoKBDUN_l5TknTfcSus1u2KJbosfbY4ErooUBsHCqDS0Dqic-kwZIbAFOJERRLr7exCtEZftpWY7MqHverET0r_zxQOgykGsvSQHkicYyQzTaEQigj202UEuGL3v6rzT8jEtDAk: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/HYJhuxawjvny939SqoKBDUN_l5TknTfcSus1u2KJbosfbY4ErooUBsHCqDS0Dqic-kwZIbAFOJERRLr7exCtEZftpWY7MqHverET0r_zxQOgykGsvSQHkicYyQzTaEQigj202UEuGL3v6rzT8jEtDAk]

**
 

This column contains two distinct observations - film title and release year.  With the following prompt, the Assistant identifies an appropriate regular expression to parse the string into multiple columns.

*Here is an example of the Title column in our dataset: 1. The Shawshank Redemption (1994). The title name will be between the number and the parentheses, and the release date is between parentheses. Write a function that extracts both the release date and the title name from the Title column in the imdb_raw DataFrame.*

> [image 4 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/TiGeECRFDNDVcOHVE7yUzkaTVbKzNmzDjfs2hg2dVw0CBgLtLafnZGZC8qVNCEAu_SGVr7UgtcIWMXfbcOo_OBz3ObFfjAcDBu2lc8aLZFROjjMC6qVOTHF0f7loJHr_jT2gGtJMqs-A39sE6t12GeA: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/TiGeECRFDNDVcOHVE7yUzkaTVbKzNmzDjfs2hg2dVw0CBgLtLafnZGZC8qVNCEAu_SGVr7UgtcIWMXfbcOo_OBz3ObFfjAcDBu2lc8aLZFROjjMC6qVOTHF0f7loJHr_jT2gGtJMqs-A39sE6t12GeA]

 

Providing an example of the string in our prompt helps the Assistant find the correct result.  If you are working with sensitive data, we recommend creating a fake example that follows the same pattern. In any case, now you have [one less problem](https://xkcd.com/1171/) to worry about in your data engineering work.

### Nested Structs, Arrays (JSON, XML, etc)

When ingesting data via API, JSON files in storage, or noSQL databases, the resulting Spark DataFrames can be deeply nested and tricky to flatten correctly.  Take a look at this mock sales data in JSON format:

> [image 5 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/rFx07NSDhsqg0lhRHgsiygemCAPlcWWYELp34Qg2XG3dd4RI_MUXvvdkPDKffPHySBbDq0_tG1AyMHY9Q3dlZa-W0o5X0a9172aVCOpdB2mOR3qYQANeQwtIRCLP1B9403FA7sznpBMB9QD440u7Y-I: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/rFx07NSDhsqg0lhRHgsiygemCAPlcWWYELp34Qg2XG3dd4RI_MUXvvdkPDKffPHySBbDq0_tG1AyMHY9Q3dlZa-W0o5X0a9172aVCOpdB2mOR3qYQANeQwtIRCLP1B9403FA7sznpBMB9QD440u7Y-I]

 

Data engineers may be asked to flatten the nested array and extract revenue metrics for each product.  Normally this task would take significant trial and error - even in a case where the data is relatively straightforward.  The Assistant, however, being context-aware of the schemas of DataFrames you have in memory, generates code to get the job done.  Using a simple prompt, we get the results we are looking for in seconds.

*Write PySpark code to flatten the df and extract revenue for each product and customer*

 

## Refactoring, debugging and optimization

Another scenario data engineers face is rewriting code authored by other team members, either ones that may be more junior or have left the company.  In these cases, the Assistant can analyze and explain poorly written code by understanding its context and intent. It can suggest more efficient algorithms, refactor code for better readability, and add comments. 

### Improving documentation and maintainability

This Python code calculates the total cost of items in an online shopping cart.

The use of conditional blocks in this code makes it hard to read and inefficient at scale.  Furthermore, there are no comments to explain what is happening.  A good place to begin is to ask the Assistant to explain the code step by step.  Once the data engineer understands the code, the Assistant can transform it, making it more performant and readable with the following prompt:

*Rewrite this code in a way that is more performant, commented properly, and documented according to Python function documentation standards*

The generated example below properly documents the code, and uses [generator expressions](https://peps.python.org/pep-0289/) instead of conditional blocks to improve memory utilization on larger datasets.

### Diagnosing errors 

Inevitably, data engineers will need to debug.  The Assistant eliminates the need to open multiple browser tabs or switch contexts in order to identify the cause of errors in code, and staying focused is a tremendous productivity boost.  To understand how this works with the Assistant, let’s create a simple PySpark DataFrame and trigger an error.

 

> [image 7 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/31uFRWDLwlqqOWedcurAfhqHMwor85gNhVljvCQA-VTcc6QSHtigpt-TVqW9QC9L0x2RzDGw1DAa__fh1RsK0qVblZTrE5diKQvumfIOY99-fxFkJwt071tLJ467Fa8JJuuHQ6Bk2yjAxu9j3HE2gMA: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/31uFRWDLwlqqOWedcurAfhqHMwor85gNhVljvCQA-VTcc6QSHtigpt-TVqW9QC9L0x2RzDGw1DAa__fh1RsK0qVblZTrE5diKQvumfIOY99-fxFkJwt071tLJ467Fa8JJuuHQ6Bk2yjAxu9j3HE2gMA]

 

In the above example, a typo is introduced when adding a new column to the DataFrame.  The zero in “10” is actually the letter “O”, leading to an *invalid decimal literal *syntax error.  The Assistant immediately offers to diagnose the error.  It correctly identifies the typo, and suggests corrected code that can be inserted into the editor in the current cell.  Diagnosing and correcting errors this way can save hours of time spent debugging.

### Transpiling pandas to PySpark

Pandas is one of the most successful data-wrangling libraries in Python and is used by data scientists everywhere. Sticking with our JSON sales data, let’s imagine a situation where a novice data scientist has done their best to flatten the data using pandas.  It isn’t pretty, it doesn’t follow best practices, but it produces the correct output:

By default, Pandas is limited to running on a single machine. The data engineer shouldn’t put this code into production and run it on billions of rows of data until it is converted to PySpark.  This conversion process includes ensuring the data engineer understands the code and rewrites it in a way that is maintainable, testable, and performant. The Assistant once again comes up with a better solution in seconds. 

> [image 8 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/0Bhc-1MgIzkLPggsNLYuPVzBXRdNyRsoUWZqKM9c26aaNkUJojxyLyu3S3WDZRsTa6KyfpsSaHtvwK5w0z-r-BzPq0lIcOGcna1Z8go-hnf_tpBP91C1yR79eS1wzmDFP0pM0un-e2DmTkbedAUX-C4: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/0Bhc-1MgIzkLPggsNLYuPVzBXRdNyRsoUWZqKM9c26aaNkUJojxyLyu3S3WDZRsTa6KyfpsSaHtvwK5w0z-r-BzPq0lIcOGcna1Z8go-hnf_tpBP91C1yR79eS1wzmDFP0pM0un-e2DmTkbedAUX-C4]

 

Note the generated code includes creating a *SparkSession*, which isn’t required in Databricks.  Sometimes the Assistant, like any LLM, can be wrong or hallucinate.  You, the data engineer, are the ultimate author of your code and it is important to review and understand any code generated before proceeding to the next task. If you notice this type of behavior, adjust your prompt accordingly.

## Writing tests

One of the most important steps in data engineering is to write tests to ensure your DataFrame transformation logic is correct, and to potentially catch any corrupted data flowing through your pipeline.  Continuing with our example from the JSON sales data, the Assistant makes it a breeze to test if any of the revenue columns are negative - as long as values in the revenue columns are not less than zero, we can be confident that our data and transformations in this case are correct.

We can build off this logic by asking the Assistant to incorporate the test into PySpark’s native testing functionality, using the following prompt: 

*Write a test using assertDataFrameEqual from pyspark.testing.utils to check that an empty DataFrame has the same number of rows as our negative revenue DataFrame.* 

The Assistant obliges, providing working code to bootstrap our testing efforts.

> [image 10 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/jWN9UcQSr1DwmfRf-nFbMFtAAI_Vrgv6fLeDdj1r2UysmMDEpuwZ3OvOIYmyAM6WHGmEXocrMnZnnwjIFpBbkvOdJb4GkOljBQ5r0zKos00hDYvqlhY3VVge-FIwkcbfWjKyrFej5GRY_HkTBwPINwE: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/jWN9UcQSr1DwmfRf-nFbMFtAAI_Vrgv6fLeDdj1r2UysmMDEpuwZ3OvOIYmyAM6WHGmEXocrMnZnnwjIFpBbkvOdJb4GkOljBQ5r0zKos00hDYvqlhY3VVge-FIwkcbfWjKyrFej5GRY_HkTBwPINwE]

 

This example highlights the fact that being specific and adding detail to your prompt yields better results.  If we simply ask the Assistant to write tests for us without any detail, our results will exhibit more variability in quality.  Being specific and clear in what we are looking for - a test using PySpark modules that builds off the logic it wrote - generally will perform better than assuming the Assistant can correctly guess at our intentions. 

## Getting help

Beyond a general capability to improve and understand code, the Assistant possesses knowledge of the entire Databricks documentation and Knowledge Base.  This information is indexed on a regular basis and made available as additional context for the Assistant via a RAG architecture.  This allows users to search for product functionality and configurations without leaving the Databricks Data + AI Platform. 

 

For example, if you want to know details about the system environment for the version of Databricks Runtime you are using, the Assistant can direct you to the appropriate page in the Databricks documentation.

 

> [image 11 not annotated: download failed: could not fetch https://lh7-us.googleusercontent.com/v1RMB5XbDvEJOh73irRuh7S_gzAqyoLTpRG-tH6XaEymKnLXhos7cp0lLJxaAgs394uTooR8Hgyesav4V8TyWcrDW1cLMJS6poH4Afar8YCQcdtBu-HGZRwkDh6S9FMni56eDLgIOmU4zQIh8DrFPrQ: HTTP Error 403: Forbidden. source: https://lh7-us.googleusercontent.com/v1RMB5XbDvEJOh73irRuh7S_gzAqyoLTpRG-tH6XaEymKnLXhos7cp0lLJxaAgs394uTooR8Hgyesav4V8TyWcrDW1cLMJS6poH4Afar8YCQcdtBu-HGZRwkDh6S9FMni56eDLgIOmU4zQIh8DrFPrQ]

 

The Assistant can handle simple, descriptive, and conversational questions, enhancing the user experience in navigating Databricks' features and resolving issues. It can even help guide users in filing support tickets!  For more details, read the [announcement article](https://www.databricks.com/blog/introducing-databricks-assistant-help).

## Conclusion

The barrier to entry for quality data engineering has been lowered thanks to the power of generative AI with the Databricks Assistant.  Whether you are a newcomer looking for help on how to work with complex data structures or a seasoned veteran who wants regular expressions written for them, the Assistant will improve your quality of life.  Its core competency of understanding, generating, and documenting code boosts productivity for data engineers of all skill levels.  To learn more, see the Databricks documentation on [how to get started with the Databricks Assistant](https://docs.databricks.com/en/notebooks/databricks-assistant-faq.html) today, and check out our recent blog [5 tips to get the most out of your Databricks Assistant](https://www.databricks.com/blog/5-tips-get-most-out-your-databricks-assistant). You can also watch [this video](https://youtu.be/4pIUI-1lkgM?si=wRo1vqx6OQKm4wym) to see Databricks Assistant in action.
