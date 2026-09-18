# Build Compound AI Systems Faster with Databricks

- Source: https://www.databricks.com/blog/build-compound-ai-systems-faster-databricks-mosaic-ai
- Published: 2024-10-01
- Authors: Ahmed Bilal, Kasey Uhlenhuth, Siddharth Murching, Akhil Gupta, Eric Peter
- Categories: engineering, data-science-machine-learning, databricks-ai
- Images: 5 total, 0 extracted as architecture

Many of our customers are shifting from monolithic prompts with general-purpose models to specialized compound AI systems to achieve the quality needed for production-ready GenAI apps.

In July, we[launched](https://www.databricks.com/blog/announcing-mosaic-ai-agent-framework-and-agent-evaluation) the Agent Framework and Agent Evaluation, now used by many enterprises to build agentic apps like[Retrieval Augmented Generation (RAG](https://www.databricks.com/glossary/retrieval-augmented-generation-rag). Today, we're excited to announce new features in Agent Framework that simplify the process of building agents capable of complex reasoning and performing tasks like opening support tickets, responding to emails, and making reservations. These capabilities include:

- Connecting LLMs with structured and unstructured enterprise data through shareable and governed** AI tools.**
- Quickly experiment and evaluate agents with the **new playground experience**.
- Seamlessly transition from playground to production with the new **one-click code generation **option.
- Continuously monitor and evaluate LLMs and agents with **AI Gateway and Agent Evaluation integration.**

With these updates, we are making it easier to build and deploy high-quality AI agents that securely interact with your organization’s systems and data.

## Compound AI Systems with Databricks

Databricks provides a complete toolchain for governing, experimenting with, deploying, and improving compound AI systems. This release adds features that make it possible to create and deploy compound AI systems that use agentic patterns.

## Centralized Governance of Tools and Agents with Unity Catalog

Almost all agentic compound AI systems rely on AI tools that extend LLM capabilities by performing tasks like retrieving enterprise data, executing calculations, or interacting with other systems. A key challenge is securely sharing and discovering AI tools for reuse while managing access control. Databricks solves this by using UC Functions as tools and leveraging Unity Catalog's governance to prevent unauthorized access and streamline tool discovery. This allows data, models, tools, and agents to be managed collectively within Unity Catalog through a single interface. 

Unity Catalog Tools can also be executed in a secure and scalable sandboxed environment, ensuring safe and efficient code execution.  Users can invoke these tools within Databricks (Playground and Agent Framework) or externally via the open-source [UCFunctionToolkit](https://api.python.langchain.com/en/latest/tools/langchain_community.tools.databricks.tool.UCFunctionToolkit.html), offering flexibility in how they host their orchestration logic.

## Rapid Experimentation with AI Playground

[AI Playground](https://docs.databricks.com/en/large-language-models/ai-playground.html) now includes new capabilities that enable rapid testing of compound AI systems through a single interactive interface. Users can experiment with prompts, LLMs, tools, and even deployed agents. The new Tool dropdown lets users select hosted tools from Unity Catalog and compare different orchestrator models, like Llama 3.1-70B and GPT-4o (indicated by the “fx” icon), helping identify the best-performing LLM for tool interactions. Additionally, AI Playground highlights chain-of-thought reasoning in the output, making it easier for users to debug and verify results. This setup also allows for quick validation of tool functionality.

AI Playground now integrates with Databricks MLflow, providing deeper insights into agent or LLM quality. Each agent-generated output is evaluated by LLM judges to generate quality metrics, which are displayed inline. When expanded, the results show the rationale behind each metric.

## Easy Deployment of Agents with Model Serving

Databricks platform now includes new capabilities that provide a fast path to deployment for Compound AI Systems. AI Playground now has an **Export** button that auto-generates a Python notebooks. Users can further customize their agents or deploy them as-is in model serving, allowing for quick transition to production.

The auto-generated notebook (1) integrates the LLM and tools into an orchestration framework such as Langgraph (we are starting with Langgraph but plan to support other frameworks in the future), and (2) logs all questions from the Playground session into an evaluation dataset. It also automates performance evaluation using LLM judges from Agent Evaluation. Below is an example of the auto-generated notebook:

 

The notebook can be deployed with [Databricks Model Serving](https://www.databricks.com/product/model-serving), which now includes automatic authentication to downstream tools and dependencies. It also provides request, response, and agent trace logging for real-time monitoring and evaluation, enabling ops engineers to maintain quality in production and developers to iterate and improve agents offline.

Together, these features enable seamless transition from experimentation to a production-ready agent.

## Iterate on Production Quality with AI Gateway and  Agent Evaluation

Agent Bricks AI Gateway's Inference Table allows users to capture incoming requests and outgoing responses from agent production endpoints into a Unity Catalog Delta table. When MLflow tracing is enabled, the Inference Table also logs inputs and outputs for each component within an agent. This data can then be used with existing data tools for analysis and, when combined with Agent Evaluation, can monitor quality, debug, and optimize agent-driven applications.

## What’s coming next?

We’re working on a new feature that enables foundation model endpoints in Model Serving to integrate enterprise data by selecting and executing tools. You can create custom tools and use this capability with any type of LLMs, whether proprietary (such as GPT-4o) or open models (such as LLama-3.1-70B). For example, the following single API call to the foundation model endpoint uses the LLM to process the user’s question, retrieve the relevant weather data by running *get_weather* tool, and then combine this information to generate the final response.

A preview is already available to select customers. **To sign up, talk to your account team about joining the “Tool Execution in Model Serving” Private Preview. **

## Get Started Today

Build your own Compound AI system today using Databricks. From rapid experimentation in AI Playground to easy deployment with Model Serving to debugging with AI Gateway Inference Tables, Databricks provides tools to support the entire lifecycle. 

- Jump into AI Playground to quickly experiment and evaluate AI Agents [[AWS](https://docs.databricks.com/en/generative-ai/create-log-agent.html) | [Azure](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/create-log-agent)]
- Quickly build Custom Agents using our [AI Cookbook](https://ai-cookbook.io/).
- Talk to your account team about joining the “Tool Execution in Model Serving” Private Preview.
- Don’t miss our virtual event in October—a great opportunity to learn about the compound AI systems our valued customers are building. Sign up [here](https://www.databricks.com/resources/webinar/shift-general-data-intelligence).
