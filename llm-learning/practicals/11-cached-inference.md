# P11. Cached inference

Verify cached incremental computation against a complete forward pass before considering performance.

**Prerequisites:** [Chapter 18](../chapters/18-kv-caches-and-serving.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Position/mask sketch

Return to P03's cached-prefix sketch. For p previous keys and q current queries, write the permitted key range for each query. Trace the position offset in `Decoder.forward` and the causal mask in `Attention.forward`.

## 2. Structural comparison

```
python practicals/scripts/tiny_decoder.py --cache --checkpoint ~/llm-data/checkpoints/byte-a.pt --tokens 32 --device cpu
```

If you have not trained a checkpoint, omit `--checkpoint` for an explicitly synthetic untrained-model check. The function compares full-sequence logits with prefill plus incremental chunks. State a numerical tolerance before interpreting equality under floating-point arithmetic.

## 3. Cache ledger

Use the saved configuration, batch, token length, head count, and actual element size to reproduce the reported payload arithmetic. Count K and V at every layer. State which runtime allocations the payload excludes and how grouped-query attention would change the formula.

## 4. Boundary and timing

Inspect the explicit context-overflow refusal. This implementation has no silent sliding-window policy. If timing both paths in scratch code, include warmup, repeated trials, device synchronization, and the same prompts/output lengths. Record Python overhead and say why the result is not a service-level load test.

## 5. Serving design

Sketch admission, prefill, decode, completion, cancellation, and cache release for two variable-length requests. Identify first-token versus subsequent-token latency and the tenant-isolation boundary.


## Evidence to keep

Keep logit-comparison protocol, mask/position trace, payload arithmetic, overflow policy, and the serving sketch.

## Scope and next step

This checks one learned-position decoder. It does not implement continuous batching, paged allocation, shared-prefix authorization, or a production scheduler. Continue to the system boundary in P12.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
