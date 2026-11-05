# P04. Decoder and generation

Connect the chapter diagrams to a complete decoder, then inspect generation from explicit random weights before revisiting it after training.

**Prerequisites:** [Chapter 08](../chapters/08-the-decoder-transformer.md), [Chapter 09](../chapters/09-generating-text.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Code reading

Open `tiny_decoder.py`. Trace `Decoder.forward`, `Block.forward`, and `Attention.forward`. Annotate the token table, position table, residual routes, normalization axis, head transpose, causal mask, and tied output weight. List the advanced features this implementation omits.

```
python practicals/scripts/tiny_decoder.py --smoke
```

The verdict is a structural check, not evidence of language capability.

## 2. Explicit untrained generation

After Chapter 09, compare these policies using the same synthetic random checkpoint construction:

```
python practicals/scripts/tiny_decoder.py --generate --untrained --prompt 'The ' --temperature 0 --max-new-tokens 16 --seed 0
python practicals/scripts/tiny_decoder.py --generate --untrained --prompt 'The ' --temperature 0.8 --top-k 8 --max-new-tokens 16 --seed 0
```

Log hypotheses about selection, not about grammatical quality. Read both displayed text and raw byte ids. Explain replacement characters using the byte-level output representation.

## 3. Paper decoding

Take a three-logit synthetic vector. Compute two positive-temperature distributions, greedy selection, and a top-k candidate set. State a stop policy. Do not let a long generated sample substitute for this numerical explanation.

## 4. Revisit after P05

Repeat generation with `--checkpoint ~/llm-data/checkpoints/byte-a.pt`, dropping `--untrained`. Keep prompt bytes, output budget, seed, and sampling policy fixed. Use the trained model's held-out metric as separate evidence from qualitative samples.


## Evidence to keep

Keep a code-to-diagram annotation, the decoding protocol, raw-byte interpretation, hand probabilities, and the later trained-checkpoint comparison.

## Scope and next step

There is no end token in this byte model, and its entire prompt plus output must fit the configured context. Continue to P05 to train the model instead of expecting competence from random weights.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
