# Building Enterprise GenAI Apps with Meta Llama 3 on Databricks

- Source: https://www.databricks.com/blog/building-enterprise-genai-apps-meta-llama-3-databricks
- Published: 2024-04-18
- Authors: Ahmed Bilal, Hagay Lupesko
- Categories: data-science-machine-learning
- Images: 0 total, 0 extracted as architecture

We are excited to partner with Meta to release the latest state-of-the-art large language model, **Meta Llama 3**, on Databricks. With Llama 3 on Databricks, enterprises of all sizes can deploy this new model via a fully managed API. Meta Llama 3 sets a new standard for open language models, providing both the community and enterprises developing their own LLMs with capabilities that rival the most advanced closed model offerings. At Databricks, we share Meta's commitment to advancing open language models and are thrilled to make this new model available to enterprise customers right from day one.

Meta Llama 3 can be accessed through the same unified API on Databricks Model Serving that thousands of enterprises are already using to access other open and external models. This means you can create high-quality, production-scale GenAI apps using the best model for your use case while securely leveraging your organization's unique data.

*Start using Meta Llama 3 on Databricks today! Visit the *[*Databricks AI Playground*](https://docs.databricks.com/en/large-language-models/ai-playground.html)* to quickly try Meta Llama 3 and other Foundation Models directly from your workspace. For more details, see this *[*guide*](https://docs.databricks.com/en/large-language-models/llm-serving-intro.html)*. *

## What is Meta Llama 3?

Meta Llama 3 is an open, large language model (LLM) designed for developers, researchers, and businesses to build, experiment, and responsibly scale their generative AI applications. It demonstrates state-of-the-art performance across a broad range of industry benchmarks and introduces new capabilities, including enhanced reasoning. 

- Compared to its predecessor, Meta Llama 3 has been trained on a significantly larger dataset of over 15 trillion tokens, which improves its comprehension and handling of complex language nuances. 
- It features an extended context window of 8k tokens—double the capacity of Llama 2—allowing the model to access more information from lengthy passages for more informed decision-making. 
- The model utilizes a new Tiktoken-based tokenizer with a vocabulary of 128k tokens, improving its capabilities in both English and multilingual contexts.

## Developing with Meta Llama 3 on Databricks

**Access Meta Llama 3 with production-grade APIs:** Databricks Model Serving offers instant access to Meta Llama 3  via [Foundation Model APIs](https://docs.databricks.com/en/machine-learning/foundation-models/index.html). These APIs completely remove the hassle of hosting and deploying foundation models while ensuring your data remains secure within Databricks' security perimeter.

**Easily compare and govern Meta Llama 3 alongside other models**: You can access Meta Llama 3 with the same unified API and SDK that works with other Foundation Models. This unified interface allows you to experiment with, switch between, and deploy foundation models across all cloud providers easily. Since all internal and externally hosted models are located in one place, this makes it easy to benefit from new model releases without incurring additional setup costs or overburdening yourself with continuous updates.

You can also invoke Meta Llama 3 inference directly from SQL using the `ai_query` SQL function. To learn more, check out the ai_query [documentation](https://docs.databricks.com/en/sql/language-manual/functions/ai_query.html).

**Securely Customize Meta Llama 3 with Your Private Data: **When Llama 2 was released, it sparked a wave of innovation as both the community and enterprises developed specialized and custom models. We anticipate that Meta Llama 3 will further advance this trend, and are excited about the fine-tuned models that will emerge from it. Databricks Model Serving supports seamless deployment of all these fine-tuned variants, making it easy for enterprises to customize the model with their domain-specific and proprietary data. Additionally, enterprises can augment Meta Llama 3 with structured and unstructured data via AI Search and feature serving.

**Stay at the cutting edge with the latest models with optimized performance:** Databricks is dedicated to ensuring that you have access to the best and latest open models with optimized inference. This approach provides the flexibility to select the most suitable model for each task, ensuring you stay at the forefront of emerging developments in the ever-expanding spectrum of available models. Our performance team is actively working to further improve optimization to ensure you continue to enjoy the lowest latency and reduced Total Cost of Ownership.

## Getting started with Meta Llama 3 on Databricks 

Visit the Databricks [AI Playground](https://docs.databricks.com/en/large-language-models/ai-playground.html) to quickly try Meta Llama 3 directly from your workspace. For more information, please refer to the following resources:

- Read Meta Llama 3 launch [blog post](https://llama.meta.com/llama3)
- Explore the Foundation Model [Getting Started Guide](https://docs.databricks.com/en/large-language-models/llm-serving-intro.html)
- Discover invoking LLMs from SQL using [AI functions](https://docs.databricks.com/en/large-language-models/ai-functions.html)
- View the [pricing page](https://www.databricks.com/product/pricing/foundation-model-serving)
