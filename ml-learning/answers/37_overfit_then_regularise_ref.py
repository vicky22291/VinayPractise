"""37. Overfit on purpose, then regularise. A small ResNet on 5,000 and 500 CIFAR-10 images, with and without
random crop and flip: training accuracy, validation accuracy and the gap between them.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import hashlib
import io
import pickle
import sys
import tarfile
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

TAR, TAR_BYTES = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz", 170_498_071
TAR_MD5 = "c58f30108f718f92721af3b95e74349a"  # the published checksum, the one torchvision checks
HF = "https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/{}-00000-of-00001.parquet"
HF_BYTES = {"train": 119_705_255, "test": 23_940_850}  # the fallback copy
NPZ = labkit.DATA / "cifar10" / "cifar10.npz"  # uint8 images N x 3 x 32 x 32 plus labels, written by --download
CONTRACT = {  # the RESULT contract: every value this lab records, by mode, with its unit
    "baseline": {"P1.gap": "points", "baseline.train_acc": "percent", "baseline.val_acc": "percent"},
    "change": {"P2.gap": "points", "P2.gap_delta": "points", "change.train_acc": "percent",
               "change.val_acc": "percent"},
    "break": {"P3.val_acc": "percent", "break.train_acc": "percent", "break.gap": "points",
              "break.epochs_to_100": "epochs"}}
PER_CLASS = {"baseline": 500, "change": 500, "break": 50}  # training images per class, 10 classes
EPOCHS, CAP, BATCH, LR = 30, 100, 128, 1e-3
DROPOUT = 0.0  # p for dropout() before the last layer: 0.0 is the identity; the stretch sets 0.3


def from_tar(path):
    """The six pickled batches, read straight from the tar once its MD5 matches (unpickling trusts the file)."""
    if hashlib.md5(path.read_bytes()).hexdigest() != TAR_MD5:
        raise ValueError(f"{path} does not match the published MD5")
    names = [f"data_batch_{i}" for i in range(1, 6)] + ["test_batch"]  # 5 x 10,000 train, then 10,000 test
    with tarfile.open(path) as tar:
        parts = [pickle.load(tar.extractfile(f"cifar-10-batches-py/{n}"), encoding="bytes") for n in names]
    x = np.concatenate([p[b"data"] for p in parts]).reshape(-1, 3, 32, 32)
    return x, np.concatenate([p[b"labels"] for p in parts])


def from_parquet():
    """The Hugging Face copy: one PNG and one label per row, the train split first."""
    import pandas as pd
    from PIL import Image
    df = pd.concat([pd.read_parquet(labkit.fetch(HF.format(s), NPZ.parent / f"{s}.parquet", size=HF_BYTES[s]))
                    for s in ("train", "test")], ignore_index=True)
    x = np.stack([np.asarray(Image.open(io.BytesIO(img["bytes"])).convert("RGB")).transpose(2, 0, 1)
                  for img in df["img"]])
    return x, df["label"].to_numpy()


def download():
    """CIFAR-10 once, as one .npz: the Toronto tar first, the Hugging Face parquet copy second."""
    with labkit.locked(NPZ):
        if not NPZ.exists():
            try:
                x, y = from_tar(labkit.fetch(TAR, NPZ.parent / "cifar-10-python.tar.gz", size=TAR_BYTES))
            except Exception as e:  # any network or checksum error: try the fallback
                print(f"RETRY Toronto tar failed ({type(e).__name__}), trying the Hugging Face copy", flush=True)
                x, y = from_parquet()
            part = NPZ.with_name("cifar10.part.npz")
            np.savez(part, x_train=x[:50_000], y_train=y[:50_000], x_val=x[50_000:], y_val=y[50_000:])
            part.replace(NPZ)  # atomic: a half-written file never looks finished
    print(f"HAVE {NPZ} {NPZ.stat().st_size / 1e6:.1f} MB", flush=True)


def load_data(per_class, seed, device, smoke=False):
    """CIFAR-10 on `device`: x_train, y_train, x_val, y_val (float32 images N x 3 x 32 x 32, int64 labels).

    Training: `per_class` images of each of the 10 classes, the first ones in a random order fixed by seed,
    so at one seed the 50-per-class set sits inside the 500-per-class set. Validation: all 10,000 test images.
    Pixels are scaled to 0 to 1, then each channel is normalized with the training images' own mean and std.
    Smoke keeps at most 20 images per class and the first 1,000 validation images.
    """
    if not NPZ.exists():
        sys.exit("no data: run python scripts/37_overfit_then_regularise.py --download first")
    d = np.load(NPZ)
    y_all, y_val = d["y_train"], d["y_val"]
    order = np.random.RandomState(seed).permutation(len(y_all))
    n = min(per_class, 20) if smoke else per_class
    keep = np.concatenate([order[y_all[order] == c][:n] for c in range(10)])
    n_val = 1000 if smoke else len(y_val)
    x_tr = torch.from_numpy(d["x_train"][keep]).float() / 255
    x_va = torch.from_numpy(d["x_val"][:n_val]).float() / 255
    mean, std = x_tr.mean((0, 2, 3), keepdim=True), x_tr.std((0, 2, 3), keepdim=True)
    y_tr, y_va = torch.from_numpy(y_all[keep]).long(), torch.from_numpy(y_val[:n_val]).long()
    return [t.to(device) for t in ((x_tr - mean) / std, y_tr, (x_va - mean) / std, y_va)]


def report(mode, values):
    """Print this mode's RESULT lines in CONTRACT order. A missing value (no baseline run yet) prints SKIP."""
    for name, unit in CONTRACT[mode].items():
        if values.get(name) is None:
            print(f"SKIP {name}: run --baseline with the same seed first", flush=True)
        else:
            labkit.result(name, values[name], unit=unit)


def dropout(x, p, training):
    """Inverted dropout: in training, zero each element with probability p and scale the rest by 1 / (1 - p)."""
    if not training:
        return x
    mask = torch.rand_like(x) >= p
    return x * mask / (1 - p)


def augment(batch, pad=4, flip_p=0.5):
    """A random crop of a reflect-padded copy, then a horizontal flip, drawn for each image on its own."""
    n, _, h, w = batch.shape
    padded = F.pad(batch, (pad, pad, pad, pad), mode="reflect")
    dy, dx = torch.randint(0, 2 * pad + 1, (2, n)).tolist()  # drawn on the CPU: no GPU sync
    out = torch.stack([padded[i, :, dy[i]:dy[i] + h, dx[i]:dx[i] + w] for i in range(n)])
    flip = (torch.rand(n) < flip_p).to(batch.device)
    return torch.where(flip[:, None, None, None], out.flip(-1), out)


class Block(nn.Module):
    """Two 3x3 convolutions with batch norm, added to a shortcut (a 1x1 convolution when the shape changes)."""

    def __init__(self, c_in, c_out, stride):
        super().__init__()
        self.conv1, self.bn1 = nn.Conv2d(c_in, c_out, 3, stride, 1, bias=False), nn.BatchNorm2d(c_out)
        self.conv2, self.bn2 = nn.Conv2d(c_out, c_out, 3, 1, 1, bias=False), nn.BatchNorm2d(c_out)
        self.short = nn.Identity() if stride == 1 and c_in == c_out else nn.Sequential(
            nn.Conv2d(c_in, c_out, 1, stride, bias=False), nn.BatchNorm2d(c_out))

    def forward(self, x):
        return F.relu(self.bn2(self.conv2(F.relu(self.bn1(self.conv1(x))))) + self.short(x))


class Net(nn.Module):
    """A small ResNet: a 32-channel stem, blocks of 32, 64 and 128 channels, average pool, dropout, linear."""

    def __init__(self, p=DROPOUT):
        super().__init__()
        self.p = p
        self.stem = nn.Sequential(nn.Conv2d(3, 32, 3, 1, 1, bias=False), nn.BatchNorm2d(32), nn.ReLU())
        self.blocks = nn.Sequential(Block(32, 32, 1), Block(32, 64, 2), Block(64, 128, 2))
        self.head = nn.Linear(128, 10)

    def forward(self, x):
        h = self.blocks(self.stem(x)).mean((2, 3))  # global average pool: N x 128
        return self.head(dropout(h, self.p, self.training))


@torch.no_grad()
def accuracy(net, x, y):
    """Percent correct in eval mode (batch norm uses its running statistics), 1,000 images at a time."""
    net.eval()
    hits = sum((net(xb).argmax(1) == yb).sum().item() for xb, yb in zip(x.split(1000), y.split(1000)))
    return 100 * hits / len(y)


def train(net, x, y, epochs, aug, seed, stop_at_100=False):
    """Adam, a fresh shuffle every epoch. Returns the epochs trained: with stop_at_100, the first epoch after
    which training accuracy (eval mode, no augmentation) is 100%."""
    opt = torch.optim.Adam(net.parameters(), lr=LR)
    order = torch.Generator().manual_seed(seed)  # its own generator: the same batch order with or without aug
    for epoch in range(1, epochs + 1):
        net.train()
        for idx in torch.randperm(len(y), generator=order).split(BATCH):
            idx = idx.to(x.device)
            loss = F.cross_entropy(net(augment(x[idx]) if aug else x[idx]), y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
        if stop_at_100 and accuracy(net, x, y) == 100:
            return epoch
    return epochs


def run(mode, seed, device, base_gap=None):
    """One step: train from the seed's starting weights, then score the training images and the validation set."""
    x_tr, y_tr, x_va, y_va = load_data(PER_CLASS[mode], seed, device, smoke=labkit.smoke())
    print(f"DATA mode={mode} train={len(y_tr)} valid={len(y_va)} augment={mode == 'change'}", flush=True)
    labkit.seed_all(seed)  # the same starting weights in every mode
    net = Net().to(device)
    epochs = 2 if labkit.smoke() else CAP if mode == "break" else EPOCHS
    trained = train(net, x_tr, y_tr, epochs, aug=mode == "change", seed=seed, stop_at_100=mode == "break")
    tr, va = accuracy(net, x_tr, y_tr), accuracy(net, x_va, y_va)
    if mode == "baseline":
        values = {"P1.gap": tr - va, "baseline.train_acc": tr, "baseline.val_acc": va}
    elif mode == "change":
        values = {"P2.gap": tr - va, "P2.gap_delta": None if base_gap is None else tr - va - base_gap,
                  "change.train_acc": tr, "change.val_acc": va}
    else:
        values = {"P3.val_acc": va, "break.train_acc": tr, "break.gap": tr - va, "break.epochs_to_100": trained}
    report(mode, values)
    return values


def calibrate(device):
    """Smoke only: seconds for one 5,000-image epoch, plain and augmented, on random pixels, to size the runs."""
    x, y = torch.randn(5000, 3, 32, 32, device=device), torch.randint(0, 10, (5000,), device=device)
    for aug in (False, True):
        net = Net().to(device)
        train(net, x, y, 1, aug, seed=0)  # warmup: one full epoch builds the GPU kernels for every batch shape
        times = []
        for _ in range(3):
            t0 = labkit.clock(device)
            train(net, x, y, 1, aug, seed=0)
            times.append(labkit.clock(device) - t0)
        labkit.result(f"smoke.sec_per_epoch_{'aug' if aug else 'plain'}", float(np.median(times)), smoke_ok=True,
                      unit="s", device=device, batch=BATCH, warmup=1, n=3, stat="median")


def main():
    args = labkit.start(lab=37, device=labkit.pick_device())
    if args.mode == "download":
        return download()
    print(f"DATA device={args.device} batch={BATCH} lr={LR} params={sum(p.numel() for p in Net().parameters())}",
          flush=True)
    if not labkit.smoke():
        return run(args.mode, args.seed, args.device, base_gap=labkit.prior("P1.gap"))
    base = run("baseline", args.seed, args.device)  # smoke: every mode on tiny data, the same code path
    run("change", args.seed, args.device, base_gap=base["P1.gap"])
    run("break", args.seed, args.device)
    calibrate(args.device)


if __name__ == "__main__":
    main()
