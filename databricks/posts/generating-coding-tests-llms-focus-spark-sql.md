# Generating Coding Tests for LLMs: A Focus on Spark SQL

- Source: https://www.databricks.com/blog/generating-coding-tests-llms-focus-spark-sql
- Published: 2024-10-02
- Authors: Linqing Liu, Matthew Hayes, Ritendra Datta, Matei Zaharia
- Categories: engineering, data-engineering
- Images: 1 total, 0 extracted as architecture

## Introduction

Applying Large Language Models (LLMs) for code generation is becoming increasingly prevalent, as it helps you code faster and smarter. A primary concern with LLM-generated code is its correctness. Most open-source coding benchmarks are designed to evaluate general coding skills. But, in enterprise environments, the LLMs must be capable not only of general programming but also of utilizing domain-specific libraries and tools, such as MLflow and Spark SQL. Consequently, a challenge arises: **how can one systematically evaluate an LLM's proficiency in specialized coding libraries?**

In this blog post, we aim to tackle this challenge by **synthesizing tailored code tests for LLMs that are specific to any coding library.** These synthesized test cases provide a structured method to evaluate models, and thus help select the best model for a particular library. They also enable proficiency gain measurement with domain-specific fine-tuning.

We demonstrate how we synthesize code tests for Spark SQL, which have been integrated into our internal benchmarks to evaluate the model behind Databricks Assistant Autocomplete. Leveraging code documentation, which includes function names, definitions, and example code, we have developed a generalizable process for synthesizing highly targeted code tests.

Figure 1: Synthesized code tests for the array_except function. The left section displays the source information for the function, as documented in the [Spark SQL API](https://spark.apache.org/docs/latest/api/sql/). The right section displays two synthesized code tests. During evaluation, the model is prompted with the *context* on the right and is tasked with generating the appropriate code at the <here> placeholder. The synthesized code instruction is pivotal to the test, with the upper example being ideal due to its clear articulation of the code's purpose and required input data. In contrast, the lower example is problematic, as its comment is semantically ambiguous.

## Approach

Given the code documentation, our test case synthesis pipeline comprises the following key steps:

- **Seed Function Filtering:** Select qualified seed functions from the provided code documentation that meet the criteria for automated testing in our pipeline.
- **Code Instruction Generation:** Employ a state-of-the-art (SOTA) model to generate detailed code instructions (comments) based on the information provided for each function in the documentation.
 These instructions should clearly explain the functionality and specify the input data requirements.
- **Code Instruction Validation:** To ensure the reliability of the generated code instructions, a SOTA model is first employed to interpret them and *produce potential solutions*, with all relevant meta information provided to mitigate the model’s limitations. These *solutions are then executed,* and their results are compared against those of the original code snippet. This process verifies that the instructions accurately guide the generation of correct code. Any responses that result in different or unexpected outputs undergo manual verification to determine if they are of high quality despite the deviation. If not, they are filtered out to maintain the integrity of the testing process.

## Seed Function Filtering

For each function listed in the code documentation, the accompanying example is typically of high quality and makes it easy to understand its usage. However, not all functions are good candidates for automated testing. To qualify as a valid seed for test case generation, its example code must meet the following two criteria:

- **Deterministic Output:** The execution of the code must yield a deterministic output, which is crucial for subsequent validation steps. Functions that generate random or time-dependent results, such as `rand()` or `current_date()`, are deemed unsuitable due to their inherent unpredictability.
- **Compatibility with the Execution Environment:** The code must be executable within the required coding environment. For example, if the code needs to run in Databricks with Unity Catalog, avoid using functions that aren't supported in UC shared mode.

To verify, we execute each piece of example code in our target environment and record their outcomes. If the result aligns with that provided in the Reference API documentation, the function and code is retained, confirming its determinism. Conversely, if execution results in an error, the function is removed as a candidate for automated testing, indicating incompatibility with the execution environment. With this filtering step complete, we now have a set of functions that we know can be automatically tested and are executable in our desired environment.

## Code Instruction Generation

We now arrive at the core step in our automated test case generation: synthesizing instructions that, when followed, should yield code that produces the exact same execution results as the seed function’s example. We prompt a state-of-the-art (SOTA) code model to generate coding instructions corresponding to each seed function. The input to the model comprises the function name, its definition, and a single example code. The resulting code instruction is essentially a concise comment that explains the example code.

It is crucial to establish specific requirements in the prompt to guide the SOTA model’s output effectively so that the instruction is a reliable test of the model’s knowledge. In the prompt we instruct the SOTA model that:

- The comment should not mention the function name, but it should specify the input data if it is given in the example code.
- The comment should include sufficient detail so that the corresponding code can be identified solely based on the information provided in the comment.

This ensures that we don’t give away the solution in the comment, but at the same time the comment has enough information that a working example can be generated.

## Code Instruction Validation

The generated code instructions are integral to our test cases. To effectively evaluate the target model, these instructions serve as prompts and must explicitly articulate the function's purpose and the associated input data. Ambiguity undermines the accuracy of the model's output, as **clear guidance in instruction is crucial for correct code generation**. Below, we provide examples of code instructions that are considered inadequate:

To ascertain that the code instructions meet our standards, we employ the following validation process: We prompt a state-of-the-art (SOTA) code model with these instructions. The model is expected to **generate a corresponding solution, which is then executed.** If the output of the model's solution **matches the results of the seed code snippet**, the instruction is **retained**, confirming that it provides sufficient detail to facilitate accurate code generation.

One confounding factor might arise here: what if the SOTA model is not intelligent enough to solve the instruction? If the model fails to interpret the instructions adequately, it may not reflect the quality of the instructions but rather the limitations of the model. To mitigate this, we ensure that all necessary prior knowledge, including the function name and definition, is incorporated into the prompt. This approach allows the SOTA model to rely on the comprehensive information provided to generate a deterministic solution. Additionally, we manually review tests where the model-generated solution fails and retain those that are of high quality despite the failure.

## Code Model Evaluation

### Experiment Setting

We evaluate the model using an infilling mode, where the model fills in the middle (FIM) at a particular cursor position within a given context. The code preceding the cursor is referred to as the prefix, while the code following the cursor is known as the suffix. Typically, sentinel tokens are used to label these two segments, followed by another sentinel to request the code that fills in the middle. The prompt provided to the model is formatted as: "<fim_prefix>prefix code<fim_suffix>suffix code<fim_middle>". It's important to note that different models may use different sentinel tokens, and their infilling formats may also vary.

Our Spark SQL test synthesis pipeline yielded 286 test cases! We convert each test case generated using the above approach into a YAML format for execution using our evaluation benchmark. Each YAML file contains the following key elements:

- ***Name***: The function name we want to test. This is used to indicate the model’s performance on a specific function.
- ***Context***: This context will be transformed into the FIM format with the necessary sentinel tokens. "<here>" is a placeholder, which we will replace with the generated code for later evaluation. This representation enables us to easily adapt the test cases to different models using different FIM formats.
- ***Canonical solution***: The ground-truth solution, used as a reference check so we can validate that the test cases are well defined. Executing the benchmark with canonical solutions should yield a score of 100%.
- ***Test***: This includes an assertion check. We will execute the post-generated code in context and verify if the result matches the reference result.

### Evaluation Results

We report performance using the pass@1 metric (Chen et al., 2021), which measures the percentage of problems for which the model generates a correct solution in its first attempt. It indicates how often the model can successfully solve a coding problem with a single guess. For sampling, we employ nucleus sampling with top_p set to 0.95 and a temperature of 0.2. We evaluate several models within the 7 billion parameters range. To understand the SOTA performance of this benchmark, we also evaluate GPT-4o with greedy decoding.

| Models | pass@1 | Prompt format |
|---|---|---|
| StarCoder2-7B | 0.358 | <fim_prefix># Databricks notebook source # Transform the array [10, 20] into multiple rows df = spark.sql("<fim_suffix>") result = [item for row in df.collect() for item in row]<fim_middle> |
| deepseek-ai/deepseek-coder-6.7b-base | 0.528 | <｜fim▁begin｜># Databricks notebook source # Transform the array [10, 20] into multiple rows df = spark.sql("<｜fim▁hole｜>") result = [item for row in df.collect() for item in row]<｜fim▁end｜> |
| google/codegemma-7b | 0.470 | <|fim_prefix|># Databricks notebook source # Transform the array [10, 20] into multiple rows df = spark.sql("<|fim_suffix|>") result = [item for row in df.collect() for item in row]<|fim_middle|> |
| gpt-4o-2024-08-06 | 0.748 | - (We instruct the model to fill in the middle with the prompt) |

Table 1: Pass@k results of different LLMs on our SparkSQL Benchmark. We evaluate the models following their unique FIM format and special tokens.

During our model evaluations, we observed that including the line "# Databricks notebook source" at the beginning positively impacts the results. This line always appears at the top of a Databricks notebook and distinguishes it from a normal Python module or script. This effect is particularly pronounced for the StarCoder2-7B model. Without this line, the Pass@1 score drops significantly to 0.125. We hypothesize that this initial line acts as a hint, enabling the model to access essential knowledge about Spark SQL during inference that was acquired in a Databricks notebook context.

When analyzing the tests where the model fails most frequently, it’s notable that many of the failures arise from the model's inability to correctly identify and use the appropriate built-in functions. For instance, in Spark SQL, the “find_in_set” function is designed to return the index of a specific string within a comma-separated list, but the model often hallucinates it with the “position” function, which is intended to find the index of a substring within a target string. Additionally, the model sometimes overcomplicates code instructions by implementing them with complex nested subqueries, which can easily lead to errors, whereas the canonical solution could be achieved with a simple built-in function.

## Conclusion

We propose a method to synthesize code tests from the given documentation for any code library. Our test case synthesis pipeline involves the following steps: filtering seed functions from the documentation, generating detailed code instructions, and validating these instructions. To validate these instructions, we leverage them along with the function information as a hint to generate corresponding code solutions and then execute these solutions to check their correctness. This ensures the accuracy of the code instructions, guaranteeing their effectiveness in evaluating the model's coding capabilities. Finally, we utilize these test cases to assess various models in their infilling mode.

In this post, we demonstrate the most direct conversion of example code from documentation into code tests. Our approach can be extended to accommodate more complex test cases. For instance, if different input data is required, an additional step can be introduced after seed function filtering to modify the example code accordingly. More assertions with various conditions can be added too. In our current scenario, the target code is a single line; however, for multi-line code, a more detailed docstring, rather than a concise code comment, would be necessary. Additionally, preceding code can be used as context, instructing the model to generate only the specific targeted function line. Various modifications can be implemented to tailor the test cases to specific requirements. In our next post, we will discuss how to fine-tune the model so that it will perform better on this Spark SQL benchmark. Stay tuned!
