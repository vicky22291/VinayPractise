"""39. A GPT from scratch: attention, the causal mask and sampling. nanoGPT's character GPT, trained on MPS.

Modes: --download, --smoke, --baseline (P1, P1b), --change (P2), --break (P3).
nanoGPT's model.py (in ~/ml-data/nanoGPT/) is the worked example; the loop and settings are its train.py's.
"""
import importlib.util
import math
import pickle
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import numpy as np
import torch

COMMIT = "3adf61e154c3fe3fca428ad6bc3818b27a3b8291"
FILES = {"train.py": 14857, "model.py": 16345, "sample.py": 3942, "configurator.py": 1758,
         "config/train_shakespeare_char.py": 1132, "data/shakespeare_char/prepare.py": 2344}
NANO, NOMASK, OUT = labkit.DATA / "nanoGPT", labkit.DATA / "nanoGPT-nomask", labkit.DATA / "results" / "lab39"
DATA_DIR = NANO / "data" / "shakespeare_char"
MASK_LINE = "            att = att.masked_fill(self.bias[:,:,:T,:T] == 0, float('-inf'))\n"
N = 350  # max_iters = lr_decay_iters: set by the build from --smoke so the whole --baseline fits in 6 minutes
# config/train_shakespeare_char.py: the model, batch, context, learning-rate schedule, beta2 and eval interval
MODEL = dict(n_layer=6, n_head=6, n_embd=384, block_size=256, dropout=0.2)
BATCH, BLOCK, LR, MIN_LR, LR_WARMUP, BETA2, EVAL_INTERVAL = 64, MODEL["block_size"], 1e-3, 1e-4, 100, 0.99, 250
BIAS, WEIGHT_DECAY, BETA1, CLIP = False, 0.1, 0.9, 1.0  # train.py's defaults, which the config file does not change
WARMUP = 2  # timing: the first WARMUP iterations are left out of the median
SIZES = {"full": dict(iters=N, eval_iters=20, chars=500, cpu_iters=20, break_iters=300),
         "smoke": dict(iters=20, eval_iters=2, chars=20, cpu_iters=1, break_iters=3)}


def download():
    for name, size in FILES.items():
        labkit.fetch(f"https://raw.githubusercontent.com/karpathy/nanoGPT/{COMMIT}/{name}", NANO / name, size=size)
    labkit.fetch("https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
                 DATA_DIR / "input.txt", size=1115394)
    with labkit.locked(DATA_DIR / "meta.pkl"):  # nanoGPT's own step: writes train.bin, val.bin and meta.pkl
        if not (DATA_DIR / "meta.pkl").exists():
            subprocess.run([sys.executable, "prepare.py"], cwd=DATA_DIR, check=True, stdout=subprocess.DEVNULL)
    src = (NANO / "model.py").read_text()
    assert src.count("is_causal=True") == 1 and src.count(MASK_LINE) == 1, "not the pinned model.py"
    NOMASK.mkdir(parents=True, exist_ok=True)  # --break trains this copy, with the causal mask deleted
    (NOMASK / "model.py").write_text(src.replace("is_causal=True", "is_causal=False").replace(MASK_LINE, ""))
    for path in (DATA_DIR / "train.bin", DATA_DIR / "val.bin", DATA_DIR / "meta.pkl", NOMASK / "model.py"):
        print(f"HAVE {path} {path.stat().st_size / 1e6:.2f} MB", flush=True)


def build(src, device, meta):
    """nanoGPT's GPT from src/model.py: nanoGPT/ for --baseline and --change, nanoGPT-nomask/ for --break."""
    spec = importlib.util.spec_from_file_location(f"model_{src.name}", src / "model.py")
    nano = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nano)
    return nano.GPT(nano.GPTConfig(**MODEL, bias=BIAS, vocab_size=meta["vocab_size"])).to(device)


def get_batch(ids, device):
    """train.py's get_batch: BATCH random windows of BLOCK characters (x) and the windows one character later (y)."""
    ix = torch.randint(len(ids) - BLOCK, (BATCH,)).tolist()
    x, y = torch.stack([ids[i:i + BLOCK] for i in ix]), torch.stack([ids[i + 1:i + 1 + BLOCK] for i in ix])
    return x.to(device), y.to(device)


def lr_at(it):
    """train.py's schedule: linear warmup for LR_WARMUP iterations, then cosine decay to MIN_LR at N."""
    if it < LR_WARMUP:
        return LR * (it + 1) / (LR_WARMUP + 1)
    return MIN_LR + 0.5 * (1 + math.cos(math.pi * min(1.0, (it - LR_WARMUP) / (N - LR_WARMUP)))) * (LR - MIN_LR)


@torch.no_grad()
def estimate_loss(model, data, device, eval_iters):
    """train.py's estimate_loss: mean loss over eval_iters random batches of each split, dropout off."""
    model.eval()
    losses = [[model(*get_batch(data[s], device))[1].item() for _ in range(eval_iters)] for s in ("train", "val")]
    model.train()
    return [float(np.mean(split)) for split in losses]


def train(model, data, iters, device, eval_iters, tag, names=None):
    """train.py's loop: AdamW, gradient clipping, an eval every EVAL_INTERVAL iterations, at 300 and at the end."""
    opt = model.configure_optimizers(WEIGHT_DECAY, LR, (BETA1, BETA2), device)
    evals, times, batch = {}, [], get_batch(data["train"], device)
    for it in range(iters + 1):
        if eval_iters and (it % EVAL_INTERVAL == 0 or it in (300, iters)):
            evals[it] = estimate_loss(model, data, device, eval_iters)
            labkit.result((names or {}).get(it, f"{tag}.val_loss_{it}"), evals[it][1], unit="nats")
        if it == iters:
            return evals, times
        for group in opt.param_groups:
            group["lr"] = lr_at(it)
        t0 = labkit.clock(device)
        _, loss = model(*batch)
        batch = get_batch(data["train"], device)  # the next batch, fetched where train.py fetches it
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP)
        opt.step()
        opt.zero_grad(set_to_none=True)
        times.append(labkit.clock(device) - t0)


@torch.no_grad()
def matches_causal_formula(model, device):
    """Layer 0's attention as the model runs it, against model.py's slow path written out here."""
    attn, (B, T, C) = model.eval().transformer.h[0].attn, (2, 32, MODEL["n_embd"])
    x = torch.randn(B, T, C, generator=torch.Generator().manual_seed(0)).to(device)
    q, k, v = (t.view(B, T, attn.n_head, C // attn.n_head).transpose(1, 2) for t in attn.c_attn(x).split(C, dim=2))
    # Q: why divide by sqrt(head_size)?
    att = (q @ k.transpose(-2, -1)) / math.sqrt(k.size(-1))
    # Q: what does the tril mask stop?
    att = att.masked_fill(torch.tril(torch.ones(T, T, device=device)) == 0, float("-inf"))
    by_hand = attn.c_proj((torch.softmax(att, dim=-1) @ v).transpose(1, 2).reshape(B, T, C))
    return torch.allclose(attn(x), by_hand, atol=1e-5)


@torch.no_grad()
def sample(model, meta, words, size, temperature, device, seed, name):
    """GPT.generate's loop from a newline, then the share of the sample's words that are words of the train split."""
    torch.manual_seed(seed)  # the same random draws at every temperature
    idx = torch.tensor([[meta["stoi"]["\n"]]], device=device)
    for _ in range(size["chars"]):
        logits, _ = model.eval()(idx[:, -BLOCK:])
        # Q: what does temperature do to the logits?
        probs = torch.softmax(logits[:, -1, :] / temperature, dim=-1)
        idx = torch.cat([idx, torch.multinomial(probs, 1)], dim=1)
    text = "".join(meta["itos"][i] for i in idx[0, 1:].tolist())
    if not labkit.smoke():
        print(f"SAMPLE {name} temperature={temperature}\n{text}\n", flush=True)
    found = [w in words for w in text.split()]  # words split on whitespace, punctuation and case kept, matched exactly
    labkit.result(name, sum(found) / max(len(found), 1), unit="fraction", temperature=temperature,
                  chars=size["chars"], words=len(found))


def main():
    args = labkit.start(lab=39, device=labkit.pick_device())
    device, seed, size = args.device, args.seed, SIZES["smoke" if labkit.smoke() else "full"]
    if args.mode == "download":
        return download()
    if not (NOMASK / "model.py").exists():
        sys.exit("missing nanoGPT: run python scripts/39_gpt_from_scratch.py --download")
    meta = pickle.loads((DATA_DIR / "meta.pkl").read_bytes())  # nanoGPT's character tables
    data = {s: torch.from_numpy(np.fromfile(DATA_DIR / f"{s}.bin", dtype=np.uint16).astype(np.int64))
            for s in ("train", "val")}
    words = set("".join(meta["itos"][i] for i in data["train"].tolist()).split())  # the train split's words
    ckpt = OUT / ("ckpt-smoke.pt" if labkit.smoke() else f"ckpt-seed{seed}.pt")
    timing = dict(batch=BATCH, warmup=WARMUP, stat="median")
    steps = ("baseline", "change", "break") if labkit.smoke() else (args.mode,)
    if "baseline" in steps:
        model = build(NANO, device, meta)
        evals, times = train(model, data, size["iters"], device, size["eval_iters"], "baseline",
                             names={0: "P1.val_loss_step0", size["iters"]: "P1b.val_loss_final"})
        if 300 in evals:
            labkit.result("baseline.train_loss_300", evals[300][0], unit="nats")
        s_iter, n = float(np.median(times[WARMUP:])), len(times) - WARMUP  # --smoke shows s_iter: N comes from it
        labkit.result("baseline.mps_s_per_iter", s_iter, smoke_ok=True, unit="s", device=device, n=n, **timing)
        labkit.result("baseline.mps_tokens_per_s", BATCH * BLOCK / s_iter, unit="tokens/s", device=device, n=n, **timing)
        OUT.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), ckpt)
        sample(model, meta, words, size, 1.0, device, seed, "baseline.word_share_t10")
        labkit.result("baseline.attention_is_causal", matches_causal_formula(model, device))
        _, cpu = train(build(NANO, "cpu", meta), data, size["cpu_iters"] + WARMUP, "cpu", 0, "cpu")
        labkit.result("baseline.cpu_tokens_per_s", BATCH * BLOCK / float(np.median(cpu[WARMUP:])), unit="tokens/s",
                      device="cpu", n=size["cpu_iters"], **timing)
        labkit.result("baseline.max_iters", size["iters"])
    if "change" in steps:
        if not ckpt.exists():
            sys.exit(f"missing {ckpt}: run python scripts/39_gpt_from_scratch.py --baseline --seed {seed}")
        model = build(NANO, device, meta)
        model.load_state_dict(torch.load(ckpt, map_location=device))
        for t, name in ((0.5, "change.word_share_t05"), (1.0, "change.word_share_t10"), (1.5, "P2.word_share_t15")):
            sample(model, meta, words, size, t, device, seed, name)
    if "break" in steps:
        model = build(NOMASK, device, meta)
        evals, _ = train(model, data, size["break_iters"], device, size["eval_iters"], "break")
        loss_300, base_300 = evals[size["break_iters"]][0], labkit.prior("baseline.train_loss_300")
        labkit.result("P3.train_loss_300", loss_300, unit="nats", iters=size["break_iters"])
        if base_300 is not None:
            labkit.result("P3.delta_train_loss_300", loss_300 - base_300, unit="nats")
        sample(model, meta, words, size, 1.0, device, seed, "break.word_share_t10")
        labkit.result("break.attention_is_causal", matches_causal_formula(model, device))


if __name__ == "__main__":
    main()
