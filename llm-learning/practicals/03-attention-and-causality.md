# P03. Attention and causality

Inspect attention as a numerical mixture, then add visibility and position without conflating the three mechanisms.

**Prerequisites:** [Chapter 06](../chapters/06-attention-from-first-principles.md), [Chapter 07](../chapters/07-causality-heads-and-position.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. One head

Redo Chapter 06's worked value mixture on paper using different value vectors and the same scores. Explain which changes affect weights and which affect returned content.

## 2. Causal perturbation

```
python practicals/scripts/tensor_lab.py --topic attention --future-shift 3
python practicals/scripts/tensor_lab.py --topic attention --future-shift 3 --unmasked
```

Before each run, state what relationship you expect between the earlier output positions under a changed suffix. Record your confidence. The script uses synthetic hidden states, not token text. Inspect where the score mask is applied and which row/column axis represents queries/keys.

## 3. Head layout

On paper, split B x T x D into B x H x T x d_h for a divisible width. Trace the transpose needed before the score product and the inverse transpose before the output projection. Write what would be mixed if you accidentally swapped batch and head axes.

## 4. Position identity

```
python practicals/scripts/tensor_lab.py --topic positions
```

Derive the two-dimensional rotation identity first. Compare the two calculated dot products and report numerical error rather than claiming a measured language-model benefit. This exercise is independent of the running decoder's learned position table.

## 5. Rebuild

Write the boolean permitted-position matrix for a chunk with a cached prefix. Use absolute query/key indices. Keep this sketch for P11.


## Evidence to keep

Keep the score/weight/output shapes, both suffix-perturbation records, rotary algebra, and your cached-prefix mask sketch.

## Scope and next step

This isolates attention and position. It does not claim that one head corresponds to one semantic concept or that rotary positions establish unlimited context support.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
