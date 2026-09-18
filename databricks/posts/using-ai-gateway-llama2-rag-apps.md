# Using MLflow AI Gateway and Llama 2 to Build Generative AI Apps

*Achieve greater accuracy using Retrieval Augmented Generation (RAG) with your own data*

- Source: https://www.databricks.com/blog/using-ai-gateway-llama2-rag-apps
- Published: 2023-08-24
- Authors: Kasey Uhlenhuth, Xiangrui Meng, Hagay Lupesko, Sean Owen, Corey Zumar, Liang Zhang, Ina Koleva, Vladimir Kolovski, Arpit Jasapara
- Categories: data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

To build customer support bots, internal knowledge graphs, or Q&A systems, customers often use Retrieval Augmented Generation (RAG) applications which leverage pre-trained models together with their proprietary data. However, the lack of guardrails for secure credential management and abuse prevention prohibits customers from democratizing access and development of these applications. We recently announced the [MLflow AI Gateway](https://www.databricks.com/blog/announcing-mlflow-ai-gateway), a highly scalable, enterprise-grade API gateway that enables organizations to manage their LLMs and make them available for experimentation and production. Today we are excited to announce extending the AI Gateway to better support RAG applications. Organizations can now centralize the governance of privately-hosted model APIs (via [Databricks Model Serving](https://www.databricks.com/blog/announcing-general-availability-databricks-model-serving)), proprietary APIs (OpenAI, Co:here, Anthropic), and now open model APIs via MosaicML to develop and deploy RAG applications with confidence. 

In this blog post, we'll walk through how you can build and deploy a RAG application on the Databricks Lakehouse AI platform using the [Llama2-70B-Chat model](https://huggingface.co/meta-llama/Llama-2-70b-chat-hf) for text generation and the [Instructor-XL](https://huggingface.co/hkunlp/instructor-xl) model for text embeddings, which are hosted and optimized through [MosaicML's Starter Tier Inference APIs](https://www.mosaicml.com/blog/llama2-inference). Using hosted models allows us to get started quickly and have a cost-effective way to experiment with low throughput. 

The RAG application we're building in this blog answers gardening questions and gives plant care recommendations. 

If you're already familiar with RAG and just want to see an example of how it all comes together, check out [our demo](https://www.databricks.com/resources/demos/tutorials/data-science-and-ai/lakehouse-ai-deploy-your-llm-chatbot) (with example notebooks) that shows you how to use Llama2, MosaicML inference, and vector search to build your RAG application on Databricks.

**What is RAG?**

RAG is a popular architecture that allows customers to improve model performance by leveraging their own data. This is done by retrieving relevant data/documents and providing them as context for the LLM. RAG has shown success in chatbots and Q&A systems that need to maintain up-to-date information or access domain-specific knowledge.

**Use the AI Gateway to put guardrails in place for calling model APIs**

The recently announced MLflow AI Gateway allows organizations to centralize governance, credential management, and rate limits for their model APIs, including SaaS LLMs, via an object called a Route. Distributing Routes allows organizations to democratize access to LLMs while also ensuring user behavior doesn't abuse or take down the system. The AI Gateway also provides a standard interface for querying LLMs to make it easy to upgrade models behind routes as new state-of-the-art models get released. 

We typically see organizations create a Route per use case and many Routes may point to the same model API endpoint to make sure it is getting fully utilized. 

For this RAG application, we want to create two AI Gateway Routes: one for our embedding model and another for our text generation model. We are using open models for both because we want to have a supported path for fine-tuning or privately hosting in the future to avoid vendor lock-in. To do this, we will use MosaicML's Inference API. These APIs provide fast and easy access to state-of-the-art open source models for rapid experimentation and token-based pricing. MosaicML supports [MPT](https://www.mosaicml.com/blog/mpt-30b) and [Llama2](https://ai.meta.com/llama/) models for text completion, and [Instructor](https://huggingface.co/hkunlp/instructor-xl) models for text embeddings. In this example, we will use Llama2-70b-Chat, which was trained on 2 trillion tokens and fine-tuned for dialogue, safety, and helpfulness by Meta and Instructor-XL, a 1.2B parameter instruction fine-tuned embedding model by HKUNLP.

It's easy to create a route for Llama2-70B-Chat using the new support for MosaicML Inference APIs on the AI Gateway:

Similarly to the text completion route configured above, we can create another route for Instructor-XL available through MosaicML Inference API

To get an API key for MosaicML hosted models, sign up [here](https://www.mosaicml.com/get-started?utm_source=blog&utm_medium=referral&utm_campaign=llama2).

**Use LangChain to piece together retriever and text generation**

Now we need to build our vector index from our document embeddings so that we can do document similarity lookups in real-time. We can use LangChain and point it to our AI Gateway Route for our embedding model:

 

We then need to stitch together our prompt template and text generation model:

The RetrievalQA chain chains the two components together so that the retrieved documents from the vector database seed the context for the text summarization model:

You can now log the chain using [MLflow LangChain flavor](https://mlflow.org/docs/latest/python_api/mlflow.langchain.html) and deploy it on a Databricks CPU Model Serving endpoint. Using MLflow automatically provides model versioning to add more rigor to your production process.

**After completing proof-of-concept, experiment to improve quality**

Depending on your requirements, there are many experiments you can run to find the right optimizations to take your application to production. Using the MLflow tracking and evaluation APIs, you can log every parameter, base model, performance metric, and model output for comparison. The new [Evaluation UI in MLflow](https://mlflow.org/docs/latest/models.html#evaluating-with-llms) makes it easy to compare model outputs side by side and all MLflow tracking and evaluation data is stored in query-able formats for further analysis. Some experiments we commonly see:

1. **Latency** - Try smaller models to to reduce latency and cost
2. **Quality** - Try fine tuning an open source model with your own data. This can help with domain-specific knowledge and adhering to a desired response format.
3. **Privacy** - Try privately hosting the model on Databricks LLM-Optimized GPU Model Serving and using the AI Gateway to fully utilize the endpoint across use cases

**Get started developing RAG applications today on Lakehouse AI with MosaicML**

The Databricks Lakehouse AI platform enables developers to rapidly build and deploy generative AI applications with confidence.

To replicate the above chat application in your organization, install our complete RAG chatbot demo directly in your workspace use Llama2, MosaicML inference, and AI Search on the Lakehouse.

[Explore the LLM RAG chatbot demo](https://www.databricks.com/resources/demos/tutorials/data-science-and-ai/lakehouse-ai-deploy-your-llm-chatbot)

 

Further explore and enhance your RAG applications:

- Join the [Databricks GPU Model Serving Preview](https://docs.google.com/forms/d/e/1FAIpQLSebZq4-gNNyeYaXvV96IaZZUG3XtS1hqlCi8ByzeqDdYJGneg/viewform) to privately host state-of-the-art open source or customized models.
- Join the [Databricks AI Search Preview](https://docs.google.com/forms/d/e/1FAIpQLSeeIPs41t1Ripkv2YnQkLgDCIzc_P6htZuUWviaUirY5P5vlw/viewform) for a serverless, scalable vector similarity search tightly integrated with Lakehouse AI.
- Try the [Databricks AutoML Embeddings Preview](https://docs.google.com/forms/d/e/1FAIpQLSeJF5ZKf0pcCUhWnJ8u_tBygl5HOgdcqro9vaO0n4YCGwU2hA/viewform) to customize embeddings to your domain-specific private data.
- [Fine-tune or pretrain your own LLM](https://www.mosaicml.com/training) with MosaicML to own your IP.
