# How to read this book

Read for a causal explanation, then use a practical to test that explanation on a small enough system to inspect.

## Reading a chapter

Read the chapter in sequence and follow its worked examples on paper. When a symbol first appears, record its meaning and shape. Use the numbered section headings to return to the specific step that needs another reading.

After reading, answer the chapter exercises without consulting the explanation. Then complete the associated practical at the checkpoint specified in its guide. A practical may span several chapters because it reuses a growing implementation. Record predictions before measurements and explain what the evidence supports afterward.

For revision, return to the chapter itself: reconstruct its central argument, redo a worked example with one changed input, and answer its exercises again. The assigned Stanford sections provide a second explanation of the same topic. There is no separate set of revision-note files.

## Prerequisites

Comfort with Python functions, lists, loops, and basic algebra is enough to start. Chapter 02 supplies the tensor/probability/gradient bridge. For a deeper introduction to optimization, use the concepts in [ML module 5](../ml-learning/m5-under-the-hood/README.md); retain that course's prediction and answer rules when working its labs. [ML module 6](../ml-learning/m6-deep-nets-on-a-mac/README.md) supplies training-dynamics context.

Do not open or search `ml-learning/answers/` to prepare this course. Do not edit that course's learner notes. Its practical results are not inputs to these chapters.

## One machine, bounded experiments

Start with synthetic tensors or a small public-domain text corpus. Before a training session, choose a maximum step count, context length, batch size, output path, and wall-time stop rule. A short run proves the pipeline works; a learning-curve investigation needs repeated held-out evaluations. Neither is evidence of frontier capability.

No course script downloads models or data. Tensor exercises need PyTorch already available in the interpreter you choose. The decoder accepts `cpu`, `mps`, or `cuda` explicitly and refuses an unavailable device. Use a device you have verified; do not infer it from another environment's package list. Keep artifacts outside the repo.

## Record keeping

Create your own work directory, for example `~/llm-data/work/`. Keep one experiment record per practical with these fields:

- Question and competing explanations.
- Prediction, including a range for a numeric claim or confidence for a choice.
- Dataset source, split boundaries, tokenizer, and model configuration.
- Command, seed, interpreter, device, and package versions.
- Observation, denominator, and any failed or interrupted runs.
- What you can conclude and one remaining uncertainty.

The chapters and practical guides are authored material; your experiment records belong in your own work directory.

## Reading at two depths

The main chapter is the required path. Advanced sections identify later extensions such as rotary position encoding, distributed sharding, direct preference optimization, and grouped-query attention. Understand the mechanism and its purpose before attempting their production implementations.

When a symbol appears, write its meaning and shape beside it. When a training trick appears, name the resource it saves and the new cost it adds. When a quality claim appears, ask which dataset, metric, baseline, and budget make it meaningful.

## Pace

A useful pace is two chapters and one practical each week, with additional practical sessions in the training and inference modules. Repeat a chapter if its prerequisite check fails. Use the chapter exercises to decide whether you can trace a token, a gradient, or a cached key through the code before continuing.
