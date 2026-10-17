# Apple Silicon and Compute for ML Practice (M4 Pro, 24 GB)

Research date: 2026-10-17. Each version, quota, and price shows the date its source displayed. "Fetched 2026-10-17" means the page had no visible date.

## How to read this file

- Every factual claim has an inline link. [unverified] means no primary source could be opened. [inference] means my reasoning from cited facts, not tested here. [stale?] marks sources older than 2024 or repos last pushed before 2025.
- Every timing names its chip. Most timings come from GitHub repos, not Apple.
- Method: about 60 search or fetch tool calls (WebSearch, WebFetch, curl, gh api, PyPI JSON). Nothing was installed, no virtual environment was created, and no model or dataset was downloaded. Wheels were read as zip data only. The 127 MB torch wheel was fetched in full because the server ignored a byte-range request.

## This Mac (read-only check, 2026-10-17)

- Apple M4 Pro: 14-core CPU (10 performance, 4 efficiency), 20-core GPU ("Metal Support: Metal 4"), 24 GiB unified memory (25,769,803,776 bytes).
- macOS 26.5.1 (25F80). Python 3.14.3 at /opt/homebrew/bin/python3. Homebrew installed. uv and conda not installed.
- Homebrew libomp installed (`brew list --versions libomp` shows 22.1.4 and 19.1.7). Disk: 188 GiB free of 926 GiB. The notes folder existed and was empty.

## Bottom line

- Local M4 Pro (24 GB) suits classical ML, CIFAR-size CNNs, DistilBERT-size fine-tunes at batch 16 to 32, and LoRA on 1B and 3B 4-bit models with MLX. A 7B 4-bit QLoRA should fit at batch size 1 [inference], but it is untested here.
- Use free cloud GPUs when one run takes more than about 10 minutes, when you need full-precision 7B fine-tunes, or when you need a CUDA-only or GPU-boosting path. LightGBM's GPU build is not for macOS. [LightGBM docs](https://github.com/microsoft/LightGBM/blob/master/docs/Installation-Guide.rst)
- Use Python 3.13 or 3.14 (3.14.3 is installed here). Avoid 3.15 for torch until torch ships cp315 wheels. [PyPI torch](https://pypi.org/pypi/torch/json) Use uv with one virtual environment per project. [uv docs](https://docs.astral.sh/uv/pip/environments/)
- Expect about 110 to 250 seconds per epoch for ResNet-50 on CIFAR-100 on the chips in Table 6.1. A 1-to-10-minute lab needs a subset, ResNet-18, or fewer epochs.

## Key question 1: Apple M4 Pro specs that matter for ML

### Takeaway
M4 Pro has 273 GB/s of memory bandwidth, a 16-core Neural Engine, and up to 20 GPU cores. The CPU and GPU share one memory pool, so the GPU budget is below 24 GB. PyTorch MPS and MLX run on the GPU, not the Neural Engine.

### Cited Findings
- Apple: M4 Pro has "an up to 14-core CPU consisting of up to 10 performance cores and four efficiency cores," a GPU with "up to 20 cores," and "up to 64GB of fast unified memory and 273GB/s of memory bandwidth." [Apple newsroom, 2024-10-30](https://www.apple.com/newsroom/2024/10/apple-introduces-m4-pro-and-m4-max/)
- Apple's spec page, archived 2024-11-28, lists M4 Pro with 12-core CPU and 16-core GPU, and M4 Pro with 14-core CPU and 20-core GPU. Both show a "16-core Neural Engine" and "273GB/s memory bandwidth." Base memory is "24GB unified memory." It also says "or 48GB (M4 Pro and M4 Max with 16-core CPU)." [Apple specs, archived](https://web.archive.org/web/20241201000000id_/https://www.apple.com/macbook-pro/specs/) See Conflicts.
- The live spec page lists only M5 models now. [Apple specs, live](https://www.apple.com/macbook-pro/specs/) (fetched 2026-10-17)
- The M4 chip (May 2024) has a Neural Engine "capable of 38 trillion operations per second" in a "16-core design." [Apple M4 newsroom](https://www.apple.com/newsroom/2024/05/apple-introduces-m4-chip/) The M4 Pro pages I read give no TOPS figure.
- PyTorch MPS enables "training on GPU for macOS devices with Metal programming framework." [PyTorch MPS notes](https://github.com/pytorch/pytorch/blob/main/docs/source/notes/mps.md) MLX: "Arrays in MLX live in shared memory." [MLX README](https://github.com/ml-explore/mlx/blob/main/README.md)
- PyTorch's watermark ratio of 1.0 means "device.recommendedMaxWorkingSetSize." [PyTorch env vars](https://github.com/pytorch/pytorch/blob/main/docs/source/mps_environment_variables.md) Apple's page for that Metal property loaded only its title here. [Apple docs](https://developer.apple.com/documentation/metal/mtldevice/recommendedmaxworkingsetsize)

### Inferences
- The 24 GB pool holds the OS, your apps, and GPU tensors. A 3B 4-bit model (1.8 GB of weights) fits easily. A 7B model at full precision (14.5 GB) leaves little room. [inference from Key question 4 sizes]
- Bandwidth matters most for LLM token generation. For small CNN training, batch size and kernel overhead matter more. [inference]
- On the repo CSVs, expect M4 Pro (20 GPU cores) between M3 Pro (14 cores) and M3 Max (30 cores). [inference; M4 Pro is not in the repo]

### Gaps
- No M4 Pro timing from a primary source. The exact GPU memory cap on this Mac is measured in Lab 3. Current store memory options were not checked.

## Key question 2: PyTorch on Apple Silicon

### Takeaway
Use torch 2.14.1 on Python 3.13 or 3.14. MPS covers many ops and is adding linear algebra and FlexAttention. float64 never works. torch.compile on MPS is still an early prototype.

### Cited Findings
- Latest stable torch is 2.14.1, uploaded 2026-09-30, requiring Python >=3.10. [PyPI torch](https://pypi.org/pypi/torch/json) GitHub release "PyTorch 2.14.1 Release," 2026-09-30. [v2.14.1](https://github.com/pytorch/pytorch/releases/tag/v2.14.1) Prior release: 2.14.0 (2026-09-02). [v2.14.0](https://github.com/pytorch/pytorch/releases/tag/v2.14.0)
- Wheels for this Mac: `torch-2.14.1-cp313-cp313-macosx_14_0_arm64.whl` and the `cp314` build (127.3 MB each), plus free-threaded `cp314t`. No `cp315` wheel exists for 2.14.1. [PyPI torch] torchvision 0.29.1 has matching macOS 14 arm64 wheels but declares `!=3.14.1,>=3.10`. [PyPI torchvision](https://pypi.org/pypi/torchvision/json)
- "The MPS backend does not support torch.float64 (torch.double) or torch.complex128," and a float64 tensor on MPS raises a TypeError. `PYTORCH_ENABLE_MPS_FALLBACK=1` "does not apply," and double-precision work "has to run on the CPU." [PyTorch MPS notes](https://github.com/pytorch/pytorch/blob/main/docs/source/notes/mps.md)
- Fallback: "If 1, falls back to CPU when MPS ops aren't supported." `PYTORCH_MPS_HIGH_WATERMARK_RATIO` defaults to 1.7; 1.0 is the recommended maximum; 0.0 disables the limit. `PYTORCH_MPS_LOW_WATERMARK_RATIO` defaults to 1.4 on unified memory. [PyTorch env vars](https://github.com/pytorch/pytorch/blob/main/docs/source/mps_environment_variables.md)
- torch.mps API: `set_per_process_memory_fraction`, `current_allocated_memory`, `driver_allocated_memory`, `recommended_max_memory`, `synchronize`, `empty_cache`. [torch.mps API](https://github.com/pytorch/pytorch/blob/main/docs/source/mps.md)
- Operator coverage tracker #77764 was opened 2022-05-18, is still open, was updated 2026-10-08, and has 1,797 comments. [PyTorch issue #77764](https://github.com/pytorch/pytorch/issues/77764)
- v2.13.0 added "Add FlexAttention support for MPS" and "Alert on non-deterministic algorithms on MPS (#185061)." [v2.13.0](https://github.com/pytorch/pytorch/releases/tag/v2.13.0) v2.14.0: "Apple Silicon gains native linear algebra, including Jacobi-kernel SVD, eigh, QR and Cholesky." v2.14.1 fixed MPS svd and lstsq failures "for inputs above 8192 elements." [v2.14.1](https://github.com/pytorch/pytorch/releases/tag/v2.14.1)
- Inductor's MPS file says: "This is not a feature-complete compiler backend. Just an early prototype that shows that one can compile elementwise ops into a Metal shader." [inductor mps.py](https://github.com/pytorch/pytorch/blob/main/torch/_inductor/codegen/mps.py) The compile API doc does not mention MPS. [torch.compiler_api.md](https://github.com/pytorch/pytorch/blob/main/docs/source/torch.compiler_api.md)
- The autocast and randomness docs do not mention MPS. [amp.md](https://github.com/pytorch/pytorch/blob/main/docs/source/amp.md) [randomness.md](https://github.com/pytorch/pytorch/blob/main/docs/source/notes/randomness.md) Accelerate says "fp16 mixed precision with MPS device requires a Pytorch >= 2.5.0" and "bf16 mixed precision with MPS device requires a Pytorch >= 2.6.0." [accelerator.py](https://github.com/huggingface/accelerate/blob/main/src/accelerate/accelerator.py)
- A 2023-24 repo README says "MPS doesn't support torch.compile()" and "float16 ... doesn't work on MPS devices," and advises raising `ulimit -n` for large runs. [mac-ml-speed-test README](https://github.com/mrdbourke/mac-ml-speed-test/blob/main/README.md) [stale?] These conflict with the newer sources. transformers says "MPS requires forking if multiple workers are specified." [training_args.py](https://github.com/huggingface/transformers/blob/main/src/transformers/training_args.py)

### Inferences
- Call `torch.mps.synchronize()` before reading clocks, and skip the first step, which pays for Metal shader compilation. A forum post says the warm-up keeps "one time Metal shader compilation" out of the timings. [forum, unverified](https://discuss.pytorch.org/t/mps-seems-much-slower-than-cpu-on-an-m1-mac/225242)
- Treat torch.compile on MPS as optional. Use float32 for science code, and test float16 autocast in a short run.

### Gaps
- No official MPS op coverage percentage (the external matrix is linked from #77764 and was not opened). No official bf16 op list. No official list of nondeterministic MPS ops.

## Key question 3: torchvision, torchaudio, transformers, datasets, accelerate, fastai on MPS

### Takeaway
The Hugging Face and fastai stacks pick MPS automatically when torch can see it. torchvision has native MPS kernels for detection ops. torchaudio is in maintenance mode.

### Cited Findings
- torchvision has MPS kernels for nms, roi_align, roi_pool, ps_roi_pool, ps_roi_align, and deform_conv2d. [torchvision csrc/ops/mps](https://github.com/pytorch/vision/tree/main/torchvision/csrc/ops/mps) torchaudio 2.11.0 (2026-03-23): "We have transitioned TorchAudio into a maintenance phase." [torchaudio README](https://github.com/pytorch/audio/blob/main/README.md) [PyPI torchaudio](https://pypi.org/pypi/torchaudio/json)
- transformers 5.20.1 (2026-10-16, Python >=3.10.0). [PyPI transformers](https://pypi.org/pypi/transformers/json) On main, `training_args.py` selects `torch.device("mps")`; my grep found no `use_mps_device` argument. [training_args.py](https://github.com/huggingface/transformers/blob/main/src/transformers/training_args.py)
- accelerate 1.15.0 (2026-09-09) lists MPS with the fp16 and bf16 gates above. [PyPI accelerate](https://pypi.org/pypi/accelerate/json) datasets 5.1.0 (2026-10-05, Python >=3.10.0). [PyPI datasets](https://pypi.org/pypi/datasets/json)
- fastai 2.8.12 (2026-09-09): the default device is `mps` when available. [PyPI fastai](https://pypi.org/pypi/fastai/json) [torch_core.py, lines 265 to 276](https://github.com/fastai/fastai/blob/main/fastai/torch_core.py)

### Inferences
- One uv virtual environment with torch, torchvision, transformers, accelerate, datasets, and fastai covers most labs. Skip torchaudio unless you need audio. [inference]
- datasets loads and processes data on the CPU. [inference; no device code checked]

### Gaps
- No Apple timings for fastai or accelerate on MPS. Nothing here was run on this Mac.

## Key question 4: Apple MLX and mlx-lm (LoRA and QLoRA)

### Takeaway
mlx-lm runs LoRA and QLoRA from the command line. A 4-bit 7B model has about 4 GB of weights, which likely fits 24 GB at batch size 1 [inference]. The official throughput numbers come from M1 Max and M2 Ultra, not M4 Pro.

### Cited Findings
- mlx 0.32.4 (2026-10-14, Python >=3.10) has cp313 and cp314 macOS arm64 wheels. [PyPI mlx](https://pypi.org/pypi/mlx/json) [mlx v0.32.4](https://github.com/ml-explore/mlx/releases/tag/v0.32.4) It depends on `mlx-metal==0.32.4`, whose wheels are 45.0 MB (macOS 14 tag) and 78.1 MB (macOS 26 tag). [PyPI mlx-metal](https://pypi.org/pypi/mlx-metal/json)
- mlx-lm 0.32.2 (2026-10-16, Python >=3.11). [PyPI mlx-lm](https://pypi.org/pypi/mlx-lm/json) Its LoRA doc says "The example also supports quantized LoRA (QLoRA)." Memory tips: `--batch-size` (default 4), `--num-layers` (default 16), and `--grad-checkpoint`. [mlx-lm LORA.md](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md)
- The doc's example is full-precision Mistral-7B-v0.1 with `--batch-size 1 --num-layers 4`, which it says "should run reasonably fast" on a 32 GB machine. On an M1 Max with 32 GB it "runs at about 250 tokens-per-second." [mlx-lm LORA.md](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md)
- The older mlx-examples LoRA README (uses `lora.py`) says the model "trains at around 475 tokens per second on an M2 Ultra" (Llama 7B, WikiSQL). [mlx-examples LoRA README](https://github.com/ml-explore/mlx-examples/blob/main/lora/README.md) [stale?]
- WWDC25 session 298: a 4-bit Mistral fine-tune "cuts memory usage for the model weights by about 3.5 times." The excerpt does not name a chip for that demo. [Apple WWDC25 298](https://developer.apple.com/videos/play/wwdc2025/298/) Session 315, "Get started with MLX for Apple silicon," exists; I did not read it. [WWDC25 315](https://developer.apple.com/videos/play/wwdc2025/315/)
- Hugging Face safetensors sizes: Llama-3.2-1B-Instruct-4bit 695.3 MB (plus 17.2 MB tokenizer) [HF API](https://huggingface.co/api/models/mlx-community/Llama-3.2-1B-Instruct-4bit?blobs=true); Llama-3.2-3B-Instruct-4bit 1,807.5 MB [HF API](https://huggingface.co/api/models/mlx-community/Llama-3.2-3B-Instruct-4bit?blobs=true); Mistral-7B-Instruct-v0.3-4bit 4,077.5 MB [HF API](https://huggingface.co/api/models/mlx-community/Mistral-7B-Instruct-v0.3-4bit?blobs=true); Mistral-7B-v0.1 full precision 9,943.0 + 4,540.5 = 14,483.5 MB [HF API](https://huggingface.co/api/models/mistralai/Mistral-7B-v0.1?blobs=true).
- mlx-examples MNIST runs on the CPU by default; "To run on the GPU, use: python main.py --gpu." It has no timings. [MNIST README](https://github.com/ml-explore/mlx-examples/blob/main/mnist/README.md) The transformer_lm README has no timings. [transformer_lm README](https://raw.githubusercontent.com/ml-explore/mlx-examples/main/transformer_lm/README.md)

### Inferences
- Fits on 24 GB (estimated, not measured): 1B and 3B 4-bit LoRA comfortably, and 7B 4-bit QLoRA at batch size 1. Full-precision 7B LoRA is risky, because the mlx-lm example is sized for 32 GB. [inference]
- 14,483.5 / 4,077.5 = 3.55, which matches Apple's "about 3.5 times." [inference from two sources] M4 Pro throughput is probably near the M1 Max figure (untested). Use the `mlx_lm.lora` CLI, not the older `lora.py` path.

### Gaps
- No M4 Pro throughput. No official memory table for 24 GB. The Stable Diffusion example was not checked.

## Key question 5: Other libraries (scikit-learn, XGBoost, LightGBM, CatBoost, JAX)

### Takeaway
Classical ML runs here with arm64 wheels. The gotchas are OpenMP (libomp) for XGBoost and LightGBM. LightGBM's GPU build is not for macOS. JAX on Apple GPU is "experimental."

### Cited Findings
- scikit-learn 1.9.1 (2026-09-10, Python >=3.11) has cp313 and cp314 arm64 wheels. [PyPI scikit-learn](https://pypi.org/pypi/scikit-learn/json)
- XGBoost 3.4.1 (2026-08-15, Python >=3.12) has a `py3-none-macosx_12_0_arm64` wheel (2.4 MB). The docs list "MacOS (x86_64, Apple Silicon)" as supported, and the platform table marks GPU unsupported on Apple Silicon. [PyPI xgboost](https://pypi.org/pypi/xgboost/json) [XGBoost install.rst](https://github.com/dmlc/xgboost/blob/master/doc/install.rst)
- XGBoost's R notes say to `brew install libomp`; its Python section does not. The XGBoost arm64 dylib has install name `@rpath/libomp.dylib` and rpath `/opt/homebrew/opt/libomp/lib`, and the wheel does not ship libomp. LightGBM 4.7.0 (2026-07-18, 1.5 MB wheel) has the same pattern. [local read of both wheels] [PyPI lightgbm](https://pypi.org/pypi/lightgbm/json)
- LightGBM docs: "The GPU version is not supported on macOS." [Installation-Guide.rst](https://github.com/microsoft/LightGBM/blob/master/docs/Installation-Guide.rst)
- CatBoost 1.2.10 (2026-02-18) has macOS `universal2` wheels for cp310 to cp314. [PyPI catboost](https://pypi.org/pypi/catboost/json) Its GPU page says "CatBoost supports training on GPUs" and "Training on GPU is non-deterministic." It does not mention macOS or Apple. [CatBoost GPU docs](https://catboost.ai/docs/features/training-on-gpu)
- JAX 0.11.2 (2026-09-17, Python >=3.12) and jaxlib 0.11.2 (cp313 and cp314 macOS arm64 wheels, 64.9 MB). [PyPI jax](https://pypi.org/pypi/jax/json) [PyPI jaxlib](https://pypi.org/pypi/jaxlib/json) The JAX table marks Apple GPU "experimental." [JAX installation.md](https://github.com/jax-ml/jax/blob/main/docs/installation.md) jax-metal's last release is 0.1.1 (2024-10-08). [PyPI jax-metal](https://pypi.org/pypi/jax-metal/json) [stale?]
- The torch cp314 wheel ships `torch/lib/libomp.dylib` (856,096 bytes uncompressed). [local read of the wheel]

### Inferences
- CPU boosting should handle a few million rows in a 1-hour lab. Not timed. [inference] Do not plan GPU boosting on this Mac.
- Torch's bundled libomp and Homebrew's libomp can both load into one process. That may crash or give wrong results. Untested. [inference] A search snippet calls `KMP_DUPLICATE_LIB_OK=TRUE` unsafe. [unverified]

### Gaps
- No primary source for the torch plus XGBoost OpenMP clash on macOS. Lab 9 tests it.

## Key question 6: Measured timings (chip named for each)

### Takeaway
The best measured set is `mac-ml-speed-test` (last pushed 2024-05-15). It covers M1 Pro, M3, M3 Pro, and M3 Max, but not M4. Use it as a proxy for this Mac.

### Repo facts
- The README describes "a collection of simple scripts focused on benchmarking the speed of various machine learning models on Apple Silicon Macs (M1, M2, M3)." [README](https://github.com/mrdbourke/mac-ml-speed-test/blob/main/README.md)
- The CIFAR script reports the average epoch time in seconds, as total time divided by epochs. [script](https://github.com/mrdbourke/mac-ml-speed-test/blob/main/pytorch_test_computer_vision_cifar100.py) GPU cores per the README table: M1 Pro 16, M3 10, M3 Pro 14, M3 Max 30. The PyTorch version is not recorded. [unverified]

Table 6.1: ResNet-50 on CIFAR-100 (32x32), average seconds per epoch. [CSVs](https://github.com/mrdbourke/mac-ml-speed-test/tree/main/results/results_pytorch_cv)

| Chip (GPU cores) | Batch 32 | Batch 128 | Batch 1024 |
|---|---|---|---|
| M1 Pro (16) | 248.6 | 127.3 | 112.3 |
| M3 (10) | 184.4 | 120.6 | 109.7 |
| M3 Pro (14) | 194.7 | 117.3 | 110.5 |
| M3 Max (30) | 211.0 | 125.0 | 110.8 |
| NVIDIA TITAN RTX (reference) | 27.8 | 11.8 | 8.5 |

Table 6.2 (Food101, 224x224, batch 32, seconds per epoch): M1 Pro 1266.5; M3 1758.2; M3 Pro 1154.9; M3 Max 775.5; TITAN RTX 286.2; Tesla V100 604.3. [CSVs](https://github.com/mrdbourke/mac-ml-speed-test/tree/main/results/results_pytorch_cv)

Table 6.3: DistilBERT on IMDB (512 tokens; README says the top two layers and top block are fine-tuned; 3 epochs). Values are `train_runtime` in seconds. [CSVs](https://github.com/mrdbourke/mac-ml-speed-test/tree/main/results/results_pytorch_nlp)

| Chip (GPU cores) | Batch 16 (s) | Samples/s at batch 16 | Batch 256 (s) |
|---|---|---|---|
| M1 Pro (16) | 2425.8 | 30.9 | 9330.5 |
| M3 (10) | 6388.9 | 11.7 | FAILED at batch 32 |
| M3 Pro (14) | 2615.7 | 28.7 | FAILED |
| M3 Max (30) | 1531.3 | 49.0 | 1707.9 |
| NVIDIA TITAN RTX (reference) | 569.5 | 131.7 | 544.9 |

Table 6.4 (Llama-2-7B-chat Q4_0 inference, not training, median tokens/s over 100 prompts): M1 Pro 34.3; M3 21.1; M3 Pro 29.5; M3 Max 48.0. [CSVs](https://github.com/mrdbourke/mac-ml-speed-test/tree/main/results/results_llama2)

Other timings:
- nanoGPT README (character-level Shakespeare): "On one A100 GPU this training run takes about 3 minutes." CPU: "Not bad for ~3 minutes on a CPU" (chip not named). MPS: "(2-3X)" (no chip named). [nanoGPT README](https://github.com/karpathy/nanoGPT) [stale?]
- nanoGPT issue 28, user reports: on a MacBook Air M2, "with mps: roughly 150~200ms for one iteration; without mps: roughly 450 ~ 500ms." Other posts give "30ms or 775ms" on M1 Pro (depending on a setting) and "approx. 2.2s" on a Mac mini M1 16GB after a fresh install. [nanoGPT issue #28](https://github.com/karpathy/nanoGPT/issues/28) [unverified user reports, conflicting]
- PyTorch forum (2.13.0): one M1 user measured a 3-layer CNN training step at 187.24 ms on CPU. A table in the thread seems to show 216 ms (CPU) vs 23.9 ms (MPS) on an M1 Air. [PyTorch forum](https://discuss.pytorch.org/t/mps-seems-much-slower-than-cpu-on-an-m1-mac/225242) [unverified]
- MLX LoRA: about 250 tokens/s on M1 Max 32 GB (Mistral-7B, batch 1, 4 layers) [mlx-lm LORA.md](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md); about 475 tokens/s on M2 Ultra (Llama-7B, WikiSQL) [mlx-examples LoRA README](https://github.com/ml-explore/mlx-examples/blob/main/lora/README.md).

Not found on Apple silicon: an MNIST CNN epoch time, a ResNet-18 or ResNet-34 Oxford-IIIT Pet fine-tune, a BERT-base fine-tune, and any M4 or M4 Pro number.

### Inferences
- A ResNet-50 CIFAR-100 epoch on M3-class chips takes about 2 minutes at batch 128. A 1-to-10-minute lab should use a subset or ResNet-18. [inference from Table 6.1]
- Beyond batch 256, per-epoch time barely moves on these chips (about 110 to 120 s). Pick batch 128 to 256. [inference]
- FAILED rows are memory signals on 16 to 36 GB machines. The repo author writes "without 24GB+ of RAM, running batch sizes of 256+ will likely error." [README](https://github.com/mrdbourke/mac-ml-speed-test/blob/main/README.md) [stale?]
- At CIFAR-100 batch 1024, M3 Pro is about 13x slower per epoch than TITAN RTX (110.5 s vs 8.5 s). At Food101 batch 32, about 4x (1154.9 s vs 286.2 s). M4 Pro should land between M3 Pro and M3 Max. [inference; not measured]

### Gaps
- No M4 or M4 Pro number from a primary source. The repo has no PyTorch version, and its CSVs date from 2023 to 2024. The nanoGPT numbers are user reports.

## Key question 7: Free cloud GPUs (quotas as shown on 2026-10-17)

### Takeaway
Free GPU use still exists, but limits are small and change. Kaggle and Colab offer 12-hour sessions. Lightning and Modal give credits. Hugging Face ZeroGPU gives minutes per day. AWS SageMaker Studio Lab no longer takes new customers.

| Provider | Free offer | Limits (as shown) | Hardware (as shown) | Source |
|---|---|---|---|---|
| Kaggle Notebooks | GPU sessions | 12 h per CPU or GPU session; 20 min idle in the editor; "At time of writing" (undated) | "1 Nvidia Tesla P100 GPU" or "2 Nvidia Tesla T4 GPUs" | [Kaggle docs](https://www.kaggle.com/docs/notebooks) |
| Google Colab | Free of charge | Free-tier notebooks run "at most 12 hours"; limits are not published | GPU types "vary over time" | [Colab FAQ](https://research.google.com/colaboratory/faq.html) |
| Lightning AI | Free credits | Rendered page shows both "80 free GPU hours" (headline) and "up to 30 free credits" (plan table); free Studios restart every 4 h | Free plan lists "Single GPUs (L40S, A100, H100, H200...)" | [Lightning pricing](https://lightning.ai/pricing) |
| Modal | Starter plan | "$0 + compute / month"; "$30 / month free credits" | Not checked | [Modal pricing](https://modal.com/pricing) |
| Hugging Face ZeroGPU | Free to all users | Daily quota: unauthenticated 2 min, free account 5 min, PRO 40 min (extensible), Enterprise org member 60 min | "NVIDIA RTX Pro 6000 Blackwell"; xlarge uses 2x the quota of large | [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu) |
| AWS SageMaker Studio Lab | "no longer open to new customers" | Existing accounts: GPU up to 4 h at a time and 4 h per 24 h | Not named on the AWS page | [AWS docs](https://docs.aws.amazon.com/sagemaker/latest/dg/studio-lab-overview.html) |

- Kaggle: "Colab Pro and Pro+ users will get 15 and 30 hours of extra GPU hours per week respectively on Kaggle," an experimental promotion linked to a Colab account. [Kaggle docs](https://www.kaggle.com/docs/notebooks) The docs state no base weekly GPU quota. Secondary sites say about 30 GPU hours a week. [unverified]
- Kaggle phone verification is not on the docs page. A forum post says it unlocks internet and GPU. [unverified, search snippet: https://forums.fast.ai/t/beginner-using-colab-or-kaggle/96280]
- Colab: "Colab does not publish these limits." Idle runtimes time out. [Colab FAQ](https://research.google.com/colaboratory/faq.html) Third-party write-ups say Studio Lab's GPU is a T4; the AWS page does not. [unverified]

### Inferences
- Kaggle offers the most predictable free session (12 hours, a fixed accelerator list). Colab hardware varies and its limits are not published.
- For runs under about 10 minutes, local MPS starts faster than a cloud notebook. Move to cloud for runs over about 30 minutes or for stronger GPUs. [inference]
- Do not plan new practice around SageMaker Studio Lab.

### Gaps
- Kaggle base weekly GPU quota and phone verification rules (no primary source). Colab compute-unit numbers and current GPU types. Lightning's real free-hour figure. Colab paid prices (not checked).

## Key question 8: Environment setup (uv, Python version, notebooks, disk)

### Takeaway
Use uv with one virtual environment per project and Python 3.13 or 3.14 (3.14.3 is already installed). Keep 3.15 out of torch projects until torch ships cp315 wheels. Plan a few GB per torch environment, plus 0.7 to 4.1 GB per 4-bit LLM.

### Cited Findings
- uv 0.13.1 (2026-10-14). [PyPI uv](https://pypi.org/pypi/uv/json) Install options: `curl -LsSf https://astral.sh/uv/install.sh | sh`, `pip install uv`, `brew install uv`. [uv install docs](https://docs.astral.sh/uv/getting-started/installation/) "Unlike pip, uv requires using a virtual environment by default." [uv environments](https://docs.astral.sh/uv/pip/environments/) `uv python install` manages Python builds. [uv Python guide](https://docs.astral.sh/uv/guides/install-python/)
- Python 3.14: "3.14.0 final: Tuesday, 2025-10-07." The schedule lists bugfix releases through 3.14.14 (2027-10-05) and security fixes "until October 2030." [PEP 745](https://raw.githubusercontent.com/python/peps/main/peps/pep-0745.rst)
- Python 3.13: "3.13.0 final: Monday, 2024-10-07." Security fixes "until October 2029." [PEP 719](https://raw.githubusercontent.com/python/peps/main/peps/pep-0719.rst)
- Python 3.15: "3.15.0 final: Friday, 2026-10-09." [PEP 790](https://raw.githubusercontent.com/python/peps/main/peps/pep-0790.rst) The CPython tag `v3.15.0` exists. [GitHub API](https://api.github.com/repos/python/cpython/git/refs/tags/v3.15.0) torch 2.14.1 has no cp315 wheel on PyPI (checked 2026-10-17). Version traps: torchvision 0.29.1 refuses Python 3.14.1; xgboost 3.4.1 and jax 0.11.2 need Python 3.12 or newer; mlx-lm needs 3.11 or newer.
- marimo 0.25.1 (2026-10-01): "A reactive Python notebook that's reproducible, git-friendly, and deployable as scripts or apps." Notebooks are stored as .py files. [marimo README](https://github.com/marimo-team/marimo) [PyPI marimo](https://pypi.org/pypi/marimo/json) JupyterLab 4.6.4 (2026-09-21) is the latest stable release. [PyPI jupyterlab](https://pypi.org/pypi/jupyterlab/json) VS Code has a Jupyter notebooks page. [VS Code docs](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- Sizes: the cp314 macOS arm64 torch wheel is 127.3 MB compressed; its member files total 524.1 MB uncompressed (zip central directory, read locally). [PyPI torch] mlx-metal 45.0 to 78.1 MB [PyPI mlx-metal]; jaxlib 64.9 MB [PyPI jaxlib]; scikit-learn 8.3 MB [PyPI scikit-learn]; XGBoost 2.4 MB and LightGBM 1.5 MB [PyPI xgboost] [PyPI lightgbm].
- ResNet-18 checkpoint `resnet18-f37072fd.pth`: HTTP content-length 46,830,571 bytes (46.8 MB). [torchvision resnet.py](https://github.com/pytorch/vision/blob/main/torchvision/models/resnet.py) [HEAD](https://download.pytorch.org/models/resnet18-f37072fd.pth) LLM checkpoints run from 695.3 MB (1B 4-bit) to 14,483.5 MB (Mistral-7B full precision); see Key question 4. Local disk: 188 GiB free of 926 GiB. [local `df`]

### Inferences
- Budget about 1 GB for torch and its direct dependencies, and a few GB per virtual environment with the usual packages. Not measured here. [inference]
- Budget about 15 GB for labs with two or three 4-bit LLMs, a few datasets, and the Hugging Face cache. [inference]
- Use marimo for small reactive labs that live in git. Use Jupyter in VS Code when you want familiar cells. [inference]

### Gaps
- Real size of a full virtual environment (installs were not allowed). Python 3.15 wheel status may change.

## Sources
| URL | What it supports | Date shown or fetched |
|---|---|---|
| https://www.apple.com/newsroom/2024/10/apple-introduces-m4-pro-and-m4-max/ | M4 Pro cores, 64 GB, 273 GB/s | 2024-10-30; fetched 2026-10-17 |
| https://web.archive.org/web/20241201000000id_/https://www.apple.com/macbook-pro/specs/ | M4 Pro configs, 16-core Neural Engine, memory text | archived 2024-11-28 |
| https://www.apple.com/macbook-pro/specs/ | Live page, M5 only | fetched 2026-10-17 |
| https://www.apple.com/newsroom/2024/05/apple-introduces-m4-chip/ | M4 Neural Engine 38 TOPS, 16-core design | May 2024; fetched 2026-10-17 |
| https://developer.apple.com/documentation/metal/mtldevice/recommendedmaxworkingsetsize | Page exists (title only) | fetched 2026-10-17 |
| https://developer.apple.com/videos/play/wwdc2025/298/ | 4-bit Mistral fine-tune, 3.5x memory | WWDC25; fetched 2026-10-17 |
| https://developer.apple.com/videos/play/wwdc2025/315/ | Session "Get started with MLX" exists (not read) | WWDC25; fetched 2026-10-17 |
| https://github.com/pytorch/pytorch/blob/main/docs/source/notes/mps.md | MPS is GPU; float64 unsupported; 15.0+ example | main; fetched 2026-10-17 |
| https://docs.pytorch.org/docs/2.14/notes/mps.html | 14.0+ example in 2.14 docs | 2.14 docs; fetched 2026-10-17 |
| https://github.com/pytorch/pytorch/blob/main/docs/source/mps_environment_variables.md | Watermark, fallback, env vars | main; fetched 2026-10-17 |
| https://github.com/pytorch/pytorch/blob/main/docs/source/mps.md | torch.mps API | main; fetched 2026-10-17 |
| https://github.com/pytorch/pytorch/issues/77764 | MPS op coverage tracker | created 2022-05-18; updated 2026-10-08 |
| https://github.com/pytorch/pytorch/releases/tag/v2.14.1 | 2.14.1 release; MPS linalg fixes | 2026-09-30 |
| https://github.com/pytorch/pytorch/releases/tag/v2.14.0 | Apple Silicon linalg | 2026-09-02 |
| https://github.com/pytorch/pytorch/releases/tag/v2.13.0 | FlexAttention on MPS; nondeterminism alert | 2026-07-08 |
| https://github.com/pytorch/pytorch/blob/main/torch/_inductor/codegen/mps.py | Inductor MPS "early prototype" | main; fetched 2026-10-17 |
| https://github.com/pytorch/pytorch/blob/main/docs/source/amp.md | Autocast doc, no MPS mention | main; fetched 2026-10-17 |
| https://github.com/pytorch/pytorch/blob/main/docs/source/notes/randomness.md | Randomness note, no MPS mention | main; fetched 2026-10-17 |
| https://github.com/pytorch/pytorch/blob/main/docs/source/torch.compiler_api.md | Compile API, no MPS mention | main; fetched 2026-10-17 |
| https://pypi.org/pypi/torch/json | torch 2.14.1 date, wheels, sizes | 2026-09-30; fetched 2026-10-17 |
| https://pypi.org/pypi/torchvision/json | torchvision 0.29.1, Python !=3.14.1 | 2026-09-30 |
| https://pypi.org/pypi/torchaudio/json | torchaudio 2.11.0 date | 2026-03-23 |
| https://github.com/pytorch/audio/blob/main/README.md | torchaudio maintenance phase | fetched 2026-10-17 |
| https://github.com/pytorch/vision/tree/main/torchvision/csrc/ops/mps | torchvision MPS kernels | main; fetched 2026-10-17 |
| https://pypi.org/pypi/transformers/json | transformers 5.20.1 date | 2026-10-16 |
| https://github.com/huggingface/transformers/blob/main/src/transformers/training_args.py | MPS device, fork note | main; fetched 2026-10-17 |
| https://pypi.org/pypi/accelerate/json | accelerate 1.15.0 date | 2026-09-09 |
| https://pypi.org/pypi/datasets/json | datasets 5.1.0 date | 2026-10-05 |
| https://pypi.org/pypi/fastai/json | fastai 2.8.12 date | 2026-09-09 |
| https://github.com/huggingface/accelerate/blob/main/src/accelerate/accelerator.py | fp16/bf16 MPS version gates | main; fetched 2026-10-17 |
| https://github.com/fastai/fastai/blob/main/fastai/torch_core.py | fastai default device mps | main; fetched 2026-10-17 |
| https://pypi.org/pypi/mlx/json | mlx 0.32.4 wheels | 2026-10-14 |
| https://github.com/ml-explore/mlx/releases/tag/v0.32.4 | mlx release | 2026-10-14 |
| https://pypi.org/pypi/mlx-metal/json | mlx-metal wheel sizes | 2026-10-14 |
| https://github.com/ml-explore/mlx/blob/main/README.md | Unified memory statement | main; fetched 2026-10-17 |
| https://pypi.org/pypi/mlx-lm/json | mlx-lm 0.32.2, Python 3.11 | 2026-10-16 |
| https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md | QLoRA, memory tips, M1 Max 250 tok/s | main; fetched 2026-10-17 |
| https://github.com/ml-explore/mlx-examples/blob/main/lora/README.md | M2 Ultra 475 tok/s (older lora.py) | main; fetched 2026-10-17 [stale?] |
| https://github.com/ml-explore/mlx-examples/blob/main/mnist/README.md | CPU default; no timings | main; fetched 2026-10-17 |
| https://raw.githubusercontent.com/ml-explore/mlx-examples/main/transformer_lm/README.md | No timings | fetched 2026-10-17 |
| https://huggingface.co/api/models/mlx-community/Llama-3.2-1B-Instruct-4bit?blobs=true | 695.3 MB weights | last modified 2025-03-05 |
| https://huggingface.co/api/models/mlx-community/Llama-3.2-3B-Instruct-4bit?blobs=true | 1,807.5 MB weights | last modified 2025-03-05 |
| https://huggingface.co/api/models/mlx-community/Mistral-7B-Instruct-v0.3-4bit?blobs=true | 4,077.5 MB weights | last modified 2024-06-18 |
| https://huggingface.co/api/models/mistralai/Mistral-7B-v0.1?blobs=true | 14,483.5 MB full precision | last modified 2025-07-24 |
| https://pypi.org/pypi/scikit-learn/json | scikit-learn 1.9.1 wheels | 2026-09-10 |
| https://pypi.org/pypi/xgboost/json | XGBoost 3.4.1 (Python 3.12), wheel | 2026-08-15 |
| https://pypi.org/pypi/lightgbm/json | LightGBM 4.7.0 wheel | 2026-07-18 |
| https://github.com/dmlc/xgboost/blob/master/doc/install.rst | Platforms; GPU unsupported on Apple Silicon; R libomp | master; fetched 2026-10-17 |
| https://github.com/microsoft/LightGBM/blob/master/docs/Installation-Guide.rst | GPU not supported on macOS | master; fetched 2026-10-17 |
| https://pypi.org/pypi/catboost/json | CatBoost 1.2.10 universal2 wheels | 2026-02-18 |
| https://catboost.ai/docs/features/training-on-gpu | GPU non-determinism; no macOS mention | fetched 2026-10-17 |
| https://pypi.org/pypi/jax/json | JAX 0.11.2 (Python 3.12) | 2026-09-17 |
| https://pypi.org/pypi/jaxlib/json | jaxlib arm64 wheels | 2026-09-17 |
| https://github.com/jax-ml/jax/blob/main/docs/installation.md | Apple GPU "experimental" | main; fetched 2026-10-17 |
| https://pypi.org/pypi/jax-metal/json | jax-metal last release | 2024-10-08 [stale?] |
| https://github.com/mrdbourke/mac-ml-speed-test/blob/main/README.md | Repo README, machine table, notes | last pushed 2024-05-15 |
| https://github.com/mrdbourke/mac-ml-speed-test/blob/main/pytorch_test_computer_vision_cifar100.py | Units: seconds per epoch | fetched 2026-10-17 |
| https://github.com/mrdbourke/mac-ml-speed-test/tree/main/results/results_pytorch_cv | CSVs for Tables 6.1 and 6.2 | fetched 2026-10-17 |
| https://github.com/mrdbourke/mac-ml-speed-test/tree/main/results/results_pytorch_nlp | CSVs for Table 6.3 | fetched 2026-10-17 |
| https://github.com/mrdbourke/mac-ml-speed-test/tree/main/results/results_llama2 | CSVs for Table 6.4 | fetched 2026-10-17 |
| https://github.com/karpathy/nanoGPT | README (A100 3 min, MPS 2-3X) | fetched 2026-10-17 [stale?] |
| https://github.com/karpathy/nanoGPT/issues/28 | User timings (M2, M1 Pro, M1) | opened 2023-01-08 |
| https://discuss.pytorch.org/t/mps-seems-much-slower-than-cpu-on-an-m1-mac/225242 | Forum timings (unverified) | fetched 2026-10-17 |
| https://www.kaggle.com/docs/notebooks | 12 h sessions, P100 or T4 x2, Colab hours | undated; fetched 2026-10-17 |
| https://research.google.com/colaboratory/faq.html | 12 h free tier; limits unpublished | undated; fetched 2026-10-17 |
| https://lightning.ai/pricing | 80 vs 30 free hours; restarts | fetched 2026-10-17 |
| https://modal.com/pricing | $30/month free credits | fetched 2026-10-17 |
| https://huggingface.co/docs/hub/spaces-zerogpu | ZeroGPU daily quotas | fetched 2026-10-17 |
| https://docs.aws.amazon.com/sagemaker/latest/dg/studio-lab-overview.html | Closed to new customers; limits | fetched 2026-10-17 |
| https://docs.astral.sh/uv/getting-started/installation/ | uv install options | fetched 2026-10-17 |
| https://docs.astral.sh/uv/pip/environments/ | uv requires a venv by default | fetched 2026-10-17 |
| https://docs.astral.sh/uv/guides/install-python/ | uv python install | fetched 2026-10-17 |
| https://pypi.org/pypi/uv/json | uv 0.13.1 | 2026-10-14 |
| https://raw.githubusercontent.com/python/peps/main/peps/pep-0745.rst | Python 3.14 schedule | fetched 2026-10-17 |
| https://raw.githubusercontent.com/python/peps/main/peps/pep-0719.rst | Python 3.13 schedule | fetched 2026-10-17 |
| https://raw.githubusercontent.com/python/peps/main/peps/pep-0790.rst | Python 3.15 schedule | fetched 2026-10-17 |
| https://api.github.com/repos/python/cpython/git/refs/tags/v3.15.0 | Tag exists | fetched 2026-10-17 |
| https://github.com/marimo-team/marimo | marimo reactive .py notebooks | fetched 2026-10-17 |
| https://pypi.org/pypi/marimo/json | marimo 0.25.1 | 2026-10-01 |
| https://pypi.org/pypi/jupyterlab/json | JupyterLab 4.6.4 | 2026-09-21 |
| https://code.visualstudio.com/docs/datascience/jupyter-notebooks | VS Code Jupyter notebooks | undated; fetched 2026-10-17 |
| https://github.com/pytorch/vision/blob/main/torchvision/models/resnet.py | ResNet-18 weight URL | fetched 2026-10-17 |
| https://download.pytorch.org/models/resnet18-f37072fd.pth | Checkpoint size (HEAD only) | fetched 2026-10-17 |
| https://forums.fast.ai/t/beginner-using-colab-or-kaggle/96280 | Kaggle phone verification (snippet) | undated [unverified] |

## Conflicts and open questions

- M4 Pro memory: the newsroom says "up to 64GB," but the archived spec page lists 64 GB only for M4 Max with 16-core CPU, and "48GB (M4 Pro and M4 Max with 16-core CPU)." Check the live store.
- Neural Engine: 38 TOPS is Apple's figure for M4 (May 2024). No TOPS figure was found for M4 Pro.
- macOS minimum for MPS: 14.0+ in the 2.14 docs, 15.0+ in the main-branch docs, and wheels tagged macOS 14. This Mac runs macOS 26.5.1, so it does not block anything.
- torch.compile on MPS: docs are silent, the Inductor file calls it an early prototype, and a 2023-24 README says it is unsupported. Lab 1 can test it.
- fp16 on MPS: a 2023-24 README says it does not work. Accelerate gates fp16 mixed precision on MPS at torch 2.5 or newer. Lab 5 decides.
- Lightning free hours: "80 free GPU hours" and "up to 30 free credits" appear on the same rendered page.
- Kaggle base weekly GPU quota is not on the docs page; secondary sites say about 30 hours a week. Kaggle phone verification comes from secondary sources only.
- AWS SageMaker Studio Lab: "no longer open to new customers." Third-party write-ups name a T4 and a sign-up cutoff date. Neither is confirmed.
- Colab GPU types: the FAQ says they vary. A 2023-24 repo README lists a Tesla V100 for the free tier.
- mac-ml-speed-test memory: its machine table gives 32 GB for the M1 Pro, but its text says "my M1 Pro with 18GB."
- nanoGPT numbers: M1 Pro reports range from 30 ms to 775 ms per iteration depending on a setting, and one Mac mini M1 reports 2.2 s. The README's "2-3X" names no chip.
- LoRA throughput: the newer mlx-lm docs and the older mlx-examples README both quote about 250 tokens/s for an M1 Max with 32 GB. The older README uses `lora.py`, which predates the `mlx_lm` CLI.
- CatBoost on Mac: the GPU page does not mention macOS or CUDA, so Mac GPU support is undocumented here, not confirmed absent.
- OpenMP: torch bundles its own libomp, and XGBoost and LightGBM load Homebrew's. Whether both load in one process, and what breaks, is untested (Lab 9).
- Apple's live spec page now shows M5 only. M4 Pro spec details come only from the 2024 archive and the 2024 newsroom.
- transformers: main has no `use_mps_device` argument; older docs may still mention it. Python patch level matters too: torchvision 0.29.1 refuses 3.14.1 but accepts 3.14.3, the version installed here.
- Still open: no M4 or M4 Pro timing, no MNIST CNN epoch timing on Apple silicon, no Oxford Pets fine-tune timing on Apple silicon, and the exact GPU memory cap on this Mac.

## Lab ideas from this topic

Each lab should run 1 to 10 minutes of training, with setup kept separate. Use `torch.mps.synchronize()` before each timing.

1. **CPU vs MPS, and why warm-up matters.** Concept: device sync and first-step cost. Dataset: MNIST, 3-layer CNN. Outcome: ms per step on CPU and MPS, first step vs later steps. Compare with the forum's 187 ms CPU and about 24 ms MPS (unverified).
2. **Batch-size knee.** Concept: throughput vs batch size. Dataset: CIFAR-100 subset, ResNet-18 at 32x32, one epoch on 5,000 images. Outcome: images per second at batch 16 to 512. The curve should flatten near 128 to 256, as in Table 6.1.
3. **Find the GPU memory ceiling.** Concept: unified memory and watermark ratios. Dataset: none (synthetic tensors). Outcome: print `torch.mps.recommended_max_memory()`, allocate 512 MB tensors until failure, then repeat with `PYTORCH_MPS_HIGH_WATERMARK_RATIO` at 1.0 and 1.7. Record the failure point against 24 GB.
4. **float64 and the fallback flag.** Concept: MPS op gaps. Dataset: none. Outcome: capture the float64 TypeError. Set `PYTORCH_ENABLE_MPS_FALLBACK=1`, find one op that errors without it, and time the CPU fallback.
5. **Mixed precision on MPS.** Concept: fp16 and bf16 autocast, speed vs accuracy. Dataset: CIFAR-10 subset, small CNN. Outcome: one epoch in float32, float16, and bfloat16, with the speedup and which dtypes run without error on torch 2.14.1.
6. **Determinism on MPS vs CPU.** Concept: nondeterministic kernels. Dataset: MNIST subset. Outcome: same seed run twice on MPS and once on CPU. Report the maximum weight difference, and note whether the 2.13 nondeterminism alert fires.
7. **Local vs cloud, end to end.** Concept: setup cost vs compute time. Dataset: CIFAR-10, one epoch. Outcome: time from start to first batch and per-epoch time on this Mac vs a Kaggle GPU notebook (P100 or T4 x2 per the docs). Find the run length where cloud wins.
8. **LoRA on 1B vs 3B 4-bit with mlx-lm.** Concept: QLoRA memory budget and tokens per second. Dataset: a small JSONL of your own Q&A, or the WikiSQL data in the mlx-lm docs. Outcome: tokens/s, time per iteration, and peak memory at `--batch-size 1 --num-layers 4`. Compare with 250 tokens/s on an M1 Max (docs).
9. **Two OpenMP runtimes in one process.** Concept: libomp duplication. Dataset: synthetic table, 10,000 rows. Outcome: import torch, then xgboost and lightgbm, in one script. Record any crash, warning, or wrong result, and list which libomp copies load (method to be confirmed in the lab). Write down the fix that works.
