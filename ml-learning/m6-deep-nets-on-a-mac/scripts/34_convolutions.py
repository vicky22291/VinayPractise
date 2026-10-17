"""34. Convolutions by hand, then a CNN. A 3x3 top-edge kernel by hand and as one matrix multiply, then an MLP and a CNN of about the same size on MNIST, scored on centred and on shifted digits.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torchvision.datasets import MNIST

args = labkit.start(lab=34, device="cpu")
ROOT = labkit.DATA / "mnist"  # shared with lab 29
PARQUET = [("train-00000-of-00001.parquet", 15_561_616), ("test-00000-of-00001.parquet", 2_595_890)]
HIDDEN, BATCH, LR, SHIFT = 26, 64, 1e-3, 4  # MLP hidden units; Adam with batch 64 for 1 epoch; --break shift in pixels
TOP_EDGE = torch.tensor([[-1.0, -1.0, -1.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])  # fastbook ch 13: dark above, bright below


def download():
    try:
        with labkit.locked(ROOT):
            MNIST(ROOT, download=True)  # all four .gz files, ossci-datasets mirror first
    except (RuntimeError, OSError) as e:
        print(f"torchvision download failed, fetching the Hugging Face copy: {str(e).splitlines()[0]}")
        for name, size in PARQUET:
            labkit.fetch(f"https://huggingface.co/datasets/ylecun/mnist/resolve/main/mnist/{name}", ROOT / "parquet" / name, size=size)
    for f in sorted(f for f in ROOT.rglob("*") if f.is_file() and f.suffix != ".lock"):
        print(f"DATA {f} {f.stat().st_size / 1e6:.1f} MB")


def load_data():
    """Train and test pairs (x, y): x is (n, 1, 28, 28) with pixels scaled to [0, 1], y is the digit."""
    try:
        pairs = [(d.data, d.targets) for d in (MNIST(ROOT, train=True), MNIST(ROOT, train=False))]
    except RuntimeError:  # --download fell back to the Hugging Face copy: PNG bytes plus labels
        import io
        import pandas as pd
        from PIL import Image
        if not all((ROOT / "parquet" / name).exists() for name, _ in PARQUET):
            sys.exit("MNIST not found: run this script with --download first")
        frames = [pd.read_parquet(ROOT / "parquet" / name) for name, _ in PARQUET]
        pairs = [(torch.from_numpy(np.stack([np.array(Image.open(io.BytesIO(im["bytes"]))) for im in df["image"]])),
                  torch.from_numpy(df["label"].to_numpy())) for df in frames]
    return [(x.unsqueeze(1).float() / 255, y) for x, y in pairs]


def conv_one(img, kernel):
    """Slide a 3x3 kernel over one (h, w) image, stride 1, no padding: each output is the window times the kernel, summed."""
    h, w = img.shape
    out = torch.zeros(h - 2, w - 2)
    for i in range(h - 2):
        for j in range(w - 2):
            out[i, j] = (img[i:i + 3, j:j + 3] * kernel).sum()
    return out


def conv_batch(x, weight, stride=1, padding=0):
    """The same sums for a batch x (n, c, h, w) and oc kernels (oc, c, k, k), as one matrix multiply."""
    n, _, h, w = x.shape
    oc, _, k, _ = weight.shape
    cols = F.unfold(x, k, padding=padding, stride=stride)  # each k x k window, all channels, becomes one column
    out = weight.view(oc, -1) @ cols  # every kernel (a row) times every window (a column)
    oh, ow = (h + 2 * padding - k) // stride + 1, (w + 2 * padding - k) // stride + 1
    return out.view(n, oc, oh, ow)


def mlp():
    return nn.Sequential(nn.Flatten(), nn.Linear(28 * 28, HIDDEN), nn.ReLU(), nn.Linear(HIDDEN, 10))  # 784 to 26 to 10


def cnn():
    """Two 3x3 conv layers (16, then 32 kernels), each with ReLU and 2x2 max-pooling, then one linear layer to 10."""
    return nn.Sequential(
        nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(),  # Q: what is the first conv's output shape for a batch of 64 digits?
        nn.MaxPool2d(2),  # Q: what does max-pooling drop from each 2x2 window?
        nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),  # Q: how many parameters are in a 3x3 conv with 8 input and 16 output channels?
        nn.MaxPool2d(2), nn.Flatten(), nn.Linear(32 * 7 * 7, 10))


def train(make, x, y):
    """A fresh model (seeded, so it starts the same in every mode), then 1 epoch of Adam on cross-entropy."""
    torch.manual_seed(args.seed)
    model = make()
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    order = torch.randperm(len(x), generator=torch.Generator().manual_seed(args.seed))  # the same batches for both models
    for idx in order.split(BATCH):
        loss = F.cross_entropy(model(x[idx]), y[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()
    return model


def accuracy(model, x, y):
    """Share of digits whose highest score is the right digit, 1,000 images at a time."""
    with torch.no_grad():
        return (torch.cat([model(xb).argmax(dim=1) for xb in x.split(1000)]) == y).float().mean().item()


if args.mode == "download":
    sys.exit(download())  # prints paths and sizes, then stops

(x, y), (x_test, y_test) = load_data()
if labkit.smoke():  # tiny data, every step once, the same code path
    x, y, x_test, y_test = x[:2000], y[:2000], x_test[:500], y_test[:500]

if args.mode in ("baseline", "smoke"):  # P1: the MLP
    model = train(mlp, x, y)
    labkit.result("baseline.mlp_params", sum(p.numel() for p in model.parameters()))
    labkit.result("P1.mlp_test_acc", accuracy(model, x_test, y_test), unit="fraction")

if args.mode in ("change", "smoke"):  # the top-edge kernel by hand, then P2: the CNN
    digit = x_test[0, 0]  # the first test digit, 28 x 28
    by_hand, library = conv_one(digit, TOP_EDGE), F.conv2d(digit[None, None], TOP_EDGE[None, None])[0, 0]
    i, j = divmod(by_hand.argmax().item(), by_hand.shape[1])  # the output with the strongest top edge
    window = (255 * digit[i:i + 3, j:j + 3]).round().int().tolist()
    if not labkit.smoke():  # smoke prints no values
        print(f"WINDOW rows {i} to {i + 2}, cols {j} to {j + 2} of the first test digit, pixels out of 255: {window}", flush=True)
    model = train(cnn, x, y)  # work the WINDOW output out on paper while this trains
    labkit.result("change.top_edge_by_hand", by_hand[i, j], row=i, col=j)
    labkit.result("change.top_edge_conv2d", library[i, j], row=i, col=j)
    labkit.result("change.hand_max_abs_diff", (by_hand - library).abs().max())
    kernels = torch.stack([TOP_EDGE, -TOP_EDGE, TOP_EDGE.T, -TOP_EDGE.T]).unsqueeze(1)  # top, bottom, left, right edges
    gaps = [(conv_batch(x_test[:64], kernels, s, p) - F.conv2d(x_test[:64], kernels, stride=s, padding=p)).abs().max()
            for s in (1, 2) for p in (0, 1)]
    labkit.result("change.unfold_max_abs_diff", torch.stack(gaps).max())  # stride 1 and 2, padding 0 and 1
    labkit.result("change.cnn_params", sum(p.numel() for p in model.parameters()))
    acc = accuracy(model, x_test, y_test)
    labkit.result("P2.cnn_test_acc", acc, unit="fraction")
    mlp_acc = labkit.prior("P1.mlp_test_acc")  # from your --baseline run with the same seed
    if mlp_acc is None:
        print("NOTE run --baseline with this seed first to get P2.cnn_minus_mlp_points", flush=True)
    else:  # accuracies are multiples of 1/10,000, so points need 2 decimals
        labkit.result("P2.cnn_minus_mlp_points", round(100 * (acc - mlp_acc), 2), unit="points")

if args.mode in ("break", "smoke"):  # P3: shift every test digit, re-score both models; neither trains on shifted digits
    shifted = F.pad(x_test, (SHIFT, 0))[..., :28]  # SHIFT blank columns enter on the left, the last SHIFT fall off
    drop = {}
    for name, make in (("mlp", mlp), ("cnn", cnn)):
        model = train(make, x, y)  # the same seed and batches as in --baseline and --change
        before, after = accuracy(model, x_test, y_test), accuracy(model, shifted, y_test)
        labkit.result(f"break.{name}_test_acc", before, unit="fraction")
        labkit.result(f"break.{name}_shifted_acc", after, unit="fraction")
        drop[name] = round(100 * (before - after), 2)
        labkit.result(f"P3.{name}_drop_points", drop[name], unit="points")
    labkit.result("P3.loses_more", max(drop, key=drop.get))
    labkit.result("P3.gap_points", round(abs(drop["mlp"] - drop["cnn"]), 2), unit="points")
