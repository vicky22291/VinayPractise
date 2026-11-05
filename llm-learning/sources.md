# Transcript inventory and chapter reading map

The transcript archive remains outside this repo. Links below are relative to its current location under `~/stocks/data/transcripts/`. The source videos are also linked so this index remains interpretable away from this workstation. Cleaned English transcripts can omit timestamps, figures, equations, or speaker corrections; this course derives its worked mathematics explicitly and does not treat transcription as a technical specification.

**Inventory:** 30 English outputs, each matching a raw filename. Required LLM/NLP selection: 13 recordings. Elective vision selection: 8 recordings. Older CME295 edition excluded from the required sequence: 9 recordings. No raw file is deleted or renamed.

## Required LLM and NLP sources

| ID | Recording | English transcript | Video |
|---|---|---|---|
| S01 | Stanford CME295 Transformers & LLMs  /  Autumn 2026  /  Lecture 1 - Transformers | [Read](../../../stocks/data/transcripts/translated/stanford-online/114i2Kz-LZA_stanford-cme295-transformers-llms-autumn-2026-lect.md) | [YouTube](https://www.youtube.com/watch?v=114i2Kz-LZA) |
| S02 | Stanford CME295 Transformers & LLMs  /  Autumn 2026  /  Lecture 2 - Large Language Models | [Read](../../../stocks/data/transcripts/translated/stanford-online/GaIeu3npx04_stanford-cme295-transformers-llms-autumn-2026-lect.md) | [YouTube](https://www.youtube.com/watch?v=GaIeu3npx04) |
| S03 | Stanford CS336 Language Modeling from Scratch  /  Spring 2025  /  Lecture 1: Overview and Tokenization | [Read](../../../stocks/data/transcripts/translated/stanford-online/SQ3fZ1sAqXI_stanford-cs336-language-modeling-from-scratch-spri.md) | [YouTube](https://www.youtube.com/watch?v=SQ3fZ1sAqXI) |
| S04 | Stanford CS229 I Machine Learning I Building Large Language Models (LLMs) | [Read](../../../stocks/data/transcripts/translated/stanford-online/9vM4p9NN0Ts_stanford-cs229-i-machine-learning-i-building-large.md) | [YouTube](https://www.youtube.com/watch?v=9vM4p9NN0Ts) |
| S05 | Stanford CME295 Transformers & LLMs  /  Autumn 2026  /  Lecture 3 - LLM training | [Read](../../../stocks/data/transcripts/translated/stanford-online/S3bCDcJhz4s_stanford-cme295-transformers-llms-autumn-2026-lect.md) | [YouTube](https://www.youtube.com/watch?v=S3bCDcJhz4s) |
| S06 | Stanford CS224N: NLP w/ DL  /  Spring 2024  /  Lecture 7 - Attention, Final Projects and LLM Intro | [Read](../../../stocks/data/transcripts/translated/stanford-online/J7ruSOIzhrE_stanford-cs224n-nlp-w-dl-spring-2024-lecture-7---a.md) | [YouTube](https://www.youtube.com/watch?v=J7ruSOIzhrE) |
| S07 | Stanford CS224N: NLP with Deep Learning  /  Spring 2024  /  Lecture 10 - Post-training by Archit Sharma | [Read](../../../stocks/data/transcripts/translated/stanford-online/35X6zlhoCy4_stanford-cs224n-nlp-with-deep-learning-spring-2024.md) | [YouTube](https://www.youtube.com/watch?v=35X6zlhoCy4) |
| S08 | Stanford CS224N: NLP with Deep Learning  /  Spring 2024  /  Lecture 11 - Benchmarking by Yann Dubois | [Read](../../../stocks/data/transcripts/translated/stanford-online/TO0CqzqiArM_stanford-cs224n-nlp-with-deep-learning-spring-2024.md) | [YouTube](https://www.youtube.com/watch?v=TO0CqzqiArM) |
| S09 | Stanford CS224N: NLP w/ DL  /  Spring 2024  /  Lecture 12 - Efficient Training, Shikhar Murty | [Read](../../../stocks/data/transcripts/translated/stanford-online/UVX7SYGCKkA_stanford-cs224n-nlp-w-dl-spring-2024-lecture-12.md) | [YouTube](https://www.youtube.com/watch?v=UVX7SYGCKkA) |
| S10 | Stanford CME295 Transformers & LLMs  /  Autumn 2026  /  Lecture 4 - Reinforcement Learning with LLMs | [Read](../../../stocks/data/transcripts/translated/stanford-online/3Vaj0Oka_t4_stanford-cme295-transformers-llms-autumn-2026-lect.md) | [YouTube](https://www.youtube.com/watch?v=3Vaj0Oka_t4) |
| S11 | Stanford CS25: V5 I Large Language Model Reasoning, Denny Zhou of Google Deepmind | [Read](../../../stocks/data/transcripts/translated/stanford-online/ebnX5Ur1hBk_stanford-cs25-v5-i-large-language-model-reasoning.md) | [YouTube](https://www.youtube.com/watch?v=ebnX5Ur1hBk) |
| S12 | Stanford CS25: V5 I On the Biology of a Large Language Model, Josh Batson of Anthropic | [Read](../../../stocks/data/transcripts/translated/stanford-online/vRQs7qfIDaU_stanford-cs25-v5-i-on-the-biology-of-a-large-langu.md) | [YouTube](https://www.youtube.com/watch?v=vRQs7qfIDaU) |
| S13 | Stanford Webinar - Large Language Models Get the Hype, but Compound Systems Are the Future of AI | [Read](../../../stocks/data/transcripts/translated/stanford-online/vRTcE19M-KE_stanford-webinar---large-language-models-get-the-h.md) | [YouTube](https://www.youtube.com/watch?v=vRTcE19M-KE) |

## Chapter reading map

Read the named sections rather than restarting a full recording for every lesson. Headers are search phrases in the English file, not timestamps. Reading assignments deliberately revisit some recordings after new prerequisites are learned.

| Chapter | Source sections | Coverage and supplement |
|---|---|---|
| [01](chapters/01-what-a-language-model-learns.md) | S04: WHAT MATTERS WHEN TRAINING LLMS; PRETRAINING AND POST-TRAINING. S03: WHAT WE CAN LEARN AT SMALL SCALE. | Lifecycle synthesis and glossary bridge authored here. |
| [02](chapters/02-tensors-probability-and-gradients.md) | S01: MATRIX MULTIPLICATION AND MULTI-HEAD ATTENTION, after this chapter. | The tensor, probability, and gradient bridge is an authored prerequisite supplement. |
| [03](chapters/03-text-bytes-and-tokenization.md) | S03: Tokenization; Byte Pair Encoding. S01: Tokenization; Special tokens. | Worked byte/BPE example and reversible implementation supplied here. |
| [04](chapters/04-embeddings-and-representations.md) | S01: Representing tokens; Word2vec; Word Embeddings and Their Limitations. | Tensor-shape walkthrough and parameter/activation distinction supplied here. |
| [05](chapters/05-next-token-prediction-and-loss.md) | S05: NEXT-TOKEN PREDICTION; CROSS-ENTROPY LOSS. S04: THE MODEL AND TRAINING LOSS. | Target shift and gradient derivation supplied here. |
| [06](chapters/06-attention-from-first-principles.md) | S06: INTRODUCING ATTENTION through ATTENTION MECHANISMS. S01: SELF-ATTENTION: QUERIES, KEYS, AND VALUES. | Numerical weighted-sum example supplied here. |
| [07](chapters/07-causality-heads-and-position.md) | S01: MATRIX MULTIPLICATION AND MULTI-HEAD ATTENTION; MASKING AND SOFTMAX. S02: POSITION INFORMATION; Rotary Position Embeddings. | Causal dependency argument and rotary dot-product derivation supplied here. |
| [08](chapters/08-the-decoder-transformer.md) | S01: THE TRANSFORMER ARCHITECTURE; Residual Connections and Other Techniques; THE DECODER. S02: Normalization. | Complete educational decoder is authored here; it uses learned positions, pre-LayerNorm, and a dense feed-forward layer. |
| [09](chapters/09-generating-text.md) | S01: Autoregressive Decoding. S02: TEMPERATURE AND DETERMINISM; GUIDED DECODING. | Exact sampling arithmetic and generation exercise supplied here. |
| [10](chapters/10-building-the-pretraining-dataset.md) | S05: PRETRAINING DATA; MIDTRAINING AND LONG-CONTEXT TRAINING. S04: Training Data; DATA PROCESSING AND QUALITY. | Corpus split and fingerprint protocol supplied here. |
| [11](chapters/11-training-a-small-language-model.md) | S05: PRETRAINING AND TRANSFER LEARNING; THE RESULT OF TRAINING. S04: SYSTEMS AND GPU OPTIMIZATION. | Complete small training/checkpoint loop supplied here. |
| [12](chapters/12-evaluating-models-and-experiments.md) | S08: Perplexity and Downstream Performance; EVALUATION BIASES; EVALUATION TAKEAWAYS. S04: Evaluating Language Models. | Controlled comparison and token-weighted metric protocol supplied here. |
| [13](chapters/13-efficient-training-and-scaling.md) | S09: FLOATING-POINT REPRESENTATION; MIXED-PRECISION TRAINING; DDP; ZeRO; Activation Memory. S02: Scaling Laws; Mixture of Experts. | Memory arithmetic and distinction between local demonstration and distributed systems supplied here. |
| [14](chapters/14-instruction-tuning-and-chat.md) | S05: SUPERVISED FINE-TUNING. S07: INSTRUCTION FINE-TUNING and LIMITATIONS. | Chat serialization, label masking, and tokenizer compatibility protocol supplied here. |
| [15](chapters/15-low-rank-adaptation.md) | S05: LOW-RANK ADAPTATION. S09: PARAMETER-EFFICIENT FINE-TUNING AND LoRA; CHOOSING LoRA SETTINGS. | Low-rank update exercise supplied here. |
| [16](chapters/16-preferences-rewards-and-reasoning.md) | S10: reward objectives, PPO, GRPO. S07: Bradley-Terry; DPO; reward hacking. S11: reasoning, decoding, verifiable rewards. | Toy preference-objective exercise is not a full PPO, GRPO, or DPO training run. |
| [17](chapters/17-quantization-and-qlora.md) | S09: FLOATING-POINT REPRESENTATION and fine-tuning memory as background. | Required quantization, group scales, clipping, packing, and QLoRA material is authored supplementation. Older CME295 2025 L4 contains useful optional background but remains excluded by latest-edition policy. |
| [18](chapters/18-kv-caches-and-serving.md) | S02: Key-Value Caching and Grouped-Query Attention; Sliding-Window Attention. S13: SMALL MODELS AND LATENCY. | Cache formula, equivalence check, scheduler discussion, and production limits supplied here. |
| [19](chapters/19-retrieval-tools-and-compound-systems.md) | S13: MODELS GET THE HEADLINES; PROMPTS AS PART OF A SYSTEM; TOOL ACCESS; Guardrails. S11: RETRIEVAL IN REASONING. | Lexical retrieval fixture, evidence boundary, and evaluation decomposition supplied here. |
| [20](chapters/20-interpretability-and-the-capstone.md) | S12: features, causal interventions, UNFAITHFULNESS. S08: EVALUATION TAKEAWAYS. | Attribution cautions and the capstone evidence rubric supplied here. |

## Elective: CME296, Spring 2026

These eight recordings are diffusion and vision generation. They explain the gap between the earlier 22-file LLM/NLP count and the complete 30-file archive. Study them after the LLM core or in a separate course. Their generative objective differs from autoregressive language modeling.

| Lecture | Topic / recording | English transcript |
|---|---|---|
| 1 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 1 - Diffusion | [Read](../../../stocks/data/transcripts/translated/stanford-online/tr-CUpw--ck_stanford-cme296-diffusion-large-vision-models-spri.md) |
| 2 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 2 - Score matching | [Read](../../../stocks/data/transcripts/translated/stanford-online/_WaR2fjZpEQ_stanford-cme296-diffusion-large-vision-models-spri.md) |
| 3 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 3 - Flow matching | [Read](../../../stocks/data/transcripts/translated/stanford-online/agN3AlfGFrk_stanford-cme296-diffusion-large-vision-models-spri.md) |
| 4 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 4 - Latent Space & Guidance | [Read](../../../stocks/data/transcripts/translated/stanford-online/WUUq6TVAu8U_stanford-cme296-diffusion-large-vision-models-spri.md) |
| 5 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 5 - Architectures | [Read](../../../stocks/data/transcripts/translated/stanford-online/HpFdSlMeXzQ_stanford-cme296-diffusion-large-vision-models-spri.md) |
| 6 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 6 - Model Training | [Read](../../../stocks/data/transcripts/translated/stanford-online/IvXTl3yj-4Y_stanford-cme296-diffusion-large-vision-models-spri.md) |
| 7 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 7 - Evaluation | [Read](../../../stocks/data/transcripts/translated/stanford-online/iNaRBp4T57Q_stanford-cme296-diffusion-large-vision-models-spri.md) |
| 8 | Stanford CME296 Diffusion & Large Vision Models  /  Spring 2026  /  Lecture 8 - Trending Topics | [Read](../../../stocks/data/transcripts/translated/stanford-online/oyLUvz9nR6E_stanford-cme296-diffusion-large-vision-models-spri.md) |

## Older course edition, excluded from required reading

CME295 Autumn 2025 has lectures 1 to 9. The required course uses Autumn 2026 instead. All nine older translations remain available in the archive. Lecture 4 contains quantization and QLoRA background; using it as an optional supplement does not restore the older series to the required reading order.

| Lecture | Recording | English transcript |
|---|---|---|
| 1 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 1 - Transformer | [Read](../../../stocks/data/transcripts/translated/stanford-online/Ub3GoFaUcds_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 2 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 2 - Transformer-Based Models & Tricks | [Read](../../../stocks/data/transcripts/translated/stanford-online/yT84Y5zCnaA_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 3 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 3 - Tranformers & Large Language Models | [Read](../../../stocks/data/transcripts/translated/stanford-online/Q5baLehv5So_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 4 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 4 - LLM Training | [Read](../../../stocks/data/transcripts/translated/stanford-online/VlA_jt_3Qc4_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 5 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 5 - LLM tuning | [Read](../../../stocks/data/transcripts/translated/stanford-online/PmW_TMQ3l0I_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 6 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 6 - LLM Reasoning | [Read](../../../stocks/data/transcripts/translated/stanford-online/k5Fh-UgTuCo_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 7 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 7 - Agentic LLMs | [Read](../../../stocks/data/transcripts/translated/stanford-online/h-7S6HNq0Vg_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 8 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 8 - LLM Evaluation | [Read](../../../stocks/data/transcripts/translated/stanford-online/8fNP4N46RRo_stanford-cme295-transformers-llms-autumn-2025-lect.md) |
| 9 | Stanford CME295 Transformers & LLMs  /  Autumn 2025  /  Lecture 9 - Recap & Current Trends | [Read](../../../stocks/data/transcripts/translated/stanford-online/Q86qzJ1K1Ss_stanford-cme295-transformers-llms-autumn-2025-lect.md) |

## Course-completeness limits

- CS224N Spring 2024: downloaded lectures 7, 10, 11, and 12. Lectures 1 to 6, 8, and 9 are absent from this archive.
- CS336 Spring 2025: downloaded lecture 1 only. It is not a complete from-scratch course archive.
- CME295 Autumn 2026: downloaded lectures 1 to 4. No later lectures are in this archive.
- CME296 Spring 2026: downloaded lectures 1 to 8, with no internal gap in that range.
- CS229, CS25, and the compound-systems webinar are individual talks, not full course archives.
