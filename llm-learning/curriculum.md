# Contents

The twenty chapters retain their current depth. They are arranged into six parts, with numbered sections, worked examples, exercises, and further reading. Follow the chapter order for the first reading; use the section links to return to a particular mechanism.

## Part I. Representing language

The opening chapters define the object being modeled and the numerical representation used to calculate its predictions. Text becomes bytes and token ids; token ids select learned vectors.

### [01. What a language model learns](chapters/01-what-a-language-model-learns.md)

- [1.1 A probability model of sequences](chapters/01-what-a-language-model-learns.md#11-a-probability-model-of-sequences)
- [1.2 Four objects that are often confused](chapters/01-what-a-language-model-learns.md#12-four-objects-that-are-often-confused)
- [1.3 Training and inference are different computations](chapters/01-what-a-language-model-learns.md#13-training-and-inference-are-different-computations)
- [1.4 Worked sequence: one model, two decoding choices](chapters/01-what-a-language-model-learns.md#14-worked-sequence-one-model-two-decoding-choices)
- [1.5 What we will build and what it can teach](chapters/01-what-a-language-model-learns.md#15-what-we-will-build-and-what-it-can-teach)
- [1.6 Exercises](chapters/01-what-a-language-model-learns.md#16-exercises)
- [1.7 Further reading](chapters/01-what-a-language-model-learns.md#17-further-reading)

### [02. Tensors, probability, and gradients](chapters/02-tensors-probability-and-gradients.md)

- [2.1 Shape is part of the meaning](chapters/02-tensors-probability-and-gradients.md#21-shape-is-part-of-the-meaning)
- [2.2 Dot products and learned transformations](chapters/02-tensors-probability-and-gradients.md#22-dot-products-and-learned-transformations)
- [2.3 Probabilities and log probabilities](chapters/02-tensors-probability-and-gradients.md#23-probabilities-and-log-probabilities)
- [2.4 Gradients tell us how a scalar objective changes](chapters/02-tensors-probability-and-gradients.md#24-gradients-tell-us-how-a-scalar-objective-changes)
- [2.5 Numerical checks and limitations](chapters/02-tensors-probability-and-gradients.md#25-numerical-checks-and-limitations)
- [2.6 Exercises](chapters/02-tensors-probability-and-gradients.md#26-exercises)
- [2.7 Further reading](chapters/02-tensors-probability-and-gradients.md#27-further-reading)

### [03. Text, bytes, and tokenization](chapters/03-text-bytes-and-tokenization.md)

- [3.1 Why a model needs a vocabulary](chapters/03-text-bytes-and-tokenization.md#31-why-a-model-needs-a-vocabulary)
- [3.2 Byte-pair encoding as a learned compression rule](chapters/03-text-bytes-and-tokenization.md#32-byte-pair-encoding-as-a-learned-compression-rule)
- [3.3 Training a tokenizer and using it are separate stages](chapters/03-text-bytes-and-tokenization.md#33-training-a-tokenizer-and-using-it-are-separate-stages)
- [3.4 A vocabulary change is a model change](chapters/03-text-bytes-and-tokenization.md#34-a-vocabulary-change-is-a-model-change)
- [3.5 Data hygiene starts before the model](chapters/03-text-bytes-and-tokenization.md#35-data-hygiene-starts-before-the-model)
- [3.6 Exercises](chapters/03-text-bytes-and-tokenization.md#36-exercises)
- [3.7 Further reading](chapters/03-text-bytes-and-tokenization.md#37-further-reading)

### [04. Embeddings and representations](chapters/04-embeddings-and-representations.md)

- [4.1 An id selects a trainable row](chapters/04-embeddings-and-representations.md#41-an-id-selects-a-trainable-row)
- [4.2 Worked lookup and parameter cost](chapters/04-embeddings-and-representations.md#42-worked-lookup-and-parameter-cost)
- [4.3 Static lookup and contextual representation](chapters/04-embeddings-and-representations.md#43-static-lookup-and-contextual-representation)
- [4.4 Position must enter somewhere](chapters/04-embeddings-and-representations.md#44-position-must-enter-somewhere)
- [4.5 Reading out vocabulary scores](chapters/04-embeddings-and-representations.md#45-reading-out-vocabulary-scores)
- [4.6 Exercises](chapters/04-embeddings-and-representations.md#46-exercises)
- [4.7 Further reading](chapters/04-embeddings-and-representations.md#47-further-reading)

## Part II. The autoregressive transformer

The next-token objective defines what the network must predict. Attention, causal visibility, position, and decoder blocks supply the computation. Generation then uses the resulting distributions one token at a time.

### [05. Next-token prediction and loss](chapters/05-next-token-prediction-and-loss.md)

- [5.1 The target is one position to the right](chapters/05-next-token-prediction-and-loss.md#51-the-target-is-one-position-to-the-right)
- [5.2 From logits to a distribution](chapters/05-next-token-prediction-and-loss.md#52-from-logits-to-a-distribution)
- [5.3 Cross-entropy and its gradient](chapters/05-next-token-prediction-and-loss.md#53-cross-entropy-and-its-gradient)
- [5.4 Three masks with different jobs](chapters/05-next-token-prediction-and-loss.md#54-three-masks-with-different-jobs)
- [5.5 What likelihood does and does not tell us](chapters/05-next-token-prediction-and-loss.md#55-what-likelihood-does-and-does-not-tell-us)
- [5.6 Exercises](chapters/05-next-token-prediction-and-loss.md#56-exercises)
- [5.7 Further reading](chapters/05-next-token-prediction-and-loss.md#57-further-reading)

### [06. Attention from first principles](chapters/06-attention-from-first-principles.md)

- [6.1 Why token lookup alone is insufficient](chapters/06-attention-from-first-principles.md#61-why-token-lookup-alone-is-insufficient)
- [6.2 A worked mixture](chapters/06-attention-from-first-principles.md#62-a-worked-mixture)
- [6.3 What the scaling factor addresses](chapters/06-attention-from-first-principles.md#63-what-the-scaling-factor-addresses)
- [6.4 Self-attention and cross-attention](chapters/06-attention-from-first-principles.md#64-self-attention-and-cross-attention)
- [6.5 Costs and interpretive limits](chapters/06-attention-from-first-principles.md#65-costs-and-interpretive-limits)
- [6.6 Exercises](chapters/06-attention-from-first-principles.md#66-exercises)
- [6.7 Further reading](chapters/06-attention-from-first-principles.md#67-further-reading)

### [07. Causality, heads, and position](chapters/07-causality-heads-and-position.md)

- [7.1 Causality is an information boundary](chapters/07-causality-heads-and-position.md#71-causality-is-an-information-boundary)
- [7.2 Masking details that matter](chapters/07-causality-heads-and-position.md#72-masking-details-that-matter)
- [7.3 Multiple heads](chapters/07-causality-heads-and-position.md#73-multiple-heads)
- [7.4 Why position changes attention](chapters/07-causality-heads-and-position.md#74-why-position-changes-attention)
- [7.5 Trade-offs and the next construction](chapters/07-causality-heads-and-position.md#75-trade-offs-and-the-next-construction)
- [7.6 Exercises](chapters/07-causality-heads-and-position.md#76-exercises)
- [7.7 Further reading](chapters/07-causality-heads-and-position.md#77-further-reading)

### [08. The decoder transformer](chapters/08-the-decoder-transformer.md)

- [8.1 From attention to a full block](chapters/08-the-decoder-transformer.md#81-from-attention-to-a-full-block)
- [8.2 What residual connections preserve](chapters/08-the-decoder-transformer.md#82-what-residual-connections-preserve)
- [8.3 Layer normalization and feed-forward transformation](chapters/08-the-decoder-transformer.md#83-layer-normalization-and-feed-forward-transformation)
- [8.4 Parameter and activation accounting](chapters/08-the-decoder-transformer.md#84-parameter-and-activation-accounting)
- [8.5 The educational implementation's boundary](chapters/08-the-decoder-transformer.md#85-the-educational-implementations-boundary)
- [8.6 Exercises](chapters/08-the-decoder-transformer.md#86-exercises)
- [8.7 Further reading](chapters/08-the-decoder-transformer.md#87-further-reading)

### [09. Generating text](chapters/09-generating-text.md)

- [9.1 The generation loop](chapters/09-generating-text.md#91-the-generation-loop)
- [9.2 Greedy decoding and temperature](chapters/09-generating-text.md#92-greedy-decoding-and-temperature)
- [9.3 Restricting the candidate set](chapters/09-generating-text.md#93-restricting-the-candidate-set)
- [9.4 Context conditioning versus weight updates](chapters/09-generating-text.md#94-context-conditioning-versus-weight-updates)
- [9.5 Reproducibility and interpretation](chapters/09-generating-text.md#95-reproducibility-and-interpretation)
- [9.6 Exercises](chapters/09-generating-text.md#96-exercises)
- [9.7 Further reading](chapters/09-generating-text.md#97-further-reading)

## Part III. Data, optimization, and evaluation

The complete decoder becomes an experiment: a versioned corpus supplies training examples, optimization changes parameters, and held-out evidence determines what the run established.

### [10. Building the pretraining dataset](chapters/10-building-the-pretraining-dataset.md)

- [10.1 The corpus is part of the experiment](chapters/10-building-the-pretraining-dataset.md#101-the-corpus-is-part-of-the-experiment)
- [10.2 Split before making overlapping windows](chapters/10-building-the-pretraining-dataset.md#102-split-before-making-overlapping-windows)
- [10.3 Cleaning changes the distribution](chapters/10-building-the-pretraining-dataset.md#103-cleaning-changes-the-distribution)
- [10.4 Packing and boundaries](chapters/10-building-the-pretraining-dataset.md#104-packing-and-boundaries)
- [10.5 Versioning the data path](chapters/10-building-the-pretraining-dataset.md#105-versioning-the-data-path)
- [10.6 Exercises](chapters/10-building-the-pretraining-dataset.md#106-exercises)
- [10.7 Further reading](chapters/10-building-the-pretraining-dataset.md#107-further-reading)

### [11. Training a small language model](chapters/11-training-a-small-language-model.md)

- [11.1 One update, in order](chapters/11-training-a-small-language-model.md#111-one-update-in-order)
- [11.2 AdamW, learning rate, and accumulation](chapters/11-training-a-small-language-model.md#112-adamw-learning-rate-and-accumulation)
- [11.3 Training mode and gradient recording](chapters/11-training-a-small-language-model.md#113-training-mode-and-gradient-recording)
- [11.4 Worked update on one scalar](chapters/11-training-a-small-language-model.md#114-worked-update-on-one-scalar)
- [11.5 Checkpoints and resume](chapters/11-training-a-small-language-model.md#115-checkpoints-and-resume)
- [11.6 Exercises](chapters/11-training-a-small-language-model.md#116-exercises)
- [11.7 Further reading](chapters/11-training-a-small-language-model.md#117-further-reading)

### [12. Evaluating models and experiments](chapters/12-evaluating-models-and-experiments.md)

- [12.1 Define the claim before the metric](chapters/12-evaluating-models-and-experiments.md#121-define-the-claim-before-the-metric)
- [12.2 Token-weighted likelihood](chapters/12-evaluating-models-and-experiments.md#122-token-weighted-likelihood)
- [12.3 Tokenizers define the metric unit](chapters/12-evaluating-models-and-experiments.md#123-tokenizers-define-the-metric-unit)
- [12.4 Fair comparisons and uncertainty](chapters/12-evaluating-models-and-experiments.md#124-fair-comparisons-and-uncertainty)
- [12.5 Human and model-based judges](chapters/12-evaluating-models-and-experiments.md#125-human-and-model-based-judges)
- [12.6 From evaluation to the next decision](chapters/12-evaluating-models-and-experiments.md#126-from-evaluation-to-the-next-decision)
- [12.7 Exercises](chapters/12-evaluating-models-and-experiments.md#127-exercises)
- [12.8 Further reading](chapters/12-evaluating-models-and-experiments.md#128-further-reading)

## Part IV. Training efficiency and model adaptation

With an evaluation protocol in place, the text examines resource constraints, instruction data, low-rank updates, and preference or reward objectives. These methods change different parts of the training system.

### [13. Efficient training and scaling](chapters/13-efficient-training-and-scaling.md)

- [13.1 First name the scarce resource](chapters/13-efficient-training-and-scaling.md#131-first-name-the-scarce-resource)
- [13.2 Floating-point formats and mixed precision](chapters/13-efficient-training-and-scaling.md#132-floating-point-formats-and-mixed-precision)
- [13.3 Activation memory and gradient accumulation](chapters/13-efficient-training-and-scaling.md#133-activation-memory-and-gradient-accumulation)
- [13.4 Data parallelism and sharding](chapters/13-efficient-training-and-scaling.md#134-data-parallelism-and-sharding)
- [13.5 Scaling laws and compute budgets](chapters/13-efficient-training-and-scaling.md#135-scaling-laws-and-compute-budgets)
- [13.6 Exercises](chapters/13-efficient-training-and-scaling.md#136-exercises)
- [13.7 Further reading](chapters/13-efficient-training-and-scaling.md#137-further-reading)

### [14. Instruction tuning and chat](chapters/14-instruction-tuning-and-chat.md)

- [14.1 The same predictor, a different training distribution](chapters/14-instruction-tuning-and-chat.md#141-the-same-predictor-a-different-training-distribution)
- [14.2 Serialization is part of the model contract](chapters/14-instruction-tuning-and-chat.md#142-serialization-is-part-of-the-model-contract)
- [14.3 Which tokens are supervised?](chapters/14-instruction-tuning-and-chat.md#143-which-tokens-are-supervised)
- [14.4 Data quality and held-out tasks](chapters/14-instruction-tuning-and-chat.md#144-data-quality-and-held-out-tasks)
- [14.5 Behavior is not a factual guarantee](chapters/14-instruction-tuning-and-chat.md#145-behavior-is-not-a-factual-guarantee)
- [14.6 Exercises](chapters/14-instruction-tuning-and-chat.md#146-exercises)
- [14.7 Further reading](chapters/14-instruction-tuning-and-chat.md#147-further-reading)

### [15. Low-rank adaptation](chapters/15-low-rank-adaptation.md)

- [15.1 An update with fewer degrees of freedom](chapters/15-low-rank-adaptation.md#151-an-update-with-fewer-degrees-of-freedom)
- [15.2 Worked parameter count](chapters/15-low-rank-adaptation.md#152-worked-parameter-count)
- [15.3 Rank, target modules, and objective are separate choices](chapters/15-low-rank-adaptation.md#153-rank-target-modules-and-objective-are-separate-choices)
- [15.4 Deployment and compatibility](chapters/15-low-rank-adaptation.md#154-deployment-and-compatibility)
- [15.5 The useful decision](chapters/15-low-rank-adaptation.md#155-the-useful-decision)
- [15.6 Exercises](chapters/15-low-rank-adaptation.md#156-exercises)
- [15.7 Further reading](chapters/15-low-rank-adaptation.md#157-further-reading)

### [16. Preferences, rewards, and reasoning](chapters/16-preferences-rewards-and-reasoning.md)

- [16.1 Feedback changes the objective](chapters/16-preferences-rewards-and-reasoning.md#161-feedback-changes-the-objective)
- [16.2 A reference policy constrains drift](chapters/16-preferences-rewards-and-reasoning.md#162-a-reference-policy-constrains-drift)
- [16.3 Direct preference optimization](chapters/16-preferences-rewards-and-reasoning.md#163-direct-preference-optimization)
- [16.4 Reasoning and inference-time computation](chapters/16-preferences-rewards-and-reasoning.md#164-reasoning-and-inference-time-computation)
- [16.5 Reward hacking and evaluation](chapters/16-preferences-rewards-and-reasoning.md#165-reward-hacking-and-evaluation)
- [16.6 Exercises](chapters/16-preferences-rewards-and-reasoning.md#166-exercises)
- [16.7 Further reading](chapters/16-preferences-rewards-and-reasoning.md#167-further-reading)

## Part V. Compression and inference

Quantization changes numerical representation. KV caching changes which previous computations are retained. Both must be understood in terms of their exact resource costs and their effects on outputs.

### [17. Quantization and QLoRA](chapters/17-quantization-and-qlora.md)

- [17.1 Precision is a design choice](chapters/17-quantization-and-qlora.md#171-precision-is-a-design-choice)
- [17.2 Symmetric uniform quantization](chapters/17-quantization-and-qlora.md#172-symmetric-uniform-quantization)
- [17.3 Asymmetric, per-channel, and grouped formats](chapters/17-quantization-and-qlora.md#173-asymmetric-per-channel-and-grouped-formats)
- [17.4 Bits, packing, and actual memory](chapters/17-quantization-and-qlora.md#174-bits-packing-and-actual-memory)
- [17.5 Quantization error and task quality](chapters/17-quantization-and-qlora.md#175-quantization-error-and-task-quality)
- [17.6 Where QLoRA fits](chapters/17-quantization-and-qlora.md#176-where-qlora-fits)
- [17.7 Exercises](chapters/17-quantization-and-qlora.md#177-exercises)
- [17.8 Further reading](chapters/17-quantization-and-qlora.md#178-further-reading)

### [18. KV caches and serving](chapters/18-kv-caches-and-serving.md)

- [18.1 Prefill and decode do different work](chapters/18-kv-caches-and-serving.md#181-prefill-and-decode-do-different-work)
- [18.2 Position and visibility are correctness conditions](chapters/18-kv-caches-and-serving.md#182-position-and-visibility-are-correctness-conditions)
- [18.3 Worked cache ledger](chapters/18-kv-caches-and-serving.md#183-worked-cache-ledger)
- [18.4 Serving several requests](chapters/18-kv-caches-and-serving.md#184-serving-several-requests)
- [18.5 What the practical establishes](chapters/18-kv-caches-and-serving.md#185-what-the-practical-establishes)
- [18.6 Exercises](chapters/18-kv-caches-and-serving.md#186-exercises)
- [18.7 Further reading](chapters/18-kv-caches-and-serving.md#187-further-reading)

## Part VI. The surrounding system and its interpretation

The final part places the model inside retrieval and tool workflows, then examines what internal observations and interventions can establish. The capstone joins the chapter artifacts into one investigation.

### [19. Retrieval, tools, and compound systems](chapters/19-retrieval-tools-and-compound-systems.md)

- [19.1 A model is one component](chapters/19-retrieval-tools-and-compound-systems.md#191-a-model-is-one-component)
- [19.2 Retrieval has its own pipeline](chapters/19-retrieval-tools-and-compound-systems.md#192-retrieval-has-its-own-pipeline)
- [19.3 An evidence-bearing prompt](chapters/19-retrieval-tools-and-compound-systems.md#193-an-evidence-bearing-prompt)
- [19.4 Evaluate components and end-to-end behavior](chapters/19-retrieval-tools-and-compound-systems.md#194-evaluate-components-and-end-to-end-behavior)
- [19.5 The design decision](chapters/19-retrieval-tools-and-compound-systems.md#195-the-design-decision)
- [19.6 Exercises](chapters/19-retrieval-tools-and-compound-systems.md#196-exercises)
- [19.7 Further reading](chapters/19-retrieval-tools-and-compound-systems.md#197-further-reading)

### [20. Interpretability and the capstone](chapters/20-interpretability-and-the-capstone.md)

- [20.1 Return to the original question](chapters/20-interpretability-and-the-capstone.md#201-return-to-the-original-question)
- [20.2 Parameters, activations, and candidate features](chapters/20-interpretability-and-the-capstone.md#202-parameters-activations-and-candidate-features)
- [20.3 Interventions strengthen a hypothesis](chapters/20-interpretability-and-the-capstone.md#203-interventions-strengthen-a-hypothesis)
- [20.4 Attention and explanations are partial observations](chapters/20-interpretability-and-the-capstone.md#204-attention-and-explanations-are-partial-observations)
- [20.5 Assemble the capstone evidence](chapters/20-interpretability-and-the-capstone.md#205-assemble-the-capstone-evidence)
- [20.6 What completion means](chapters/20-interpretability-and-the-capstone.md#206-what-completion-means)
- [20.7 Exercises](chapters/20-interpretability-and-the-capstone.md#207-exercises)
- [20.8 Further reading](chapters/20-interpretability-and-the-capstone.md#208-further-reading)

## Practical sequence

The [practical index](practicals/README.md#practical-index) connects the reading to twelve exercises. P01 establishes the text representation; P02 and P03 expose the numerical mechanisms; P04 reads the complete decoder; P05 and P06 train and evaluate it. P07 to P10 investigate precision, adaptation objectives, and quantization. P11 verifies cached inference, and P12 develops the surrounding evidence and system boundary.

The BPE tokenizer exercise remains separate from the fixed-byte decoder checkpoint. Changing the tokenizer requires a compatible vocabulary and model; it is not an interchangeable preprocessing switch.

## Stanford reading and course coverage

The [source map](sources.md#chapter-reading-map) assigns recording sections to chapters. It preserves the latest CME295 edition in required reading, identifies absent course lectures, and distinguishes lecture-supported topics from authored supplements. The eight CME296 diffusion and vision lectures form a separate elective after the LLM core.

## Back matter

- [Glossary](glossary.md)
- [Transcript inventory and chapter reading map](sources.md)
- [Capstone](capstone.md)
- [Reading guide](study-guide.md)
