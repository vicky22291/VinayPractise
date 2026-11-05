# P01. Text to tokens

Trace text through bytes, learned merges, and ids before changing any model weights. After Chapter 01 do the paper lifecycle trace only; run BPE after Chapter 03.

**Prerequisites:** [Chapter 01](../chapters/01-what-a-language-model-learns.md), [Chapter 03](../chapters/03-text-bytes-and-tokenization.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Paper trace

Choose a short synthetic string containing repeated letters, a space, and a non-ASCII character. Write its visible characters, then its UTF-8 byte representation. State which part is a representation rule and which part BPE learns.

## 2. Inspect the algorithm

Read `ByteBPE.fit`, `replace_pair`, `encode`, and `decode`. Identify the pair tie-break, whether pair counting includes overlaps, and how replacement consumes a match. The fit accepts a list of documents so it does not create pair counts across document boundaries.

## 3. Run a baseline and one change

```
python practicals/scripts/tokenizer_lab.py --text 'abab café abab' --merges 0
python practicals/scripts/tokenizer_lab.py --text 'abab café abab' --merges 4
```

Log a prediction before each command. Explain the output using the actual learned pair list, not just a compressed length. Encode/decode the same string with both tokenizers and preserve the distinction between reversibility and equal token counts.

## 4. Coverage and compatibility

In a Python scratch file outside the repo, fit a tokenizer on one string and encode another containing an unseen Unicode character. Check the round-trip property. Then sketch why feeding a newly learned id above 255 into the byte decoder would require a different embedding/output contract.

## 5. Rebuild

Write a left-to-right `replace_pair` from memory for a synthetic integer list. Design a test where possible pair occurrences overlap. Compare with the visible teaching implementation only after writing your version.


## Evidence to keep

Keep your character/byte/id trace, both RESULT lines, the merge-table explanation, the round-trip check, and your rebuilt replacement function.

## Scope and next step

This experiment changes a tokenizer, not a saved model. The decoder will continue to use fixed byte ids. Move to P02 for embedding and loss shapes.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
