"""Lab 36 rebuild: the activation std after each ReLU layer, written from memory.

Write the body (about 10 lines), then run: python rebuild/36_layer_stds.py
check() compares with torch (nn.init.kaiming_normal_, nn.init.normal_, nn.Linear, nn.BatchNorm1d), never with the lab's results.
"""
import math

import torch
import torch.nn.functional as F
from torch import nn


def layer_stds(x, depth=10, width=100, init="kaiming", norm=False):
    """The std of the activations after each of `depth` ReLU layers of `width` units, at initialization.

    x: (n, d) float tensor. Each layer draws a fresh (fan_in, width) weight W, with fan_in its input width:
    init="normal" draws N(0, 1) weights, init="kaiming" draws Kaiming normal weights for ReLU (fan_in mode),
    and a number c draws c times the Kaiming weights. Then z = h @ W (no bias). If norm, normalize each
    column of z over the n rows, as nn.BatchNorm1d does in training without its learned scale and shift.
    Then h = relu(z). Return a list of `depth` floats: h.std() after each layer.
    """
    raise NotImplementedError("write this from memory")


def torch_layer_stds(x, depth, scale=1.0, norm=False, width=1000):
    """The same statistics from torch's own layers on fresh draws: nn.Linear with scale x Kaiming weights
    (nn.init.kaiming_normal_), then nn.BatchNorm1d (training mode, affine=False) when norm, then ReLU."""
    h, stds = x, []
    for _ in range(depth):
        layer = nn.Linear(h.shape[1], width, bias=False)
        nn.init.kaiming_normal_(layer.weight, nonlinearity="relu")
        z = scale * layer(h)
        h = F.relu(nn.BatchNorm1d(width, affine=False)(z) if norm else z)
        stds.append(h.std().item())
    return stds


def check():
    torch.manual_seed(0)
    eye = torch.eye(1000)  # one layer on the 1,000 x 1,000 identity: z is the weight itself
    mine = layer_stds(eye, depth=1, width=1000, init="kaiming")[0]
    lib = F.relu(nn.init.kaiming_normal_(torch.empty(1000, 1000), nonlinearity="relu")).std().item()
    assert abs(mine - lib) < 0.002, f"kaiming: {mine:.4f} vs nn.init.kaiming_normal_ {lib:.4f}"
    for init, w in (("normal", nn.init.normal_(torch.empty(1000, 1000))),
                    (3.0, 3 * nn.init.kaiming_normal_(torch.empty(1000, 1000), nonlinearity="relu"))):
        mine, lib = layer_stds(eye, depth=1, width=1000, init=init)[0], F.relu(w).std().item()
        assert math.isclose(mine, lib, rel_tol=0.01), f"init={init}: {mine:.4f} vs torch {lib:.4f}"
    x = torch.randn(500, 100)  # 500 rows of 100 inputs, into 1,000 units per layer
    mixed = x * torch.logspace(-1, 1, 500)[:, None]  # the same rows, scaled from 0.1 to 10
    for what, rows, depth, init, norm, tol in (
            ("1 layer from 100 inputs", x, 1, "kaiming", False, 0.03),  # fan_in is 100 here, not 1,000
            ("3 layers at 3 x Kaiming", x, 3, 3.0, False, 0.25),
            ("3 layers with BatchNorm", x, 3, "kaiming", True, 0.02),
            ("1 BatchNorm layer on rows scaled 0.1 to 10", mixed, 1, "kaiming", True, 0.05),
            ("1 BatchNorm layer from 1 input", x[:, :1], 1, "kaiming", True, 0.03)):
        mine = layer_stds(rows, depth=depth, width=1000, init=init, norm=norm)
        lib = torch_layer_stds(rows, depth, scale=1.0 if init == "kaiming" else init, norm=norm)
        assert len(mine) == depth and all(math.isclose(a, b, rel_tol=tol) for a, b in zip(mine, lib)), \
            f"{what}: {[round(v, 4) for v in mine]} vs torch {[round(v, 4) for v in lib]}"
    print("check: PASS")


if __name__ == "__main__":
    check()
