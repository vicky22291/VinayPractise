# P06. Honest evaluation

Turn a pair of checkpoints into a comparison with an explicit unit, denominator, and decision.

**Prerequisites:** [Chapter 12](../chapters/12-evaluating-models-and-experiments.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Define the claim

Choose the question before running: for example, compare two budgets for the same architecture on the same fixed held-out byte partition. State why that question is narrower than instruction following or factual reliability. Write a metric and the decision it will support.

## 2. Fixed evaluation

```
python practicals/scripts/tiny_decoder.py --evaluate --checkpoint ~/llm-data/checkpoints/byte-a.pt --text ~/ml-data/nanoGPT/data/shakespeare_char/input.txt --max-eval-windows 32 --device cpu
python practicals/scripts/tiny_decoder.py --evaluate --checkpoint ~/llm-data/checkpoints/byte-b.pt --text ~/ml-data/nanoGPT/data/shakespeare_char/input.txt --max-eval-windows 32 --device cpu
```

Record scored tokens, window count, natural-log NLL per byte, and the context-reset protocol. The code refuses a different corpus fingerprint. Explain why this protects one experiment identity without proving that the data is uncontaminated.

## 3. Variation and qualitative checks

If making a claim about training rather than just these checkpoints, repeat the chosen budgets with additional seeds and new output paths. Keep failed runs. Use a fixed sample prompt/decoding policy from P04 as a qualitative diagnostic, then identify what the likelihood metric misses.

## 4. Build a tiny rubric

Create a synthetic set of examples for a proposed downstream task. Name the input, acceptable answer, scoring rule, and failure category. Explain why the byte model's corpus does not automatically support this task. Keep these task questions separate from its language-model test suffix.

## 5. Explain the denominator

Work one unequal-batch token-loss aggregation on paper. State how a changed tokenizer or rolling-context evaluator would change the unit/question before comparing another number.


## Evidence to keep

Keep a paired checkpoint table with protocol fields, uncertainty notes, samples marked qualitative, and one next decision. Explicitly list claims not covered by the chosen metric.

## Scope and next step

The evaluator is fixed-window byte likelihood. It is not a benchmark harness for arbitrary chat models or a guarantee about truth. Efficiency experiments in P07 should preserve an interpretable quality comparison.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
