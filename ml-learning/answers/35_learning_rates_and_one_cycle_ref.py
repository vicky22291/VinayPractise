"""35. Learning-rate finder and one-cycle. An xresnet18 from random weights on Imagenette at 128 px: lr_find picks
a rate, then 5 epochs of one-cycle at that rate, of a constant rate at the same peak, and of one-cycle at 10x it.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import contextlib, copy, io, itertools, math, statistics, sys, time
from functools import partial
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import numpy as np
import torch
from fastai.callback.schedule import minimum, valley
from fastai.vision.all import (Callback, CategoryBlock, DataBlock, GrandparentSplitter, ImageBlock, Normalize,
                               OptimWrapper, Resize, accuracy, get_image_files, imagenet_stats, parent_label,
                               vision_learner, xresnet18)
from matplotlib.figure import Figure

URL, TGZ_BYTES = "https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-160.tgz", 99_003_388
ROOT = labkit.DATA / "imagenette2-160"  # train/ and val/, one folder per class; shared with lab 02
OUT = labkit.DATA / "results" / "lab35"  # the lr_find plot; fastai's own lr_find keeps its temp files here too
SIZE, BATCH, N_STEPS = 128, 64, 100
WORKERS = 0  # fastai 2.8 sets workers to 0 on macOS: images load in this process
ADAMW = partial(torch.optim.AdamW, betas=(0.9, 0.99), eps=1e-5)  # fastai's Adam defaults, as a torch optimizer

def download():
    labkit.extract(labkit.fetch(URL, labkit.DATA / "imagenette2-160.tgz", size=TGZ_BYTES), labkit.DATA)
    print(f"HAVE {ROOT} {len(get_image_files(ROOT))} images", flush=True)

# --- CONCEPT start ---
def lr_find(model, loss_fn, opt, batches, start_lr=1e-7, end_lr=10, n_steps=100, beta=0.98):
    """A mock training run that raises the learning rate every step, then puts the model and optimizer back.

    First save copy.deepcopy(model.state_dict()) and copy.deepcopy(opt.state_dict()), and call model.train().
    Step i (i = 0 to n_steps - 1) takes the next (x, y) from `batches`, sets "lr" in every param group of `opt`
    to lr_i = start_lr * (end_lr / start_lr) ** (i / (n_steps - 1)), then trains once:
    loss = loss_fn(model(x), y), opt.zero_grad(), loss.backward(), opt.step().
    Smooth the losses: avg_i = beta * avg_(i-1) + (1 - beta) * loss_i with avg_(-1) = 0, then
    smooth_i = avg_i / (1 - beta ** (i + 1)). Stop after the first step whose smooth_i is above 4 times
    the lowest smooth so far, or is not finite, or when `batches` runs out.
    Then clear the gradients with opt.zero_grad() and load both saved copies back, so the model and the
    optimizer leave exactly as they came. Return (lrs, smooths): two lists of floats, one entry per step taken.
    """
    saved_model, saved_opt = copy.deepcopy(model.state_dict()), copy.deepcopy(opt.state_dict())
    model.train()
    lrs, smooths, avg, best = [], [], 0.0, math.inf
    for i, (x, y) in zip(range(n_steps), batches):
        lr = start_lr * (end_lr / start_lr) ** (i / (n_steps - 1))
        for group in opt.param_groups:
            group["lr"] = lr
        loss = loss_fn(model(x), y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        avg = beta * avg + (1 - beta) * loss.item()
        smooths.append(avg / (1 - beta ** (i + 1)))
        lrs.append(lr)
        best = min(best, smooths[-1])
        if smooths[-1] > 4 * best or not math.isfinite(smooths[-1]):
            break
    opt.zero_grad()
    model.load_state_dict(saved_model)
    opt.load_state_dict(saved_opt)
    return lrs, smooths

# --- CONCEPT end ---

def check():
    """A 20-row fixture: lr_find() against numpy (np.geomspace), pandas (ewm, adjust=True) and torch (state_dict)."""
    import pandas as pd
    g = torch.Generator().manual_seed(35)
    x = torch.randn(20, 3, generator=g)
    batches = [(x, x @ torch.tensor([[1.0], [-2.0], [0.5]]) + 0.1 * torch.randn(20, 1, generator=g))] * 100
    torch.manual_seed(35)
    model, raw = torch.nn.Linear(3, 1), []
    opt = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)

    def loss_fn(pred, target):  # mean squared error that also records each raw loss
        loss = torch.nn.functional.mse_loss(pred, target)
        raw.append(loss.item())
        return loss
    for xb, yb in batches[:3]:  # three real steps first, so the optimizer holds momentum to restore
        opt.zero_grad()
        loss_fn(model(xb), yb).backward()
        opt.step()
    raw.clear()
    model0, opt0 = copy.deepcopy(model.state_dict()), copy.deepcopy(opt.state_dict())
    lrs, smooths = lr_find(model, loss_fn, opt, iter(batches))
    n = len(lrs)
    assert len(smooths) == len(raw) == n and 1 < n < 100, f"this toy blows up before lr reaches 10: stop early, not at {n}"
    assert np.allclose(lrs, np.geomspace(1e-7, 10, 100)[:n], rtol=1e-9, atol=0), "rates differ from np.geomspace"
    ref = pd.Series(raw).ewm(alpha=1 - 0.98, adjust=True).mean().to_numpy()  # the bias-corrected moving average
    assert np.allclose(smooths, ref, rtol=1e-5), "smoothed losses differ from pandas ewm(alpha=0.02, adjust=True)"
    over = ~np.isfinite(ref) | (ref > 4 * np.minimum.accumulate(ref))
    assert over[-1] and not over[:-1].any(), "stop right after the first smoothed loss above 4x the lowest so far"
    assert all(torch.equal(v, model.state_dict()[k]) for k, v in model0.items()), "model weights not restored exactly"
    assert all(p.grad is None or not p.grad.any() for p in model.parameters()), "gradients left over: zero them"
    opt1 = opt.state_dict()
    assert opt1["param_groups"] == opt0["param_groups"], "optimizer rate or settings not restored"
    assert all(torch.equal(opt1["state"][k][name], t) for k, s in opt0["state"].items() for name, t in s.items()), \
        "optimizer momentum not restored exactly"
    print("check: PASS")

class EpochTimer(Callback):
    "Seconds per epoch (train plus validation), read twice: after torch.mps.synchronize(), and without it."
    def __init__(self, on):
        self.on, self.synced, self.unsynced = on, [], []
    def before_epoch(self):
        self.raw0 = time.perf_counter()  # read before the sync, so this clock does not wait for the GPU
        self.sync0 = labkit.clock(self.on)
    def after_epoch(self):
        raw1 = time.perf_counter()
        self.synced.append(labkit.clock(self.on) - self.sync0)
        self.unsynced.append(raw1 - self.raw0)

def save_curve(lrs, smooths, lr, valley_lr, seed):
    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()
    ax.plot(lrs, smooths)
    ax.axvline(lr, color="tab:red", linestyle="--", label="suggested: minimum / 10 (fastbook ch 5)")
    ax.axvline(valley_lr, color="tab:gray", linestyle=":", label="valley (fastai 2.8 default)")
    ax.set(xscale="log", xlabel="learning rate (log scale)", ylabel="smoothed training loss",
           title=f"lr_find: xresnet18, Imagenette 128 px, seed {seed}")
    ax.legend()
    path = io.BytesIO() if labkit.smoke() else OUT / f"lr_find_seed{seed}.png"  # smoke draws it, writes nothing
    fig.savefig(path, dpi=120, bbox_inches="tight")
    return path

def run(mode, dls, seed, device, epochs):
    labkit.seed_all(seed)  # every mode starts from the same random weights
    learn = vision_learner(dls, xresnet18, pretrained=False, metrics=accuracy, path=OUT,
                           opt_func=partial(OptimWrapper, opt=ADAMW))
    learn.model.to(device)
    learn.create_opt()  # one optimizer for lr_find() and the training after it
    n_steps = 20 if labkit.smoke() else N_STEPS  # smoke: a short curve, the same code path
    with contextlib.ExitStack() as stack:
        if labkit.smoke():  # smoke checks the plumbing only: fastai's own lr_find stands in for the TODO
            stack.enter_context(learn.no_bar())  # and hides fastai's progress bar and per-epoch table
            stack.enter_context(learn.no_logging())
            learn.lr_find(start_lr=1e-7, end_lr=10, num_it=n_steps, show_plot=False)
            lrs, smooths = [float(v) for v in learn.recorder.lrs], [float(v) for v in learn.recorder.losses]
        else:
            stream = (b for _ in itertools.count() for b in dls.train)  # training batches, epoch after epoch
            lrs, smooths = lr_find(learn.model, learn.loss_func, learn.opt.opt, stream, n_steps=n_steps)
        curve = torch.tensor(lrs[n_steps // 10:-5]), torch.tensor(smooths[n_steps // 10:-5])  # trimmed as fastai does
        lr = minimum(*curve, n_steps)[0]  # fastbook ch 5's rule: a tenth of the rate at the lowest smoothed loss
        valley_lr = valley(*curve, n_steps)[0]  # fastai 2.8's default rule, printed for comparison only
        peak, timer = 10 * lr if mode == "break" else lr, EpochTimer(device)
        labkit.seed_all(seed)  # every mode trains on the same batch order, crops and dropout draws
        if mode == "change":
            learn.fit(epochs, peak, cbs=timer)  # the same rate on every step: no warmup, no annealing
        else:
            learn.fit_one_cycle(epochs, peak, cbs=timer)  # peak / 25 up to peak, then down to peak / 1e5
    accs = [100 * float(row[-1]) for row in learn.recorder.values]  # validation accuracy after each epoch
    if mode == "baseline":
        path = save_curve(lrs, smooths, lr, valley_lr, seed)
        if not labkit.smoke():
            print(f"PLOT {path}", flush=True)
        labkit.result("baseline.lr_find_steps", len(lrs), unit="steps")
        labkit.result("baseline.suggested_lr", lr, unit="lr")
        labkit.result("baseline.valley_lr", valley_lr, unit="lr")
    else:
        labkit.result(f"{mode}.peak_lr", peak, unit="lr")
    step = {"baseline": "P1", "change": "P2", "break": "P3"}[mode]
    labkit.result(f"{step}.valid_acc", accs[-1], unit="percent", epochs=epochs, n=len(dls.valid_ds))
    if mode != "baseline" and (p1 := labkit.prior("P1.valid_acc")) is not None:
        labkit.result("P2.delta_vs_P1" if mode == "change" else "break.delta_vs_P1", accs[-1] - p1, unit="points")
    labkit.result(f"{mode}.acc_by_epoch", ",".join(f"{a:.2f}" for a in accs), unit="percent")
    if mode == "baseline":
        tags = dict(unit="s", device=device, batch=BATCH, warmup=1, n=len(timer.synced) - 1, stat="median")
        labkit.result("baseline.sec_per_epoch", statistics.median(timer.synced[1:]), **tags)
        labkit.result("baseline.sec_per_epoch_nosync", statistics.median(timer.unsynced[1:]), **tags)
    return timer

def main():
    args = labkit.start(lab=35, device=labkit.pick_device(), extra_modes=("check",))
    if args.mode in ("download", "check"):
        return download() if args.mode == "download" else check()
    if not (ROOT / "val").exists():
        sys.exit("no images: run python scripts/35_learning_rates_and_one_cycle.py --download first")
    OUT.mkdir(parents=True, exist_ok=True)
    every = 20 if labkit.smoke() else 1  # smoke: one image in 20, the same code path
    block = DataBlock(blocks=(ImageBlock, CategoryBlock), get_y=parent_label,
                      splitter=GrandparentSplitter(train_name="train", valid_name="val"),  # the official split
                      item_tfms=Resize(SIZE), batch_tfms=Normalize.from_stats(*imagenet_stats))
    dls = block.dataloaders(sorted(get_image_files(ROOT))[::every], bs=BATCH, num_workers=WORKERS, device=args.device)
    print(f"DATA device={dls.device} workers={WORKERS} batch={BATCH} size={SIZE} train={len(dls.train_ds)} "
          f"valid={len(dls.valid_ds)} classes={dls.c}", flush=True)
    for mode in (("baseline", "change", "break") if labkit.smoke() else (args.mode,)):
        timer = run(mode, dls, args.seed, args.device, epochs=2 if labkit.smoke() else 5)
        if labkit.smoke() and mode == "baseline":  # calibration: the second smoke epoch, scaled to all the images
            labkit.result("smoke.sec_per_full_epoch_est", timer.synced[-1] * every, smoke_ok=True, unit="s")

if __name__ == "__main__":  # safe if workers are turned on: macOS DataLoader workers re-import this file
    main()
