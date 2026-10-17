"""40. LoRA on a 4-bit model vs 5-shot prompting. Prompt or fine-tune the same 1B model, then score both on the same WikiSQL test items.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Level S starter: download(), load_data() and report() are written, and --download and --smoke work.
--baseline, --change and --break need the harness: write the protocol in the lab file first, then the AI writes it.
--seed 0 uses the first 5 train rows as the shots; any other seed draws 5 train rows at random.
"""
import contextlib
import io
import json
import sys
import types
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, mlx and mlx_lm: it sets cache defaults
import numpy as np
import mlx.core as mx  # noqa: F401  imported before labkit.start, so its random seed is set
from huggingface_hub import snapshot_download
from huggingface_hub.utils import disable_progress_bars, logging as hf_logging
from mlx_lm import generate, load
from mlx_lm.lora import CONFIG_DEFAULTS, train_model
from mlx_lm.tuner.datasets import create_dataset
from mlx_lm.tuner.trainer import TrainingCallback
from mlx_lm.utils import DEFAULT_ALLOW_PATTERNS

args = labkit.start(lab=40, device="mlx")
disable_progress_bars()  # no Hugging Face download bars: --download prints paths and sizes only
hf_logging.set_verbosity_error()  # and no Hub notice about requests without a token
DATA, OUT = labkit.DATA / "wikisql", labkit.DATA / "results" / "lab40"
URL = "https://raw.githubusercontent.com/ml-explore/mlx-examples/main/lora/data/{}.jsonl"
SIZES = {"train": 272_537, "valid": 28_495, "test": 27_862}
MODEL, MODEL_3B = "mlx-community/Llama-3.2-1B-Instruct-4bit", "mlx-community/Llama-3.2-3B-Instruct-4bit"
FLAGS = dict(batch_size=4, num_layers=16, max_seq_length=512)  # every other training flag is mlx-lm's default
ITERS = 300  # N = min(600, the iterations that fit 6 minutes after the run's fixed cost of loading,
#              scoring 100 items and the 3B run), rounded down for margin; seconds per iteration from --smoke
CONTRACT = {  # mode -> RESULT name -> unit
    "baseline": {"P1.exact_match_pct": "pct", "baseline.prompt_tokens": "tokens"},
    "change": {"P2.em_change_pts": "pts", "P2.flips_to_right": "items", "P2.flips_to_wrong": "items",
               "change.exact_match_pct": "pct", "change.sign_test_p": "p", "change.ci95_width_pts": "pts",
               "change.prompt_tokens": "tokens", "change.trainable_pct": "pct", "change.lora_rank": "r",
               "change.lora_scale": "scale", "change.peak_mem_gb": "GB", "change.train_tok_per_s": "tok/s",
               "change.tok_s_3b_share": "fraction"},
    "break": {"P3.best_iter": "iteration", "break.val_loss_start": "nats", "break.val_loss_min": "nats",
              "break.val_loss_final": "nats", "break.train_loss_final": "nats"},
}


def download():
    for name, size in SIZES.items():
        labkit.fetch(URL.format(name), DATA / f"{name}.jsonl", size=size)
    for repo in (MODEL, MODEL_3B):
        with labkit.locked(labkit.DATA / "hf" / repo.replace("/", "--")):
            path = Path(snapshot_download(repo, allow_patterns=DEFAULT_ALLOW_PATTERNS))
        print(f"HAVE {path} {sum(f.stat().st_size for f in path.glob('*.safetensors')) / 1e6:.1f} MB", flush=True)


def load_data():
    """Every train, valid and test row, split after its last 'A:' into the prompt and the gold SQL."""
    rows = {}
    for name in SIZES:
        texts = [json.loads(line)["text"] for line in open(DATA / f"{name}.jsonl")]
        rows[name] = [dict(text=t, prompt=t[:t.rindex("\nA:") + 3], gold=t[t.rindex("\nA:") + 3:].strip()) for t in texts]
    return rows


def report(mode, values, tags=None):
    """The RESULT contract: one line per name in CONTRACT[mode], in its unit (a missing name raises KeyError)."""
    for name, unit in CONTRACT[mode].items():
        labkit.result(name, values[name], unit=unit, **(tags or {}).get(name, {}))


def smoke():
    """Plumbing only: the data loads, the 1B model generates, mlx-lm trains for 20 iterations, report() parses."""
    rows = load_data()
    model, tok = load(MODEL)
    generate(model, tok, rows["test"][0]["prompt"], max_tokens=64)
    ns = types.SimpleNamespace(**{**CONFIG_DEFAULTS, **FLAGS, "model": MODEL, "data": str(DATA), "train": True,
                                  "iters": 20, "steps_per_report": 2, "save_every": 21, "seed": args.seed,
                                  "adapter_path": str(OUT / "adapters-smoke")})
    reports, callback = [], TrainingCallback()
    callback.on_train_loss_report = reports.append
    with contextlib.redirect_stdout(io.StringIO()):  # silence mlx-lm's progress output
        train_model(ns, model, create_dataset([{"text": r["text"]} for r in rows["train"]], tok, ns), [],
                    training_callback=callback)
    labkit.result("smoke.sec_per_iter", 1 / np.median([x["iterations_per_second"] for x in reports[1:]]),
                  smoke_ok=True, unit="s", device="mlx", batch=4, warmup=2, n=18, stat="median")
    for mode, names in CONTRACT.items():
        report(mode, dict.fromkeys(names, 0))


if __name__ == "__main__":
    if args.mode == "download":
        download()
    elif args.mode == "smoke":
        smoke()
    else:
        raise NotImplementedError("write the harness: see the lab file")
