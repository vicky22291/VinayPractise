# Practical setup and evidence

These guides turn the chapters into inspectable numerical experiments. The default fixtures are synthetic, and none of the scripts downloads data or installs packages.

## Run from the course directory

```
cd llm-learning
python --version
python practicals/scripts/tokenizer_lab.py --smoke
python practicals/scripts/systems_lab.py --smoke
python practicals/scripts/tensor_lab.py --smoke
python practicals/scripts/tiny_decoder.py --smoke
```

The first two scripts use only Python's standard library. The tensor and decoder scripts require PyTorch already installed in the selected interpreter. Reuse the [ML course's documented environment](../../ml-learning/README.md#set-up-once) when available. Do not assume that the VQTS-Python translation environment is the same environment or exposes the same GPU. No new environment or package pins are created here.

A smoke command checks small structural properties and prints a pass verdict. It performs no optimizer update, writes no model/data file, and is not a training or throughput benchmark. The decoder smoke includes shape, causal-prefix, cache, gradient-finiteness, and context-boundary checks.

The decoder's real modes use an explicit device: `--device cpu`, `--device mps`, or `--device cuda`. An unavailable accelerator is refused rather than silently falling back. Start with CPU if that is the verified option. Choose a step budget before training; runtime is not premeasured for your interpreter/device.

## Four scripts

| Script | Purpose | Important boundary |
|---|---|---|
| [tokenizer_lab.py](scripts/tokenizer_lab.py) | Reversible byte BPE with deterministic pair ties | Separate representation experiment; it does not change the decoder's vocabulary |
| [tensor_lab.py](scripts/tensor_lab.py) | Shapes, loss, attention, rotary identity, precision, response masking, low-rank fitting, preference loss, packed quantization | Synthetic tensors; no pretrained LLM is adapted |
| [tiny_decoder.py](scripts/tiny_decoder.py) | One complete byte decoder with learned positions, bounded training, checkpoint resume, evaluation, generation, and cache comparison | No RoPE, dropout, distributed training, fused kernels, or production scheduling |
| [systems_lab.py](scripts/systems_lab.py) | Lexical retrieval over synthetic versioned documents | No answer generation and no tool execution |

## Data and artifacts

The decoder accepts `--text PATH` and writes only to an explicit `--out PATH` during training. Use a work directory outside this repo, normally `~/llm-data/`. An existing TinyShakespeare copy may be at `~/ml-data/nanoGPT/data/shakespeare_char/input.txt`; the [ML language-model module](../../ml-learning/m7-language-models/README.md) documents its source and download workflow. Check the corpus you actually use. No corpus is bundled here.

The decoder uses UTF-8 bytes directly with a fixed vocabulary of 256. It splits the file at 90 percent by byte offset, then builds windows entirely within each partition. This avoids crossing that boundary but does not remove repeated content across it. The saved data hash and boundary must match when resuming or evaluating that checkpoint.

Checkpoints include model configuration, tokenizer identity, weights, optimizer state, completed updates, data fingerprint, training settings, and CPU/device generator states. `--steps` means additional updates on resume. A resume retains saved batch size, learning rate, and architecture; use a new run for a changed configuration. Device/software changes may change reproducibility. Checkpoints use the teaching script's own format, not arbitrary Hugging Face model files.

## Experiment record

Before non-smoke runs, write a prediction or competing hypotheses. Record all commands, seed, data identity, device, software, budget, and failed runs. Paste `RESULT` lines into your own record, then explain what the denominator and scope fields mean. No measured result is prefilled in these guides.

The maximum context includes prompt plus new tokens. The default decoder context is 64 bytes, not 64 characters. Generated arbitrary bytes can be invalid UTF-8; the display replaces invalid sequences while preserving raw byte ids in the result. `--untrained` is an explicit random-model generation demonstration.

The decoder implements greedy selection, temperature sampling, and an optional top-k filter. Nucleus sampling and grammar-constrained decoding are explained in the chapter but are not implemented by this script. The synthetic preference exercise is a scalar loss, and the quantization exercise is a packed tensor representation; neither is a full alignment or optimized low-bit model runtime.

## Practical index

- [P01: Text to tokens](01-tokens-and-bpe.md)
- [P02: Vectors, logits, and loss](02-vectors-logits-and-loss.md)
- [P03: Attention and causality](03-attention-and-causality.md)
- [P04: Decoder and generation](04-decoder-and-generation.md)
- [P05: Data and small-model training](05-data-and-small-model-training.md)
- [P06: Honest evaluation](06-honest-evaluation.md)
- [P07: Precision and training memory](07-precision-and-training-memory.md)
- [P08: Instruction loss and LoRA](08-instruction-loss-and-lora.md)
- [P09: Preference objectives](09-preference-objectives.md)
- [P10: Quantization](10-quantization.md)
- [P11: Cached inference](11-cached-inference.md)
- [P12: Grounding and capstone](12-grounding-and-capstone.md)
