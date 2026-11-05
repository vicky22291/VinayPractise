# Course glossary

Definitions follow the course's conventions. The linked chapter supplies the mechanism, worked example, and limits.

| Term | Meaning | Chapter |
|---|---|---|
| Activation | An intermediate tensor calculated for a particular input, layer, and position. | [04](chapters/04-embeddings-and-representations.md) |
| Adapter | A compatible trainable addition to a base model, often saved separately from frozen base weights. | [15](chapters/15-low-rank-adaptation.md) |
| Attention | An input-dependent weighted mixture of value vectors, with weights derived from query/key scores. | [06](chapters/06-attention-from-first-principles.md) |
| Autoregressive | Factorizing a sequence into next-item predictions conditioned on previous items. | [01](chapters/01-what-a-language-model-learns.md) |
| Batch | Examples processed together; its axis is distinct from token positions and features. | [02](chapters/02-tensors-probability-and-gradients.md) |
| BF16 | A 16-bit floating-point format with an FP32-like exponent range and fewer significand bits. | [13](chapters/13-efficient-training-and-scaling.md) |
| BPE | Byte-pair encoding: an ordered learned merge procedure for adjacent symbols. | [03](chapters/03-text-bytes-and-tokenization.md) |
| Causal mask | A visibility rule that excludes future keys from a next-token position. | [07](chapters/07-causality-heads-and-position.md) |
| Chat template | Checkpoint-compatible serialization of messages, roles, boundaries, and output prefix. | [14](chapters/14-instruction-tuning-and-chat.md) |
| Checkpoint | Model weights plus configuration and, for resume, optimizer/data/random state. | [11](chapters/11-training-a-small-language-model.md) |
| Context | The supplied token prefix available to a request, within the model/runtime limits. | [01](chapters/01-what-a-language-model-learns.md) |
| Cross-entropy | For an observed target, the negative log probability assigned to it. | [05](chapters/05-next-token-prediction-and-loss.md) |
| Decode | Select continuation tokens from model logits under a chosen policy. | [09](chapters/09-generating-text.md) |
| DPO | Direct preference optimization: a reference-relative pairwise response objective. | [16](chapters/16-preferences-rewards-and-reasoning.md) |
| Embedding | A trainable vector indexed by a discrete id; not the same object as every contextual hidden state. | [04](chapters/04-embeddings-and-representations.md) |
| Evaluation split | Examples withheld under an explicit sampling/boundary protocol for assessing a defined claim. | [10](chapters/10-building-the-pretraining-dataset.md) |
| Fine-tuning | Optimization of selected model parameters on additional examples or objectives. | [14](chapters/14-instruction-tuning-and-chat.md) |
| FLOP | A floating-point operation; estimated FLOPs are not measured wall time. | [13](chapters/13-efficient-training-and-scaling.md) |
| Gradient | Local derivative of a scalar objective with respect to a parameter tensor. | [02](chapters/02-tensors-probability-and-gradients.md) |
| Grouped-query attention | An attention architecture with fewer key/value heads shared among more query heads. | [18](chapters/18-kv-caches-and-serving.md) |
| GRPO | Group relative policy optimization: policy training using relative reward information within response groups. | [16](chapters/16-preferences-rewards-and-reasoning.md) |
| Hidden state | A contextual activation vector at one layer and position. | [04](chapters/04-embeddings-and-representations.md) |
| Inference | Use of model weights to calculate outputs, normally without weight updates. | [01](chapters/01-what-a-language-model-learns.md) |
| KV cache | Saved per-layer keys and values for the same causal prefix during incremental inference. | [18](chapters/18-kv-caches-and-serving.md) |
| LayerNorm | Per-position normalization over feature coordinates, with learned affine parameters. | [08](chapters/08-the-decoder-transformer.md) |
| Logit | An unrestricted vocabulary score before softmax. | [05](chapters/05-next-token-prediction-and-loss.md) |
| LoRA | Low-rank adaptation: a frozen base matrix plus a trainable factorized additive update. | [15](chapters/15-low-rank-adaptation.md) |
| Loss mask | A choice of target positions that contribute to the optimization objective. | [05](chapters/05-next-token-prediction-and-loss.md) |
| MLP | A multilayer perceptron; a decoder feed-forward sublayer transforms features per position. | [08](chapters/08-the-decoder-transformer.md) |
| NF4 | A non-uniform four-bit weight format associated with a roughly normal weight-distribution assumption. | [17](chapters/17-quantization-and-qlora.md) |
| Perplexity | The exponential of mean natural-log negative likelihood per defined token unit. | [12](chapters/12-evaluating-models-and-experiments.md) |
| Prefill | Processing prompt positions before incremental output decoding. | [18](chapters/18-kv-caches-and-serving.md) |
| Pretraining | Broad corpus optimization that produces base-model parameters, commonly using next-token learning. | [11](chapters/11-training-a-small-language-model.md) |
| PPO | Proximal policy optimization: a policy-gradient family using constraints such as clipped probability ratios. | [16](chapters/16-preferences-rewards-and-reasoning.md) |
| QLoRA | Low-rank adaptation with a frozen quantized base and a compatible reconstruction/compute training path. | [17](chapters/17-quantization-and-qlora.md) |
| Quantization | Mapping values to finite codes and reconstruction metadata. | [17](chapters/17-quantization-and-qlora.md) |
| RAG | Retrieval-augmented generation: insert selected external evidence into model context. | [19](chapters/19-retrieval-tools-and-compound-systems.md) |
| Residual connection | An identity path added to a learned sublayer update. | [08](chapters/08-the-decoder-transformer.md) |
| RoPE | Rotary position embeddings: position-dependent coordinate rotations of queries and keys. | [07](chapters/07-causality-heads-and-position.md) |
| SFT | Supervised fine-tuning on desired outputs under a defined serialization and loss mask. | [14](chapters/14-instruction-tuning-and-chat.md) |
| Softmax | Normalization of real scores into a categorical distribution by exponentiation and division by their sum. | [05](chapters/05-next-token-prediction-and-loss.md) |
| Temperature | A positive scaling divisor on logits used in a sampling policy. | [09](chapters/09-generating-text.md) |
| Token | A vocabulary item represented by an integer id; it need not be a whole word or character. | [03](chapters/03-text-bytes-and-tokenization.md) |
| Weight tying | Reusing a parameter table, such as input embeddings, for the output projection. | [04](chapters/04-embeddings-and-representations.md) |
