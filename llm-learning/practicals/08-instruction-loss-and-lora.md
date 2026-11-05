# P08. Instruction loss and LoRA

Connect response-only supervision to a low-rank trainable update while keeping the objective and parameterization separate.

**Prerequisites:** [Chapter 14](../chapters/14-instruction-tuning-and-chat.md), [Chapter 15](../chapters/15-low-rank-adaptation.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Align the labels

Write the synthetic four-token conversation from Chapter 14. Shift the target ids and the target-role mask together. Identify the ignored prompt prediction and the scored response predictions before running:

```
python practicals/scripts/tensor_lab.py --topic instruction
```

Inspect the denominator and explain why ignored targets can remain in context. A chat-template convention is not established by arbitrary integer examples.

## 2. Low-rank mechanism

Read the `lora` branch of `tensor_lab.py`, then count A/B parameters and explain its zero-update initialization.

```
python practicals/scripts/tensor_lab.py --topic lora --rank 2 --steps 30 --seed 0
python practicals/scripts/tensor_lab.py --topic lora --rank 4 --steps 30 --seed 0
```

Log predictions before each run. The desired mapping, inputs, and optimizer are synthetic. A changed rank changes capacity and initialization dimensions; interpret that comparison accordingly. The base tensor remains frozen.

## 3. Rebuild and merge

In external scratch code, compute xW0-transpose plus the adapter path, then the merged-weight path for fixed A/B. Compare outputs under a specified dtype and tolerance. Explain which copies can be removed for inference and what base identity must accompany an adapter.

## 4. Optional real-model project

The existing ML course's lab 40 is a separate real-model learning exercise with its own prediction and answer rules. Follow those rules if you study it. A new real adapter project here needs a chosen compatible model/template, dataset, evaluation set, memory budget, and installed runtime. That extension is not implied by this linear-map exercise.


## Evidence to keep

Keep the shifted supervision mask, trainable/frozen parameter inventory, both fitting records, merge equivalence explanation, and a proposed real-model evaluation protocol.

## Scope and next step

This practical does not fine-tune an LLM or demonstrate QLoRA. Its numerical mechanism supports the later quantized-base explanation and the optional capstone extension.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
