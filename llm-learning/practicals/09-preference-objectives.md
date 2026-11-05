# P09. Preference objectives

Inspect a pairwise preference loss and its gradients without presenting a scalar example as a complete alignment run.

**Prerequisites:** [Chapter 16](../chapters/16-preferences-rewards-and-reasoning.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Define the pair

Read the chosen/rejected and reference log-probability constants in the `preferences` branch. On paper, form the model-relative preference margin. Write what each symbol would mean for an actual serialized response sequence.

## 2. Run and vary one coefficient

```
python practicals/scripts/tensor_lab.py --topic preferences --beta 0.5
python practicals/scripts/tensor_lab.py --topic preferences --beta 2
```

Predict the local gradient behavior before each run, then inspect the result. The scalar log probabilities are synthetic leaves, not outputs of a normalized language model. Explain why a real pair-training run still needs the entire sequence-model and data pipeline.

## 3. Reward design exercise

Propose a synthetic task whose score rewards an easily counted output feature. Write a response that satisfies the score and fails the intended task. Redesign the evaluation so this failure is visible. Do not turn a judge score into a universal truth definition.

## 4. Reasoning budget

Design a comparison between one attempt and several verified attempts. Record which resources grow, how the verifier can fail, and how to report a fair budget. State why a generated explanation does not establish an internal causal trace.


## Evidence to keep

Keep the margin derivation, local gradient records, list of missing pieces for real DPO, a reward-hacking counterexample, and the inference-budget comparison protocol.

## Scope and next step

No PPO, GRPO, reward-model fitting, or real DPO training occurs here. Move to P10 for representation compression, which changes a different part of the system.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
