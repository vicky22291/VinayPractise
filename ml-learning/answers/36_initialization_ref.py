"""36. Initialization and activation statistics. The activation std after each of 10 ReLU layers for four inits and Kaiming with BatchNorm, then 2 epochs of training with each.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import gzip
import io
import math
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

args = labkit.start(lab=36, device="cpu", extra_modes=("check",))
torch.set_num_threads(1)  # the layers are tiny, so one thread is fastest, and BatchNorm sums come out the same on any Mac
ROOT = labkit.DATA / "fashion_mnist"
HF = "https://huggingface.co/datasets/zalando-datasets/fashion_mnist/resolve/main/fashion_mnist/"
PARQUET = [("train-00000-of-00001.parquet", 30_931_277), ("test-00000-of-00001.parquet", 5_175_617)]
GH = "https://raw.githubusercontent.com/zalandoresearch/fashion-mnist/master/data/fashion/"
GZ = [("train-images-idx3-ubyte.gz", 26_421_880), ("train-labels-idx1-ubyte.gz", 29_515),
      ("t10k-images-idx3-ubyte.gz", 4_422_102), ("t10k-labels-idx1-ubyte.gz", 5_148)]
DEPTH, WIDTH, N_STATS = 10, 100, 512  # 10 ReLU layers of 100 units; the statistics use 512 training images
EPOCHS, BATCH, LR = 2, 64, 0.05  # plain SGD, no momentum
UNTRAINED, NEAR = math.log(10), 0.1  # the loss when each of the 10 classes gets probability 0.1; "near" is within 0.1 nats

def download():
    try:
        for name, size in PARQUET:
            labkit.fetch(HF + name, ROOT / name, size=size)
    except OSError as e:
        print(f"Hugging Face download failed, fetching the GitHub gz files: {str(e).splitlines()[0]}")
        for name, size in GZ:
            labkit.fetch(GH + name, ROOT / "gz" / name, size=size)

def load_data(limit=None):
    """Train and test (x, y): x is (n, 784), standardized with the training set's pixel mean and std."""
    if all((ROOT / name).exists() for name, _ in PARQUET):  # PNG bytes plus a label per row
        import pandas as pd
        from PIL import Image
        frames = [pd.read_parquet(ROOT / name)[:limit] for name, _ in PARQUET]
        pairs = [(np.stack([np.array(Image.open(io.BytesIO(im["bytes"]))) for im in df["image"]]), df["label"].to_numpy()) for df in frames]
    elif all((ROOT / "gz" / name).exists() for name, _ in GZ):  # the GitHub copy: raw bytes after a short header
        raw = [gzip.decompress((ROOT / "gz" / name).read_bytes()) for name, _ in GZ]
        pairs = [(np.frombuffer(raw[k], np.uint8, offset=16).reshape(-1, 784)[:limit], np.frombuffer(raw[k + 1], np.uint8, offset=8)[:limit]) for k in (0, 2)]
    else:
        sys.exit("Fashion-MNIST not found: run this script with --download first")
    (x, y), (x_test, y_test) = [(torch.from_numpy(im.reshape(len(im), 784) / np.float32(255)), torch.from_numpy(lab.astype(np.int64))) for im, lab in pairs]
    return (x - x.mean()) / x.std(), y, (x_test - x.mean()) / x.std(), y_test  # the training mean and std for both

# --- CONCEPT start ---
def layer_stds(x, depth=DEPTH, width=WIDTH, init="kaiming", norm=False):
    """The std of the activations after each of `depth` ReLU layers of `width` units, at initialization.

    x: (n, d) float tensor. For each layer, with fan_in its input width, W = torch.randn(fan_in, width) * s:
    s = 1 for init="normal", sqrt(2 / fan_in) for "kaiming", init * sqrt(2 / fan_in) when init is a number.
    z = h @ W (no bias). If norm, normalize each column of z over the n rows as nn.BatchNorm1d does in
    training, without its learned scale and shift: (z - mean) / sqrt(var + 1e-5), var dividing by n.
    Then h = relu(z). Draw nothing else at random. Return a list of `depth` floats: h.std() after each layer.
    """
    h, stds = x, []
    for _ in range(depth):
        fan_in = h.shape[1]
        s = 1.0 if init == "normal" else math.sqrt(2 / fan_in) * (1.0 if init == "kaiming" else float(init))
        z = h @ (torch.randn(fan_in, width) * s)
        if norm:
            z = (z - z.mean(dim=0)) / torch.sqrt(z.var(dim=0, unbiased=False) + 1e-5)
        h = torch.relu(z)
        stds.append(h.std().item())
    return stds
# --- CONCEPT end ---

def make_net(init, norm=False, depth=DEPTH, width=WIDTH, n_in=784):
    """depth blocks of Linear (no bias), BatchNorm1d when norm, ReLU; then a head to 10 classes. Drawn as layer_stds() draws."""
    layers, fan_in = [], n_in
    for i, fan_out in enumerate([width] * depth + [10]):
        s = 1.0 if init == "normal" else nn.init.calculate_gain("relu") / math.sqrt(fan_in) * (1.0 if init == "kaiming" else float(init))
        layers.append(nn.utils.skip_init(nn.Linear, fan_in, fan_out, bias=False))  # no default init, so no extra draws
        layers[-1].weight.data = (torch.randn(fan_in, fan_out) * s).T.contiguous()
        if i < depth:
            layers += [nn.BatchNorm1d(width), nn.ReLU()] if norm else [nn.ReLU()]
        fan_in = fan_out
    return nn.Sequential(*layers)

def library_layer_stds(x, init="kaiming", norm=False, depth=DEPTH, width=WIDTH):
    """The same statistics from torch's own layers: make_net() with a forward hook on every ReLU."""
    net, stds = make_net(init, norm, depth, width, n_in=x.shape[1]), []
    for m in net:
        if isinstance(m, nn.ReLU):
            m.register_forward_hook(lambda mod, inp, out: stds.append(out.std().item()))
    net(x)  # each hook records the std after its ReLU
    return stds

def run(init, norm, names):
    """One init: the std after each layer on the 512 images, then 2 epochs of plain SGD. Prints four RESULT lines."""
    torch.manual_seed(args.seed)  # every init draws the same random numbers, so only the scale differs
    logs = [math.log10(s) for s in stds_of(x_stats, init=init, norm=norm)]
    labkit.result(names[0], ",".join(f"{v:.2f}" for v in logs), unit="log10")  # layer 1 first
    labkit.result(names[1], logs[-1], unit="log10")
    torch.manual_seed(args.seed)  # the net that trains starts from the weights measured above
    net = make_net(init, norm)
    opt = torch.optim.SGD(net.parameters(), lr=LR)
    for _ in range(EPOCHS):
        losses = []
        for idx in torch.randperm(len(x)).split(BATCH):
            loss = F.cross_entropy(net(x[idx]), y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(loss.item())
    net.eval()
    with torch.no_grad():
        acc = (net(x_test).argmax(dim=1) == y_test).float().mean().item()
    loss = sum(losses) / len(losses)  # the mean batch loss of the last epoch
    labkit.result(names[2], loss, unit="nats")
    labkit.result(names[3], acc, unit="fraction")
    return loss

def check():
    """A 20-row fixture: layer_stds() must match torch's own layers (nn.Linear, nn.BatchNorm1d, nn.ReLU) on the same draws."""
    x = torch.randn(20, 30, generator=torch.Generator().manual_seed(0))
    for init, norm in (("normal", False), ("kaiming", False), (10.0, False), (0.1, False), ("kaiming", True)):
        torch.manual_seed(1)
        mine = layer_stds(x, depth=4, width=16, init=init, norm=norm)
        torch.manual_seed(1)  # the same draws again, inside torch's layers
        ref = library_layer_stds(x, init=init, norm=norm, depth=4, width=16)
        bad = [k + 1 for k, (a, b) in enumerate(zip(mine, ref)) if not math.isclose(a, b, rel_tol=1e-4)]
        assert len(mine) == 4 and not bad, f"layer_stds(init={init!r}, norm={norm}): {len(mine)} stds for depth 4, and layers {bad} differ from torch's"
    print("check: PASS")

if args.mode in ("download", "check"):
    sys.exit(download() if args.mode == "download" else check())
x, y, x_test, y_test = load_data(limit=2000 if labkit.smoke() else None)  # smoke: tiny data, the same code path
x_stats = x[torch.randperm(len(x), generator=torch.Generator().manual_seed(args.seed))[:N_STATS]]
stds_of = library_layer_stds if labkit.smoke() else layer_stds  # smoke checks the plumbing only

if args.mode in ("baseline", "smoke"):  # P1: N(0, 1) weights
    run("normal", False, ("baseline.log10_std_by_layer", "P1.log10_std_layer10", "baseline.train_loss", "baseline.test_acc"))
if args.mode in ("change", "smoke"):  # P2: Kaiming init; then Kaiming with BatchNorm
    run("kaiming", False, ("change.log10_std_by_layer", "P2.log10_std_layer10", "change.train_loss", "change.test_acc"))
    run("kaiming", True, ("change.bn_log10_std_by_layer", "change.bn_log10_std_layer10", "change.bn_train_loss", "change.bn_test_acc"))
if args.mode in ("break", "smoke"):  # P3: Kaiming x 10, then Kaiming x 0.1
    near = []
    for tag, scale in (("x10", 10.0), ("x01", 0.1)):
        loss = run(scale, False, (f"break.{tag}_log10_std_by_layer", f"break.{tag}_log10_std_layer10",
                                  f"P3.{tag}_train_loss", f"break.{tag}_test_acc"))
        near += [f"x{scale:g}"] if abs(loss - UNTRAINED) < NEAR else []
    labkit.result("P3.near_untrained", "both" if len(near) == 2 else (near[0] if near else "neither"))
