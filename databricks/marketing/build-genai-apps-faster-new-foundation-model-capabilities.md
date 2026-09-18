# Build GenAI Apps Faster with New Foundation Model Capabilities

*Access, Govern, and Monitor any Foundation Models with Databricks Model Serving*

- Source: https://www.databricks.com/blog/build-genai-apps-faster-new-foundation-model-capabilities
- Published: 2023-12-11
- Authors: Ahmed Bilal, Asfandyar Qureshi, Margaret Qian, Jianwei Xie, Sue Ann Hong, Vladimir Kolovski, Mingyu Li, Ankit Mathur
- Categories: engineering
- Images: 3 total, 0 extracted as architecture

Following the [announcements](https://www.databricks.com/blog/building-high-quality-rag-applications-databricks) we made last week about [Retrieval Augmented Generation (RAG)](https://www.databricks.com/glossary/retrieval-augmented-generation-rag), we're excited to announce major updates to Model Serving. Databricks Model Serving now offers a **unified interface**, making it easier to experiment, customize, and productionize foundation models across all clouds and providers. This means you can create high-quality GenAI apps using the best model for your use case while securely leveraging your organization's unique data.

The new unified interface lets you manage all models in one place and query them with a single API, no matter if they're on Databricks or hosted externally. Additionally, we are releasing **Foundation Model APIs** that provide you instant access to popular Large Language Models (LLMs), such as Llama2 and MPT models, directly from within Databricks. These APIs come with on-demand pricing options, such as pay-per-token or provisioned throughput, reducing cost and increasing flexibility. 

 

***Start building GenAI apps today! Visit the ***[***Databricks AI Playground***](https://docs.databricks.com/en/machine-learning/foundation-models/supported-models.html#chat-with-supported-model-llms-using-ai-playground)*** to quickly try generative AI models directly from your workspace.***

### Challenges with Productionizing Foundation Models

Software has revolutionized every industry, and we believe AI will soon transform existing software to be more intelligent. The implications are vast and varied, impacting everything from customer support to healthcare and education. While many of our customers have already begun integrating AI into their products, growing to full-scale production still faces several challenges:

- Experimenting Across Models: Each use case requires experimentation to identify the best model among several open and proprietary options. Enterprises need to quickly experiment across models, which includes managing credentials, rate limits, permissions, and query syntaxes from different model providers.
- Lacking Enterprise Context:  Foundation models have broad knowledge but lack internal knowledge and domain expertise. Used as is, they don't fully meet unique business requirements.
- Operationalizing Models: Requests and model responses must be consistently monitored for quality, debugging, and safety purposes. Different interfaces among models make it challenging to govern and integrate them.

### Databricks Model Serving: Unified Serving for any Foundation Model

Databricks Model Serving is already used in production by hundreds of enterprises for a wide range of use cases, including Large Language Models and Vision applications. With the latest update, we are making it significantly simpler to query, govern and monitor any Foundation Models.

"*With Databricks Model Serving, we are able to integrate generative AI into our processes to improve customer experience and increase operational efficiency. Model Serving allows us to deploy LLM models while retaining complete control over our data and model*."
— Ben Dias, Director of Data Science and Analytics at easyJet

### Access any Foundation Model 

Databricks Model Serving supports any Foundation Model, be it a fully custom model, a Databricks-managed model, or a third-party Foundation Model. This flexibility allows you to choose the right model for the right job, keeping you ahead of future advances in the range of available models. To realize this vision, today we are introducing two new capabilities:

- **Foundation Model APIs**: Foundation Model APIs provide instant access to popular foundation models on Databricks. These APIs completely remove the hassle of hosting and deploying foundation models while ensuring your data remains secure within Databricks' security perimeter. You can get started with Foundation Model APIs on a pay-per-token basis, which significantly reduces operational costs. Alternatively, for workloads requiring fine-tuned models or performance guarantees, you can switch to Provisioned Throughput (previously known as Optimized LLM Serving). The APIs currently support various models, including chat (llama-2-70b-chat), completion (mpt-30B-instruct & mpt-7B-instruct), and embedding models (bge-large-en-v1.5). We will be expanding the model offerings over time.
- **External Models**: External Models (formerly AI Gateway) allow you to add endpoints for accessing models hosted outside of Databricks, such as Azure OpenAI GPT models, Anthropic Claude Models, or AWS Bedrock Models. Once added, these models can be managed from within Databricks. 

Additionally, we have added a list of curated foundation models to the [Databricks Marketplace](https://marketplace.databricks.com/?asset=Model&provider=Databricks&sortBy=date), an open marketplace for data and AI assets, which can be fine-tuned and deployed on Model Serving.

“*Databricks’ Foundation Model APIs allow us to query state-of-the-art open models with the push of a button, letting us focus on our customers rather than on wrangling compute. We’ve been using multiple models on the platform and have been impressed with the stability and reliability we’ve seen so far, as well as the support we’ve received any time we’ve had an issue*.” — Sidd Seethepalli, CTO & Founder, Vellum

 

"*Databricks’ Foundation Model APIs product was extremely easy to set up and use right out of the box, making our RAG workflows a breeze. We’ve been excited by the performance, throughput, and the pricing we’ve seen with this product, and love how much time it’s been able to save us!*” - Ben Hills, CEO, HeyIris.AI"

### Query Models via a Unified Interface 

Databricks Model Serving now offers a unified OpenAI-compatible API and SDK for easy querying of Foundation Models. You can also query models directly from SQL through [AI functions](https://docs.databricks.com/en/large-language-models/ai-functions.html), simplifying AI integration into your analytics workflows. A standard interface allows for easy experimentation and comparison. For example, you might start with a proprietary model and then switch to a fine-tuned open model for lower latency and cost, as demonstrated with [Databricks' AI-generated documentation](https://www.databricks.com/blog/creating-bespoke-llm-ai-generated-documentation).

### Govern and Monitor All Models

The new Databricks Model Serving UI and architecture allow all model endpoints, including externally hosted ones, to be managed in one place. This includes the ability to manage permissions, track usage limits, and monitor the quality of all types of models. For instance, admins can set up external models and grant access to teams and applications, allowing them to query models through a standard interface without exposing credentials. This approach democratizes access to powerful SaaS and open LLMs within an organization while providing necessary guardrails.

 

*"Databricks Model Serving is accelerating our AI-driven projects by making it easy to securely access and manage multiple SaaS and open models, including those hosted on or outside Databricks. Its centralized approach simplifies security and cost management, allowing our data teams to focus more on innovation and less on administrative overhead."* — Greg Rokita, AVP, Technology at Edmunds.com

### Securely Customize Models with Your Private Data

Built on a Data + AI Platform, Databricks Model Serving makes it easy to extend the power of foundation models using techniques such as retrieval augmented generation (RAG), parameter-efficient fine-tuning (PEFT), or standard fine-tuning. You can fine-tune foundation models with proprietary data and deploy them effortlessly on Model Serving. The newly released  Databricks AI Search integrates seamlessly with Model Serving, allowing you to generate up-to-date and contextually relevant responses.

 

*“Using Databricks Model Serving, we quickly deployed a fine-tuned GenAI model for Stardog Voicebox, a question answering and data modeling tool that democratizes enterprise analytics and reduces cost for knowledge graphs. The ease of use, flexible deployment options, and LLM optimization provided by Databricks Model Serving have accelerated our deployment process, freeing our team to innovate rather than manage infrastructure.”* — Evren Sirin, CTO and Co-founder at Stardog

### Get Started Now with Databricks AI Playground

Visit the [AI Playground](https://docs.databricks.com/en/machine-learning/foundation-models/supported-models.html#chat-with-supported-model-llms-using-ai-playground) now and begin interacting with powerful foundation models immediately. With AI Playground, you can prompt, compare and adjust settings such as system prompt and inference parameters, all without needing programming skills.

### For more information:

- Explore the [Foundation Model API](https://docs.databricks.com/en/machine-learning/foundation-models/index.html) and [External Models](https://docs.databricks.com/en/generative-ai/external-models/index.html) Documentation.
- Discover foundation models in the [Databricks Marketplace](https://marketplace.databricks.com/?asset=Model&provider=Databricks&sortBy=date)
- Sign–up for a [Databricks Generative AI Webinar](https://www.databricks.com/resources/webinar/disrupt-your-industry-generative-ai)
- Looking to solve Generative AI use cases? Compete in the Databricks & AWS Generative AI Hackathon! Sign up [here](https://events.databricks.com/GenerativeAIHackathon)
- Go to the [Databricks Model Serving webpage](https://www.databricks.com/product/model-serving)
