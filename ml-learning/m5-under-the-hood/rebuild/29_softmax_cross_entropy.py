"""Lab 29 rebuild: softmax and cross-entropy from logits, written from memory.

Write both bodies (a few lines each), then run: python rebuild/29_softmax_cross_entropy.py
check() compares with torch.softmax and F.cross_entropy, never with the lab's results.
"""
import torch
import torch.nn.functional as F


def softmax(logits):
    """Row-wise softmax of an (n, k) tensor of logits: every row sums to 1.

    Subtract the row maximum before exp, so a logit of 1,000 does not overflow.
    Plain tensor ops only (no torch.softmax).
    """
    raise NotImplementedError("write this from memory")


def cross_entropy(logits, targets):
    """Mean over the batch of minus the log softmax probability of the right class.

    logits: (n, k) float tensor. targets: (n,) class ids. Use logsumexp with the row
    maximum subtracted (no F.cross_entropy, F.log_softmax or torch.logsumexp).
    """
    raise NotImplementedError("write this from memory")


def check():
    g = torch.Generator().manual_seed(29)
    logits = 3 * torch.randn(20, 10, generator=g, dtype=torch.float64)
    logits[:5] += 1000  # exp(1000) overflows, so a naive version returns nan on these rows
    logits[5, 3] = 1000
    targets = torch.randint(0, 10, (20,), generator=g)
    p = softmax(logits)
    assert torch.allclose(p, torch.softmax(logits, dim=1), rtol=0, atol=1e-6), "softmax differs from torch.softmax"
    assert torch.allclose(p.sum(dim=1), torch.ones(20, dtype=torch.float64)), "rows do not sum to 1"
    mine, ref = cross_entropy(logits, targets).item(), F.cross_entropy(logits, targets).item()
    assert abs(mine - ref) < 1e-6, f"cross_entropy {mine} vs F.cross_entropy {ref}"
    print("check: PASS")


if __name__ == "__main__":
    check()
