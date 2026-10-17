"""40. LoRA on a 4-bit model vs 5-shot prompting. Prompt or fine-tune the same 1B model, then score both on the same WikiSQL test items.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
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
import mlx.core as mx
from huggingface_hub import snapshot_download
from mlx.utils import tree_flatten
from mlx_lm import generate, load
from mlx_lm.lora import CONFIG_DEFAULTS, train_model
from mlx_lm.tuner.datasets import create_dataset
from mlx_lm.tuner.trainer import TrainingCallback
from mlx_lm.utils import DEFAULT_ALLOW_PATTERNS, get_total_parameters
from scipy.stats import binomtest

args = labkit.start(lab=40, device="mlx")
DATA, OUT = labkit.DATA / "wikisql", labkit.DATA / "results" / "lab40"
URL = "https://raw.githubusercontent.com/ml-explore/mlx-examples/main/lora/data/{}.jsonl"
SIZES = {"train": 272_537, "valid": 28_495, "test": 27_862}
MODEL, MODEL_3B = "mlx-community/Llama-3.2-1B-Instruct-4bit", "mlx-community/Llama-3.2-3B-Instruct-4bit"
FLAGS = dict(batch_size=4, num_layers=16, max_seq_length=512)  # every other training flag is mlx-lm's default
SMOKE = args.mode == "smoke"
ITERS = 20 if SMOKE else 300  # N = min(600, the iterations that fit 6 minutes), from the 20-iteration smoke
N_TEST, VAL_BATCHES, REPORT = (2, 2, 2) if SMOKE else (None, -1, 10)  # None: every test row; -1: every valid row
BREAK_ITERS, EVERY = (6, 3) if SMOKE else (1000, 25)
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


def score(model, tok, prompts, rows, name):
    """Greedy, at most 64 new tokens, first line; exact match after lowercasing and collapsing whitespace."""
    preds = [generate(model, tok, p, max_tokens=64).split("\n")[0] for p in prompts]
    norm = lambda s: " ".join(s.lower().split())  # noqa: E731
    ok = np.array([norm(p) == norm(r["gold"]) for p, r in zip(preds, rows)])
    if not SMOKE:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{name}-s{args.seed}.json").write_text(json.dumps({"ok": ok.tolist(), "preds": preds}))
    return ok


def lora(model, tok, train, valid, iters, repo=MODEL, **flags):
    """mlx_lm lora --train with the lab's flags, in process; returns the reports and the run's adapter config."""
    ns = types.SimpleNamespace(**{**CONFIG_DEFAULTS, **FLAGS, "model": repo, "data": str(DATA), "train": True,
                                  "iters": iters, "seed": args.seed, "save_every": iters + 1, "val_batches": VAL_BATCHES,
                                  "steps_per_report": REPORT, "adapter_path": str(OUT / f"adapters-{args.mode}-s{args.seed}"),
                                  **flags})
    sets = [create_dataset([{"text": r["text"]} for r in part], tok, ns) if part else [] for part in (train, valid)]
    labkit.seed_all(args.seed)  # the same LoRA init and batch order for every model at this seed
    log, callback = types.SimpleNamespace(train=[], val=[]), TrainingCallback()  # keeps every report mlx-lm sends
    callback.on_train_loss_report, callback.on_val_loss_report = log.train.append, log.val.append
    with contextlib.redirect_stdout(io.StringIO()) if SMOKE else contextlib.nullcontext():
        train_model(ns, model, *sets, training_callback=callback)
    return log, json.loads((Path(ns.adapter_path) / "adapter_config.json").read_text())


def baseline(rows):
    model, tok = load(MODEL)
    idx = range(5) if args.seed == 0 else np.random.default_rng(args.seed).choice(len(rows["train"]), 5, replace=False)
    shots, test = "".join(rows["train"][i]["text"] + "\n\n" for i in idx), rows["test"][:N_TEST]
    prompts = [shots + r["prompt"] for r in test]
    ok = score(model, tok, prompts, test, "baseline")
    report("baseline", {"P1.exact_match_pct": 100 * ok.mean(),
                        "baseline.prompt_tokens": np.mean([len(tok.encode(p)) for p in prompts])},
           {"P1.exact_match_pct": {"n": len(ok), "shots": "-".join(str(i) for i in idx)}})
    return ok


def change(rows, prompt_ok):
    model, tok = load(MODEL)
    log, config = lora(model, tok, rows["train"], [], ITERS)
    if SMOKE:  # calibration for N: seconds per training iteration after the first report window
        labkit.result("smoke.sec_per_iter", 1 / np.median([x["iterations_per_second"] for x in log.train[1:]]),
                      smoke_ok=True, unit="s", device="mlx", batch=4, warmup=REPORT, n=ITERS - REPORT, stat="median")
    trainable_pct = 100 * sum(v.size for _, v in tree_flatten(model.trainable_parameters())) / get_total_parameters(model)
    test = rows["test"][:N_TEST]
    ok = score(model.eval(), tok, [r["prompt"] for r in test], test, "change")
    del model
    mx.clear_cache()
    model_3b, tok_3b = load(MODEL_3B)  # the same flags, seed and batches, for 3 report windows
    log_3b, _ = lora(model_3b, tok_3b, rows["train"], [], 3 * REPORT, repo=MODEL_3B, adapter_path=str(OUT / "adapters-3b"))
    early = [np.median([x["tokens_per_second"] for x in lg.train[1:3]]) for lg in (log, log_3b)]  # windows 2 and 3
    right, wrong = int((ok & ~prompt_ok).sum()), int((~ok & prompt_ok).sum())  # paired flips, each way
    diff = ok.astype(float) - prompt_ok.astype(float)
    timing = dict(device="mlx", batch=4, warmup=REPORT, stat="median")
    report("change", {
        "P2.em_change_pts": 100 * diff.mean(), "P2.flips_to_right": right, "P2.flips_to_wrong": wrong,
        "change.exact_match_pct": 100 * ok.mean(),
        "change.sign_test_p": binomtest(right, right + wrong).pvalue if right + wrong else 1.0,
        "change.ci95_width_pts": 100 * 2 * 1.96 * diff.std(ddof=1) / np.sqrt(len(diff)),
        "change.prompt_tokens": np.mean([len(tok.encode(r["prompt"])) for r in test]),
        "change.trainable_pct": trainable_pct, "change.lora_rank": config["lora_parameters"]["rank"],
        "change.lora_scale": config["lora_parameters"]["scale"], "change.peak_mem_gb": log.train[-1]["peak_memory"],
        "change.train_tok_per_s": np.median([x["tokens_per_second"] for x in log.train[1:]]),
        "change.tok_s_3b_share": early[1] / early[0]},
        {"P2.em_change_pts": {"n": len(ok), "iters": ITERS}, "change.train_tok_per_s": dict(timing, n=ITERS - REPORT),
         "change.tok_s_3b_share": dict(timing, n=2 * REPORT)})


def break_(rows):
    model, tok = load(MODEL)
    log, _ = lora(model, tok, rows["train"][:100], rows["valid"], BREAK_ITERS, steps_per_eval=EVERY)
    its, loss = [v["iteration"] + 1 for v in log.val], [v["val_loss"] for v in log.val]  # iterations as mlx-lm prints them
    best = int(np.argmin(loss))
    report("break", {"P3.best_iter": its[best], "break.val_loss_start": loss[0], "break.val_loss_min": loss[best],
                     "break.val_loss_final": loss[-1], "break.train_loss_final": log.train[-1]["train_loss"]},
           {"P3.best_iter": {"every": EVERY, "iters": BREAK_ITERS}})


if __name__ == "__main__":
    saved = OUT / f"baseline-s{args.seed}.json"
    if args.mode == "download":
        download()
    elif args.mode == "change" and not saved.exists():
        print(f"missing {saved}: run python scripts/40_lora_vs_prompting.py --baseline --seed {args.seed} first")
        sys.exit(2)
    else:
        rows = load_data()
        prompt_ok = baseline(rows) if args.mode in ("smoke", "baseline") else None
        if args.mode in ("smoke", "change"):
            change(rows, prompt_ok if SMOKE else np.array(json.loads(saved.read_text())["ok"]))
        if args.mode in ("smoke", "break"):
            break_(rows)
