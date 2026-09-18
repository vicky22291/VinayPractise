# Production-Quality RAG Applications with Databricks

*Announcing the general availability of AI Search and major updates to Model Serving*

- Source: https://www.databricks.com/blog/production-quality-rag-applications-databricks
- Published: 2024-05-08
- Authors: Akhil Gupta, Oliver Chiu
- Categories: data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

In December, we [announced](https://www.databricks.com/blog/building-high-quality-rag-applications-databricks) a new suite of tools to get Generative AI applications to production using Retrieval Augmented Generation (RAG). Since then, we have seen an explosion of RAG applications being built by thousands of customers on the [Databricks Data + AI Platform](https://www.databricks.com/product/data-intelligence-platform).

Today, we are excited to make several announcements to make it easy for enterprises to build high-quality RAG applications with native capabilities available directly in the Databricks Data + AI Platform - including the General Availability of AI Search and major updates to Model Serving.

### **The Challenge of High Quality AI Applications **

As we collaborated closely with our customers to build and deploy AI applications, we’ve identified that the greatest challenge is achieving the high standard of quality required for customer facing systems. Developers spend an inordinate amount of time and effort to ensure that the output of AI applications is accurate, safe, and governed before making it available to their customers and often cite accuracy and quality as the biggest blockers to unlocking the value of these exciting new technologies.

Traditionally, the primary focus to maximize quality has been to deploy an LLM that provides the highest quality baseline reasoning and knowledge capabilities. But, recent research has shown that base model quality is only one of many determinants of the quality of your AI application. LLMs without enterprise context and guidance still hallucinate because they don’t by default have a good understanding of your data. AI applications can also expose confidential or inappropriate data if they don’t understand governance and have proper access controls. 

>  Corning is a materials science company where our glass and ceramics technologies are used in many industrial and scientific applications. We built an AI research assistant using Databricks to index 25M documents of US patent office data. Having the LLM-powered assistant respond to questions with high accuracy was extremely important to us so our researchers could find and further the tasks they were working on. To implement this, we used Databricks AI Search to augment a LLM with the US patent office data. The Databricks solution significantly improved retrieval speed, response quality, and accuracy.  - Denis Kamotsky, Principal Software Engineer, Corning

### **An ****AI* Systems***** Approach to Quality **

Achieving production quality in GenAI applications requires a comprehensive approach involving multiple components that cover all aspects of the GenAI process: data preparation, retrieval models, language models (either SaaS or open source), ranking, post-processing pipelines, prompt engineering, and training on custom enterprise data. Together these components constitute an *AI System*.

>  Ford Direct needed to create a unified chatbot to help our dealers assess their performance, inventory, trends, and customer engagement metrics. Databricks AI Search allowed us to integrate our proprietary data and documentation into our Generative AI solution that uses retrieval-augmented generation (RAG).  The integration of AI Search with Databricks Delta Tables and Unity Catalog made it seamless to our vector indexes real-time as our source data is updated, without needing to touch/re-deploy our deployed model/application. - Tom Thomas, VP of Analytics, FordDirect

Today, we are excited to announce major updates and more details to help customers build production-quality GenAI applications. 

- General availability of [AI Search](https://docs.databricks.com/en/generative-ai/vector-search.html), a serverless vector database purpose-built for customers to augment their LLMs with enterprise data.  
- General availability in the coming weeks of [Model Serving Foundation Model API](https://docs.databricks.com/en/machine-learning/foundation-models/index.html) which allows you to access and query state-of-the-art LLMs from a serving endpoint
- Major updates to [Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/index.html) 
  - A new user interface making it easier than ever before to deploy, serve, monitor, govern, and query LLMs
  - Support for additional state of the art models - Claude3, Gemini, DBRX and Llama3
  - Performance improvements to deploy and query large LLMs
  - Better governance and auditability with support for inference tables across all types of serving endpoints.

We also previously announced the following that helps deploy production-quality GenAI:

- [General availability of Feature Serving](https://www.databricks.com/blog/announcing-general-availability-databricks-feature-serving) so you can make structured context available to RAG apps 
- A flexible [quality monitoring interface](https://docs.databricks.com/en/lakehouse-monitoring/index.html)to observe production performance of RAG apps.

Over the course of this week, we’ll have detailed blogs on how you can use these new capabilities to build high-quality RAG apps. We'll also share an insider's blog on how we built DBRX, an open, general-purpose LLM created by Databricks. 

### **Explore more**

- Watch the [GenAI Payoff Virtual Event](https://www.databricks.com/resources/webinar/gen-ai-payoff-2024)
- Refer to [AI Search](https://docs.databricks.com/en/generative-ai/vector-search.html) and [Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/index.html) documentation
- Join us at [Data + AI Summit](https://www.databricks.com/dataaisummit)
