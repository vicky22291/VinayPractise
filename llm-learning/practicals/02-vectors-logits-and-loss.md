# P02. Vectors, logits, and loss

Make the tensor and probability path visible in stages. Do the shape arithmetic after Chapter 02, embedding lookup after Chapter 04, and the loss/gradient calculation after Chapter 05.

**Prerequisites:** [Chapter 02](../chapters/02-tensors-probability-and-gradients.md), [Chapter 04](../chapters/04-embeddings-and-representations.md), [Chapter 05](../chapters/05-next-token-prediction-and-loss.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Shapes on paper

Choose B=2, T=5, D=8, and V=16. Write the shapes after embedding lookup and vocabulary projection. Distinguish PyTorch Linear's stored weight orientation from row-vector matrix notation.

## 2. Trace synthetic tensors

```
python practicals/scripts/tensor_lab.py --topic shapes
python practicals/scripts/tensor_lab.py --topic loss
```

Read the construction of the logits and target before running. Work the softmax denominator and one negative log probability by hand. Compare autograd's logit gradient with p minus the one-hot target. The script reports an algebraic consistency property as well as numbers.

## 3. Change one thing

Copy only the small synthetic loss example to your external scratch file. Change the observed target without changing logits. State which object changed and why the logits' shapes remain legal. Then add a constant to every logit and inspect whether the distribution identity holds numerically.

## 4. Numerical stability

Compare direct exponentiation with `log_softmax` on a deliberately large synthetic score vector. Record overflow/nonfinite behavior as an implementation observation. Do not confuse the demonstration with a realistic trained-model logit distribution.

## 5. Rebuild and explain

Write stable log-softmax using subtraction of the maximum and a log sum. State where its reduction axis belongs. Explain why gradients cannot validate an incorrectly shifted target dataset.


## Evidence to keep

Keep shape annotations, hand arithmetic, the exact target/logit changes, stable versus naive calculations, and an explanation of the objective/gradient distinction.

## Scope and next step

These are synthetic numerical examples. No trained-model quality is measured. Continue to P03 when queries, keys, values, and causal visibility have been introduced.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
