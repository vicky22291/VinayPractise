"""Lab 35 rebuild: the learning-rate finder, written from memory.

Write the body (about 20 lines), then run: python rebuild/35_lr_find.py
check() compares with numpy (np.geomspace), pandas (ewm with adjust=True) and torch (state_dict, torch.equal),
never with the lab's results.
"""
import copy
import math

import numpy as np
import pandas as pd
import torch
from torch import nn


def lr_find(model, loss_fn, opt, batches, start_lr=1e-7, end_lr=10, n_steps=100, beta=0.98):
    """The learning-rate range test: one mock training run whose rate grows every step, then a full restore.

    The rate grows by the same factor every step, from start_lr at step 0 to end_lr at step n_steps - 1.
    Each step sets the rate in every param group of `opt`, trains once on the next (x, y) from `batches`,
    and records the rate and the bias-corrected moving average of the losses so far (beta on the old average).
    Stop after the first step whose smoothed loss is above 4 times the lowest so far, or is not finite,
    or when `batches` runs out. At the end clear the gradients and put the model and the optimizer back
    exactly as they came. Return (lrs, smoothed losses): two lists of floats.
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


def check():
    g = torch.Generator().manual_seed(0)
    x = torch.randn(256, 4, generator=g)
    y = (x[:, :1] - 2 * x[:, 1:2] + 0.1 * torch.randn(256, 1, generator=g))
    batches = [(x[k:k + 64], y[k:k + 64]) for k in range(0, 256, 64)] * 25  # 100 mini-batches of 64 rows
    raw = []

    def loss_fn(pred, target):  # mean squared error that also records each raw loss
        loss = nn.functional.mse_loss(pred, target)
        raw.append(loss.item())
        return loss

    torch.manual_seed(0)
    model = nn.Sequential(nn.Linear(4, 16), nn.BatchNorm1d(16), nn.ReLU(), nn.Linear(16, 1))
    opt = torch.optim.SGD(model.parameters(), lr=1e-3, momentum=0.9)
    for xb, yb in batches[:2]:  # two real steps first, so the optimizer holds momentum buffers to restore
        opt.zero_grad()
        loss_fn(model(xb), yb).backward()
        opt.step()
    raw.clear()
    model0, opt0 = copy.deepcopy(model.state_dict()), copy.deepcopy(opt.state_dict())
    lrs, smooths = lr_find(model, loss_fn, opt, iter(batches))
    n = len(lrs)
    assert len(smooths) == len(raw) == n, f"one rate and one smoothed loss per step: {n}, {len(smooths)}, {len(raw)}"
    assert 1 < n < 100, f"this toy blows up before the rate reaches 10, so the finder must stop early, not at step {n}"
    assert np.allclose(lrs, np.geomspace(1e-7, 10, 100)[:n], rtol=1e-9, atol=0), "rates differ from np.geomspace"
    ref = pd.Series(raw).ewm(alpha=1 - 0.98, adjust=True).mean().to_numpy()  # the bias-corrected moving average
    assert np.allclose(smooths, ref, rtol=1e-5), "smoothed losses differ from pandas ewm(alpha=0.02, adjust=True)"
    over = ~np.isfinite(ref) | (ref > 4 * np.minimum.accumulate(ref))
    assert over[-1] and not over[:-1].any(), "stop right after the first smoothed loss above 4x the lowest so far"
    state = model.state_dict()  # weights and the BatchNorm running statistics
    assert all(torch.equal(state[k], v) for k, v in model0.items()), "model state not restored exactly"
    assert all(p.grad is None or not p.grad.any() for p in model.parameters()), "gradients left over: zero them"
    opt1 = opt.state_dict()
    assert opt1["param_groups"] == opt0["param_groups"], "optimizer rate or settings not restored"
    assert all(torch.equal(opt1["state"][k][name], t) for k, s in opt0["state"].items() for name, t in s.items()), \
        "optimizer momentum buffers not restored exactly"
    raw.clear()
    lrs, _ = lr_find(model, loss_fn, opt, iter(batches), start_lr=1e-6, end_lr=1e-4, n_steps=30)
    assert len(lrs) == 30, f"at small rates nothing blows up, so all 30 steps run, not {len(lrs)}"
    assert np.allclose(lrs, np.geomspace(1e-6, 1e-4, 30), rtol=1e-9, atol=0), "start_lr, end_lr or n_steps ignored"
    print("check: PASS")


if __name__ == "__main__":
    check()
