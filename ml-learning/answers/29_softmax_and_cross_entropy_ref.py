"""29. Softmax and cross-entropy: from 2 digits to 10. One linear 784-to-10 MNIST model, 1 epoch, three losses.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import numpy as np
import torch
import torch.nn.functional as F
from torchvision.datasets import MNIST

args = labkit.start(lab=29, device="cpu", extra_modes=("check",))
ROOT = labkit.DATA / "mnist"  # shared with lab 34
HF = "https://huggingface.co/datasets/ylecun/mnist/resolve/main/mnist/"
PARQUET = [("train-00000-of-00001.parquet", 15_561_616), ("test-00000-of-00001.parquet", 2_595_890)]
INIT_STD, BATCH, LR = 0.01, 64, 0.1  # linear 784-to-10, plain SGD, 1 epoch


def download():
    try:
        with labkit.locked(ROOT):
            MNIST(ROOT, download=True)  # all four .gz files, ossci-datasets mirror first
    except (RuntimeError, OSError) as e:
        print(f"torchvision download failed, fetching the Hugging Face copy: {str(e).splitlines()[0]}")
        for name, size in PARQUET:
            labkit.fetch(HF + name, ROOT / "parquet" / name, size=size)
    for f in sorted(ROOT.rglob("*")):
        if f.is_file() and f.suffix != ".lock":
            print(f"DATA {f} {f.stat().st_size / 1e6:.1f} MB")


def read_parquet(path):
    """The Hugging Face copy: PNG bytes plus labels, decoded to uint8 images."""
    import io
    import pandas as pd
    from PIL import Image
    df = pd.read_parquet(path)
    images = np.stack([np.array(Image.open(io.BytesIO(im["bytes"]))) for im in df["image"]])
    return torch.from_numpy(images), torch.from_numpy(df["label"].to_numpy())


def load_data():
    """Train and test pairs (x, y): pixels scaled to [0, 1], each image flattened to 784."""
    try:
        pairs = [(d.data, d.targets) for d in (MNIST(ROOT, train=True), MNIST(ROOT, train=False))]
    except RuntimeError:  # --download fell back to the Hugging Face copy
        files = [ROOT / "parquet" / name for name, _ in PARQUET]
        if not all(f.exists() for f in files):
            sys.exit("MNIST not found: run this script with --download first")
        pairs = [read_parquet(f) for f in files]
    return [(x.reshape(len(x), 784).float() / 255, y) for x, y in pairs]


# --- CONCEPT start ---
def cross_entropy(logits, targets):
    """Mean cross-entropy over the batch, computed from raw logits.

    logits: (n, 10) float tensor of scores. targets: (n,) tensor of class ids. Per row the loss
    is minus the log of the softmax probability of the right class: write it with logsumexp,
    subtracting the row maximum before exp so a logit of 1,000 does not overflow. Plain tensor ops
    only (no F.cross_entropy, F.log_softmax or torch.logsumexp). Return a scalar tensor for backward().
    """
    z = logits - logits.max(dim=1, keepdim=True).values
    log_sum_exp = z.exp().sum(dim=1).log()
    return (log_sum_exp - z[torch.arange(len(targets)), targets]).mean()
# --- CONCEPT end ---


def mse_one_hot(logits, targets):
    """--change: mean squared error between the softmax probabilities and one-hot targets."""
    return F.mse_loss(torch.softmax(logits, dim=1), F.one_hot(targets, 10).float())


def double_softmax(logits, targets):
    """--break: softmax on the outputs first, then nn.CrossEntropyLoss."""
    return torch.nn.CrossEntropyLoss()(torch.softmax(logits, dim=1), targets)


def train(loss_fn, x, y):
    """A fresh linear 784-to-10 model, 1 epoch of SGD over shuffled batches. Returns it and every batch loss."""
    model = torch.nn.Linear(784, 10)
    torch.nn.init.normal_(model.weight, std=INIT_STD)
    torch.nn.init.zeros_(model.bias)
    opt = torch.optim.SGD(model.parameters(), lr=LR)
    losses = []
    for idx in torch.randperm(len(x)).split(BATCH):
        loss = loss_fn(model(x[idx]), y[idx])
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(loss.item())
    return model, losses


def accuracy(model, x, y):
    with torch.no_grad():
        return (model(x).argmax(dim=1) == y).float().mean().item()


def check():
    """A 20-row fixture: cross_entropy() must match F.cross_entropy, value and gradient, within 1e-6."""
    g = torch.Generator().manual_seed(0)
    logits = 3 * torch.randn(20, 10, generator=g, dtype=torch.float64)
    logits[:5] += 1000  # a naive exp overflows on these rows
    logits[5, 3] = 1000
    targets = torch.randint(0, 10, (20,), generator=g)
    mine, ref = logits.clone().requires_grad_(), logits.clone().requires_grad_()
    loss_mine, loss_ref = cross_entropy(mine, targets), F.cross_entropy(ref, targets)
    loss_mine.backward()
    loss_ref.backward()
    assert abs(loss_mine.item() - loss_ref.item()) < 1e-6, (loss_mine.item(), loss_ref.item())
    assert torch.allclose(mine.grad, ref.grad, rtol=0, atol=1e-6), "gradients differ from F.cross_entropy"
    print("check: PASS")


if args.mode == "download":
    download()
elif args.mode == "check":
    check()
else:
    (x, y), (x_test, y_test) = load_data()
    if labkit.smoke():  # tiny data, every loss once
        x, y, x_test, y_test = x[:2000], y[:2000], x_test[:500], y_test[:500]
    ce = F.cross_entropy if labkit.smoke() else cross_entropy  # smoke checks the plumbing only
    if args.mode in ("baseline", "smoke"):
        model, losses = train(ce, x, y)
        labkit.result("P1.first_batch_loss", losses[0], unit="nats")
        labkit.result("baseline.test_accuracy", accuracy(model, x_test, y_test), unit="fraction")
        labkit.result("baseline.min_batch_loss", min(losses), unit="nats")
    if args.mode in ("change", "smoke"):
        model, losses = train(mse_one_hot, x, y)
        acc = accuracy(model, x_test, y_test)
        labkit.result("P2.test_accuracy", acc, unit="fraction")
        base = labkit.prior("baseline.test_accuracy")
        if base is not None:
            labkit.result("P2.accuracy_delta", acc - base, unit="fraction")
        labkit.result("change.min_batch_loss", min(losses), unit="mse")
    if args.mode in ("break", "smoke"):
        model, losses = train(double_softmax, x, y)
        labkit.result("P3.test_accuracy", accuracy(model, x_test, y_test), unit="fraction")
        z, digits = torch.zeros(10, 10, requires_grad=True), torch.arange(10)  # free logits, one row per digit
        opt = torch.optim.Adam([z], lr=1.0)
        for _ in range(100):
            opt.zero_grad()
            double_softmax(z, digits).backward()
            opt.step()
        labkit.result("P3.lowest_possible_loss", double_softmax(z, digits).item(), unit="nats")
        labkit.result("break.min_batch_loss", min(losses), unit="nats")
