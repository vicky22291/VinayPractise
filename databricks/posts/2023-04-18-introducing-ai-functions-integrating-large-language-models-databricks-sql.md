# Introducing AI Functions: Integrating Large Language Models with Databricks SQL

*AI Functions brings the power of LLMs and more into DB SQL*

- Source: https://www.databricks.com/blog/2023/04/18/introducing-ai-functions-integrating-large-language-models-databricks-sql.html
- Published: 2023-04-18
- Authors: Patrick Wendell, Eric Peter, Nicolas Pelaez, Jianwei Xie, Vinny Vijeyakumaar, Linhong Liu, Shitao Li
- Categories: platform, data-warehousing
- Images: 1 total, 0 extracted as architecture

With all the incredible progress being made in the space of Large Language Models, customers have asked us how they can enable their SQL analysts to leverage this powerful technology in their day-to-day workflows.

Today, we are excited to announce the public preview of AI Functions. AI Functions is a built-in DB SQL function, allowing you to access Large Language Models (LLMs) directly from SQL.

With this launch, you can now quickly experiment with LLMs on your company’s data from within a familiar SQL interface. Once you have developed the correct LLM prompt, you can quickly turn that into a production pipeline using existing Databricks tools such as Delta Live Tables or scheduled Jobs. This greatly simplifies both the development and productionization workflow for LLMs.

AI Functions abstracts away the technical complexities of calling LLMs, enabling analysts and data scientists to start using these models without worrying about the underlying infrastructure.

## Using AI Functions

To show how AI Functions works, imagine that you’re an analyst and have been given a historical list of thousands of call transcripts with the task of providing a report that breaks down all of the calls into one of four categories [Frustrated, Happy, Neutral, Satisfied]. Typically, this would require you to request the data science team create a classification model. Instead, with AI Functions, you can prompt a Large Language Model, such as OpenAI’s ChatGPT model, directly from SQL. An example LLM prompt could look like the following:

With AI Functions, you can turn this prompt in a custom SQL function. This enables you to do the following, rather than a complicated multi-step pipeline:

Let’s use this example to walk through the steps needed to do so. We will use the Azure OpenAI service as our large language model, although you could also use OpenAI. In future releases, we will enable other Large Language Models, including open source LLMs such as Dolly.

We’ve previously saved an Azure OpenAI API key as a Databricks Secret so we can reference it with the SECRET function. With that stored, let’s take a look at the new AI_GENERATE_TEXT function to see how we make it work for our specific goal:

We suggest that you wrap the AI_GENERATE_TEXT function with another function. This makes it easier to pass along input data such as transcripts, and to name the function to make it more descriptive of the intended goal:

That's *all it takes* to achieve the functionality that we set out at the start, which leads to our query being as simple as:

No complicated pipelines, no filing tickets for data engineers to create new processes, or tickets for data scientists to create new models - all it takes is a bit of your creativity to develop the prompt and straightforward SQL to bring the incredible power of LLMs right to your data.

AI Functions lets you harness the power of Large Language Models - from translating from one language to another, summarizing text, suggesting next steps for support teams, or even using multiple function calls for multi-shot prompts.

AI Functions are just the start on our journey to empower users to easily customize LLMs to your business and use LLMs with your data. We can’t wait to see what you build!

Sign up for the Public Preview of AI Functions [here](https://forms.gle/pBTvFmrAzLLbjPyg7) and make sure to check out our Webinar covering how to build your own LLM like Dolly [here](https://www.databricks.com/resources/webinar/build-your-own-large-language-model-dolly)! For more details you can also read the docs [here](https://docs.databricks.com/sql/language-manual/functions/ai_generate_text.html).
