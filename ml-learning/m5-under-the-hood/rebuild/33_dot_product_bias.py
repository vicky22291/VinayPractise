"""Rebuild 33: DotProductBias and one SGD step with an explicit L2 term, from memory.

Write the bodies of DotProductBias and train_step, then run: python rebuild/33_dot_product_bias.py
check() compares with torch.optim.SGD(weight_decay=wd) on synthetic ratings, never with the lab's results.
"""
import copy

import torch
from torch import nn


class DotProductBias(nn.Module):
    """One row of n_factors numbers and one bias per user and per item, every number drawn from N(0, 0.01).

    forward(users, items) takes two LongTensors of the same length and returns one predicted rating per pair:
    sigmoid_range(user row . item row + user bias + item bias, 0, 5.5), which is 5.5 * sigmoid(score).
    """

    def __init__(self, n_users, n_items, n_factors=50):
        super().__init__()
        raise NotImplementedError("write this from memory")

    def forward(self, users, items):
        raise NotImplementedError("write this from memory")


def train_step(model, opt, users, items, ratings, wd):
    """One step of plain SGD on one batch. opt is torch.optim.SGD with no weight_decay of its own.

    The loss is the mean squared error plus an explicit L2 term, (wd / 2) * the sum of every parameter squared,
    so every gradient gains wd * w. Zero the gradients, backpropagate, step, and return the loss as a float.
    """
    raise NotImplementedError("write this from memory")


def check():
    torch.manual_seed(0)
    n_users, n_items, k, n = 20, 30, 8, 512
    users, items = torch.randint(0, n_users, (n,)), torch.randint(0, n_items, (n,))
    taste = torch.randn(n_users, 2) @ torch.randn(2, n_items)  # synthetic ratings from a rank-2 taste model
    ratings = (3.5 + taste[users, items] + 0.3 * torch.randn(n)).clamp(1, 5)
    model = DotProductBias(n_users, n_items, k)
    flat = torch.cat([p.detach().flatten() for p in model.parameters()])
    assert flat.numel() == (n_users + n_items) * (k + 1), "expected one k-number row and one bias per user and per item"
    assert abs(flat.mean()) < 0.003 and abs(flat.std() - 0.01) < 0.002, "the starting values are not N(0, 0.01)"
    out = model(users, items)
    assert out.shape == (n,), f"forward returned shape {tuple(out.shape)}, expected one rating per pair"
    assert ((out > 0) & (out < 5.5)).all() and (out - 2.75).abs().max() < 0.15, "at the start, outputs sit near 2.75"
    big = copy.deepcopy(model)
    with torch.no_grad():
        for p in big.parameters():
            p.mul_(100)
    out = big(users, items)
    assert out.min() >= 0 and out.max() <= 5.5, "outputs left the range 0 to 5.5"
    assert out.min() < 0.5 and out.max() > 5.0, "large scores should reach both ends of 0 to 5.5"
    a, b = copy.deepcopy(model), copy.deepcopy(model)
    opt_a = torch.optim.SGD(a.parameters(), lr=1.0)
    opt_b = torch.optim.SGD(b.parameters(), lr=1.0, weight_decay=0.1)  # the library's L2
    losses = []
    for _ in range(20):
        losses.append(train_step(a, opt_a, users, items, ratings, wd=0.1))
        opt_b.zero_grad()
        nn.functional.mse_loss(b(users, items), ratings).backward()
        opt_b.step()
    gap = max((pa - pb).abs().max().item() for pa, pb in zip(a.parameters(), b.parameters()))
    assert gap < 1e-6, f"the explicit L2 term under SGD differs from SGD(weight_decay=wd) by {gap:.2e}"
    assert losses[-1] < 0.9 * losses[0], f"the loss did not fall over 20 steps: {losses[0]:.3f} to {losses[-1]:.3f}"
    print("check: PASS")


if __name__ == "__main__":
    check()
