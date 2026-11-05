# P10. Quantization

Connect rounding and code packing to reconstruction error, metadata cost, and the limits of an inference claim.

**Prerequisites:** [Chapter 17](../chapters/17-quantization-and-qlora.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Hand quantization

Use a small synthetic vector and Q=7. Choose a scale, round/clamp codes, reconstruct values, and calculate one error. State whether clipping occurred before using the s/2 error bound. Include an all-zero group in your reasoning.

## 2. Representation comparison

```
python practicals/scripts/tensor_lab.py --topic quantization --bits 8 --group-size 16 --seed 0
python practicals/scripts/tensor_lab.py --topic quantization --bits 4 --group-size 16 --seed 0
```

The script physically packs four-bit codes, including a defined padding nibble for odd counts. Its scale metadata is FP32, so use 32/g rather than the chapter's illustrative FP16 16/g overhead when checking this implementation's ledger.

## 3. Range and grouping

```
python practicals/scripts/tensor_lab.py --topic quantization --bits 4 --group-size 64 --outlier 20 --seed 0
python practicals/scripts/tensor_lab.py --topic quantization --bits 4 --group-size 8 --outlier 20 --seed 0
```

Predict the competing effects on error and metadata before running. Keep data/seed fixed. Inspect exactly which weights share a scale. Rebuild the low/high-nibble unpacking operation in your own scratch code.

## 4. Model-level extension design

Propose an evaluation that would test a real quantized checkpoint's task quality and latency. Name compute dtype, weight format, scale grouping, cache dtype, kernel/runtime, prompt set, and decoding budget. Explain why the current reconstructed-vector calculation cannot establish any speed benefit.


## Evidence to keep

Keep hand codes and errors, packed/metadata byte counts, grouping comparison, and a model-level protocol. Distinguish packed storage from runtime memory.

## Scope and next step

The script uses symmetric uniform codes, not NF4 and not an optimized low-bit matmul. QLoRA requires a separate quantized-base training stack. P11 follows the context-memory allocation instead.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
