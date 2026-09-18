# Llama 2 Foundation Models Available in Databricks Lakehouse AI

- Source: https://www.databricks.com/blog/llama-2-foundation-models-available-databricks-lakehouse-ai
- Published: 2023-10-10
- Authors: Kasey Uhlenhuth, Sid Murching, Lu Wang, Ankit Mathur, Ahmed Bilal
- Categories: announcements, machine-learning, data-science-machine-learning
- Images: 2 total, 0 extracted as architecture

We’re excited to announce that [Meta AI’s Llama 2](https://ai.meta.com/llama/)foundation chat models are available in the [Databricks Marketplace](https://marketplace.databricks.com/details/46527194-66f5-4ea1-9619-d7ec6be6a2fa/Databricks_Llama-2-Models) for you to fine-tune and deploy on private model serving endpoints. The Databricks Marketplace is an open marketplace that enables you to share and exchange data assets, including datasets and notebooks, across clouds, regions, and platforms. Adding to the data assets already offered on Marketplace, this new listing provides instant access to Llama 2's chat-oriented large language models (LLM), from 7 to 70 billion parameters, as well as centralized governance and lineage tracking in the Unity Catalog. Each model is wrapped in MLflow to make it easy for you to use the [MLflow Evaluation API](https://mlflow.org/docs/latest/models.html#evaluating-with-llms)in Databricks notebooks as well as to deploy with a single-click on our [LLM-optimized GPU model serving endpoints.](https://www.databricks.com/blog/announcing-gpu-and-llm-optimization-support-model-serving)

Databricks Marketplace

**What is Llama 2?**

Llama 2 is Meta AI’s family of generative text models that are optimized for chat use cases. The models have outperformed other open models and represent a breakthrough where fine-tuned open models can compete with OpenAI’s GPT-3.5-turbo. 

### Llama 2 on Lakehouse AI

You can now get a secure, end-to-end experience with Llama 2 on the Databricks Lakehouse AI platform:

1. Access on Databricks Marketplace. You can preview the notebook, and get instant access to the chat-family of Llama 2 models from the [Databricks Marketplace](https://marketplace.databricks.com/details/46527194-66f5-4ea1-9619-d7ec6be6a2fa/Databricks_Llama-2-Models). The Marketplace makes it easy to discover and evaluate state-of-the-art foundation models you can manage in the Unity Catalog. 
2. Centralized Governance in the Unity Catalog. Because the models are now in a catalog, you automatically get all the centralized governance, auditing, and lineage tracking that comes with the Unity Catalog for your Llama 2 models.
3. Deploy in One-Click with Optimized GPU Model Serving. We packaged the Llama 2 models in MLflow so you can have single-click deployment to privately host your model with Databricks Model Serving. The now Public Preview of GPU Model Serving is [optimized](https://www.databricks.com/blog/announcing-gpu-and-llm-optimization-support-model-serving) to work with large language models to provide low latencies and support high throughput. This is a great option for use cases that leverage sensitive data or in cases where you cannot send customer data to third-parties. 
4. Saturate Private Endpoints with AI Gateway. Privately hosting models on GPUs can be expensive, which is why we recommend leveraging the [MLflow AI Gateway](https://www.databricks.com/blog/announcing-mlflow-ai-gateway) to create and distribute routes for each use case in your organization to saturate the endpoint. The AI Gateway now supports rate limiting for cost control in addition to secure credential management of Databricks Model Serving endpoints and externally-hosted SaaS LLMs. 
5. Try it yourself: Launch the [product tour](https://www.databricks.com/resources/demos/tours/data-science-and-ai/databricks-llama2-lakehouse) to see how to serve Llama 2 models from Databricks Marketplace

Select the Llama 2 Model from Marketplace

### Get Started with Generative AI on Databricks

The Databricks Lakehouse AI platform enables developers to rapidly build and deploy generative AI applications with confidence.

- Go to the [Marketplace](https://marketplace.databricks.com/details/46527194-66f5-4ea1-9619-d7ec6be6a2fa/Databricks_Llama-2-Models) today and grab the Llama 2 chat models!
- Check out private hosting of LLMs with [Databricks GPU Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/llm-optimized-model-serving.html). If you want to deploy Llama 2-70B please [fill out this form](https://docs.google.com/forms/d/1-GWIlfjlIaclqDz6BPODI2j1Xg4f4WbFvBXyebBpN-Y/edit) and we will contact you with next steps. 
- [Sign up](https://forms.gle/RrNrrSQrzfeZ4a4t7) for the Private Preview of the MLflow AI Gateway
- Build a Retrieval Augmented Generation (RAG) chat bot which augments the LLM with your enterprise data from our [Databricks Demo](https://www.databricks.com/resources/demos/tutorials/data-science-and-ai/lakehouse-ai-deploy-your-llm-chatbot)
- Check out our [GitHub repository with LLM examples](https://github.com/databricks/databricks-ml-examples)
- Launch the [product tour](https://www.databricks.com/resources/demos/tours/data-science-and-ai/databricks-llama2-lakehouse) to see how to serve Llama 2 models from the Databricks Marketplace

Stay tuned for more exciting announcements soon!
