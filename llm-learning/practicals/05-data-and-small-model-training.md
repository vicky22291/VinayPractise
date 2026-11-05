# P05. Data and small-model training

Produce a versioned small-corpus experiment and a resumable checkpoint with a bounded amount of actual optimization.

**Prerequisites:** [Chapter 10](../chapters/10-building-the-pretraining-dataset.md), [Chapter 11](../chapters/11-training-a-small-language-model.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Data audit before the session

Select a small local text file with known provenance. An existing TinyShakespeare copy may be at the path below, documented by the ML course. Confirm it exists and record its source/license. Do not substitute a secret or private corpus casually. The course does not download one for you.

Read `corpus` and `evaluate`. Draw the contiguous split and the T+1 slicing rule. Identify the remaining near-duplicate and document-boundary limitations. Choose a maximum step count and wall-time stop rule before training.

## 2. Bounded first run

Use an available device you verified. This example explicitly chooses CPU; change it only as a recorded experimental setting.

```
python practicals/scripts/tiny_decoder.py --train --text ~/ml-data/nanoGPT/data/shakespeare_char/input.txt --out ~/llm-data/checkpoints/byte-a.pt --steps 40 --batch 8 --context 64 --width 64 --layers 2 --heads 4 --device cpu --seed 0
```

This is a step budget, not a runtime promise. The initial and final validation records have their own scope; the last training-batch loss is a different statistic. The output path must be new.

## 3. Resume deliberately

```
python practicals/scripts/tiny_decoder.py --train --resume ~/llm-data/checkpoints/byte-a.pt --text ~/ml-data/nanoGPT/data/shakespeare_char/input.txt --out ~/llm-data/checkpoints/byte-b.pt --steps 20 --device cpu
```

The saved architecture, batch size, learning rate, and generator states are retained. `--steps` adds updates. Explain why a weights-only restart would be a different experiment. Keep the same device and software for the resume comparison.

## 4. Failure boundary

Before a long run, plan what should happen if the corpus changes, the context does not fit, or the output file already exists. Inspect the explicit refusals. Run only a small synthetic reproduction of a failure, preserving your real artifacts.


## Evidence to keep

Keep corpus identity and split, initial/final validation records, exact commands, interpreter/device, elapsed time, completed updates, and both checkpoint paths. Explain what a 40-step run does and does not establish.

## Scope and next step

This is a small byte model with a simple contiguous split, not a frontier-pretraining recipe. No required long job has been benchmarked. Move to P06 for a controlled evaluation of the saved artifacts.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
