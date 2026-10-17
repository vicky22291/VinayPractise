"""11 rebuild: per-item losses and the top k, a label flip that always changes the class, and a category tally.

Write the three bodies from memory, then run: python rebuild/11_top_losses.py
check() compares with PyTorch and pandas on synthetic data, never with the lab's results.
"""
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F


def top_losses(logits, targets, k):
    """Return (losses, idx): the k largest per-item cross-entropy losses, highest first, and their rows.

    loss_i = -log_softmax(logits_i)[targets_i]. Sort with argsort, descending.
    """
    raise NotImplementedError("write this from memory")


def flip_labels(targets, n_classes, frac, seed):
    """Return (new_targets, rows): exactly round(frac * n) random rows, each moved to another class at random."""
    raise NotImplementedError("write this from memory")


def tally(categories):
    """Return {category: (count, share)} for a list with one category per example, largest count first."""
    raise NotImplementedError("write this from memory")


def check():
    """1,000 synthetic rows of 37 classes; every tenth row has logits 100 times larger."""
    g = torch.Generator().manual_seed(0)
    logits = torch.randn(1000, 37, generator=g) * torch.where(torch.arange(1000) % 10 == 0, 100.0, 1.0).view(-1, 1)
    targets = torch.randint(0, 37, (1000,), generator=g)
    want = F.cross_entropy(logits, targets, reduction="none")
    losses, idx = top_losses(logits, targets, 50)
    assert torch.allclose(losses, want[idx], rtol=1e-5, atol=1e-5), "losses differ from F.cross_entropy"
    assert torch.equal(idx, want.topk(50).indices), "idx is not the top 50 rows, highest loss first"
    y = targets.numpy()
    new, rows = flip_labels(y, 37, 0.10, seed=0)
    assert len(rows) == 100 and np.array_equal(np.sort(rows), np.flatnonzero(new != y)), "flip exactly 10% of rows"
    assert ((new >= 0) & (new < 37)).all(), "a flipped label must still be one of the 37 classes"
    cats = ["x"] * 11 + ["y"] * 30 + ["z"] * 19
    want_counts, got = pd.Series(cats).value_counts(), tally(cats)
    assert list(got) == list(want_counts.index), "tally order: largest count first"
    for c, n in want_counts.items():
        assert got[c][0] == n and abs(got[c][1] - n / len(cats)) < 1e-12, f"tally[{c!r}]"
    print("check: PASS")


if __name__ == "__main__":
    check()
