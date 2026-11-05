# P07. Precision and training memory

Separate numerical format, parameter-state storage, and activation/compute choices in one explicit resource ledger.

**Prerequisites:** [Chapter 13](../chapters/13-efficient-training-and-scaling.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Precision fixture

```
python practicals/scripts/tensor_lab.py --topic precision
```

Before running, distinguish exponent range and local precision in your prediction. Inspect the original synthetic values and what each cast reports. Do not extrapolate one cast fixture to a training-speed claim.

## 2. Memory ledger

Read the teaching decoder configuration and count shared embedding weights once. Build a ledger for parameter bytes, gradients, two optimizer moments, activations, and temporary buffers. State which terms are exact arithmetic and which need profiling. Repeat with a hypothetical storage dtype change without assuming optimizer buffers changed too.

## 3. Accumulation on paper and in scratch code

Create two synthetic microbatches with different supervised-token counts. Sum token losses and divide by the total count. Contrast that with an unweighted mean of microbatch means. If implementing a scratch backward comparison, use a deterministic linear model and the same complete token objective for both paths.

## 4. Name the bottleneck

For each hypothetical constraint, choose a candidate mechanism and a cost it adds: optimizer state too large, activations too large, device underutilized, or communication too large. Identify what data parallelism, sharding, checkpoint recomputation, or accumulation actually changes. The teaching script does not implement these distributed methods.

## 5. Optional measured extension

A real mixed-precision run requires a supported device/dtype path and an explicit quality/throughput comparison. Design that protocol first. Do not claim this practical already benchmarked it.


## Evidence to keep

Keep the cast result, parameter/memory arithmetic, correctly weighted microbatch objective, and a resource-to-mechanism decision table.

## Scope and next step

This practical demonstrates formats and accounting. It does not implement a fused attention kernel, FSDP, or a mixed-precision training benchmark. Continue to the adaptation objective in P08.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
