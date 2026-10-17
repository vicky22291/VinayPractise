"""37. Overfit on purpose, then regularise. A small ResNet on 5,000 and 500 CIFAR-10 images, with and without
random crop and flip: training accuracy, validation accuracy and the gap between them.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
Level S starter: load_data() and report() are given. You write dropout() and augment() from the lab file,
then the AI writes the model, the training loop and the three measured modes.
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


def main():
    args = labkit.start(lab=37, device=labkit.pick_device())
    if args.mode == "download":
        return download()
    if args.mode != "smoke":
        raise NotImplementedError("write the harness: see the lab file")
    # smoke checks the plumbing only: a linear model and torch's own dropout stand in for what you will write
    x_tr, y_tr, x_va, y_va = load_data(50, args.seed, args.device, smoke=True)
    print(f"DATA device={args.device} train={len(y_tr)} valid={len(y_va)}", flush=True)
    net = nn.Sequential(nn.Flatten(), nn.Dropout(0.3), nn.Linear(3 * 32 * 32, 10)).to(args.device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    for xb, yb in zip(x_tr.split(128), y_tr.split(128)):
        loss = F.cross_entropy(net(xb), yb)
        opt.zero_grad()
        loss.backward()
        opt.step()
    net.eval()
    with torch.no_grad():
        stand_in = 100 * (net(x_va).argmax(1) == y_va).float().mean().item()
    for mode, names in CONTRACT.items():
        report(mode, dict.fromkeys(names, stand_in))


if __name__ == "__main__":
    main()
