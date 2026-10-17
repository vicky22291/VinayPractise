"""Rebuild 40: a LoRA linear layer, its trainable share, and exact match, in PyTorch. Write the bodies from memory.

Run from the module folder: python rebuild/40_lora_linear.py
check() compares your layer with torch's own nn.Linear and F.linear, never with this lab's results.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class LoRALinear(nn.Module):
    """A frozen base layer plus a trainable low-rank update: y = base(x) + (alpha / r) * x @ A.T @ B.T.

    Store the base as self.base and freeze its parameters. self.A is an nn.Parameter of shape
    (r, base.in_features) with small random values; self.B is an nn.Parameter of shape
    (base.out_features, r) filled with zeros. Only A and B train.
    """

    def __init__(self, base: nn.Linear, r: int = 8, alpha: float = 16):
        super().__init__()
        raise NotImplementedError("write this from memory")

    def forward(self, x):
        raise NotImplementedError("write this from memory")


def trainable_share(model: nn.Module) -> float:
    """The parameters that require grad, as a fraction of all parameters, A and B included
    (unlike mlx-lm's trainable share, which divides by the base model's parameters only)."""
    raise NotImplementedError("write this from memory")


def exact_match(pred: str, gold: str) -> bool:
    """True when pred equals gold after lowercasing, trimming both ends and collapsing runs of whitespace to one space."""
    raise NotImplementedError("write this from memory")


def check():
    torch.manual_seed(0)
    base = nn.Linear(2048, 2048)
    layer = LoRALinear(base, r=8, alpha=16)
    x = torch.randn(4, 2048)
    assert torch.equal(layer(x), base(x)), "at init the layer must equal its base layer"
    assert torch.count_nonzero(layer.B) == 0 and torch.count_nonzero(layer.A) > 0, "B starts at zeros, A random"
    before = {n: p.detach().clone() for n, p in layer.named_parameters()}
    opt = torch.optim.SGD([p for p in layer.parameters() if p.requires_grad], lr=0.1)
    layer(x).pow(2).mean().backward()
    opt.step()
    moved = {n for n, p in layer.named_parameters() if not torch.equal(p, before[n])}
    assert moved and moved <= {"A", "B"}, f"only A and B may change, changed: {sorted(moved)}"
    with torch.no_grad():
        layer.B.normal_()
        merged = F.linear(x, base.weight + (16 / 8) * layer.B @ layer.A, base.bias)
        assert torch.allclose(layer(x), merged, rtol=1e-4, atol=1e-4), "the layer must equal W + (alpha / r) B A"
    assert abs(trainable_share(layer) - 0.0077) < 0.0001, f"trainable share {trainable_share(layer):.4%}"
    assert exact_match("SELECT  Notes FROM t ", "select notes from t") and not exact_match("SELECT a", "SELECT b"), \
        "exact_match must ignore case and extra whitespace, including at the ends"
    print("check: PASS")


if __name__ == "__main__":
    check()
