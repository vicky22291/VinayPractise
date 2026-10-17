"""11. Error analysis by hand: errors decide the next experiment. Ranks a fine-tuned ResNet-34's validation
images by loss for a hand tally, lists fastai's most_confused pairs, then flips 10% of the training labels.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import contextlib
import csv
import re
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from fastai.vision.all import (CategoryBlock, ClassificationInterpretation, DataBlock, ImageBlock, ItemGetter,
                               Normalize, RandomSplitter, Resize, aug_transforms, error_rate, get_image_files,
                               imagenet_stats, noop, resnet34, set_seed, vision_learner)
from torchvision.models import ResNet34_Weights

PETS_URL, PETS_BYTES = "https://s3.amazonaws.com/fast-ai-imageclas/oxford-iiit-pet.tgz", 811_706_944
PETS = labkit.DATA / "oxford-iiit-pet"  # images/ holds Abyssinian_1.jpg ... yorkshire_terrier_99.jpg
BATCH, WORKERS, BASE_LR = 64, 0, 2e-3   # lab 01's recipe; fastai 2.8 sets workers to 0 on macOS
K, FLIP = 50, 0.10                       # images read by hand; share of training labels flipped in --break
BREED = re.compile(r"^(.*)_\d+\.jpg$")   # great_pyrenees_17.jpg -> great_pyrenees


def download():
    labkit.extract(labkit.fetch(PETS_URL, labkit.DATA / "oxford-iiit-pet.tgz", size=PETS_BYTES), labkit.DATA)
    weights = ResNet34_Weights.IMAGENET1K_V1  # what fastai loads for a pretrained resnet34
    path = Path(torch.hub.get_dir()) / "checkpoints" / Path(weights.url).name
    with labkit.locked(path):
        weights.get_state_dict(progress=False, check_hash=True)
    print(f"HAVE {path} {path.stat().st_size / 1e6:.1f} MB", flush=True)
    print(f"HAVE {PETS / 'images'} {len(get_image_files(PETS / 'images'))} images", flush=True)


# --- CONCEPT start ---
def top_losses(logits, targets, k):
    """The k largest per-item cross-entropy losses, highest first, and their row numbers: (losses, idx).

    loss_i = -log softmax(logits_i)[targets_i]. Use log-softmax, not the log of softmax, so huge logits
    stay finite, then sort with argsort. --check compares it with F.cross_entropy(reduction='none').
    """
    losses = -torch.log_softmax(logits, dim=1)[torch.arange(len(targets)), targets]
    idx = torch.argsort(losses, descending=True)[:k]
    return losses[idx], idx


# --- CONCEPT end ---


def library_top_losses(logits, targets, k):
    """top_losses the library way: PyTorch's per-item cross-entropy, then topk."""
    return F.cross_entropy(logits, targets, reduction="none").topk(k)


def flip_labels(targets, n_classes, frac, seed):
    """Move exactly round(frac * n) random rows to another class, picked at random. Returns (new targets, rows)."""
    rng = np.random.default_rng(seed)
    rows = np.sort(rng.choice(len(targets), size=round(frac * len(targets)), replace=False))
    new = np.array(targets).copy()
    new[rows] = (new[rows] + rng.integers(1, n_classes, size=len(rows))) % n_classes  # never the same class
    return new, rows


def pet_dataloaders(seed, device, flip=0.0):
    """Lab 01's images, transforms and split. flip > 0 flips that share of the training labels, never validation."""
    files = sorted(get_image_files(PETS / "images"))
    if labkit.smoke():
        files = files[::20]  # smoke: about 10 images per breed, same code path
    names = [BREED.match(f.name).group(1) for f in files]
    vocab = sorted(set(names))
    y = np.array([vocab.index(n) for n in names])
    splitter = RandomSplitter(valid_pct=0.2, seed=42 + seed)  # lab 01's split
    train_idx, flipped = np.array(splitter(files)[0]), set()
    if flip:
        new, rows = flip_labels(y[train_idx], len(vocab), flip, seed)
        y[train_idx], flipped = new, {files[i] for i in train_idx[rows]}
    block = DataBlock(blocks=(ImageBlock, CategoryBlock(vocab=vocab)), get_x=ItemGetter(0), get_y=ItemGetter(1),
                      splitter=splitter, item_tfms=Resize(448),
                      batch_tfms=[*aug_transforms(size=224, min_scale=0.75), Normalize.from_stats(*imagenet_stats)])
    items = [(f, vocab[c]) for f, c in zip(files, y)]
    return block.dataloaders(items, bs=BATCH, num_workers=WORKERS, device=device), flipped


def fine_tune(learn):
    "Lab 01's fine_tune(1) at its base learning rate. Silent in --smoke."
    with contextlib.ExitStack() as stack:
        if labkit.smoke():
            stack.enter_context(learn.no_bar())
            stack.enter_context(learn.no_logging())
        learn.fine_tune(1, base_lr=BASE_LR)


def predict(learn, dl=None):
    """Logits, labels and fastai's per-item losses, in item order (default: the validation set)."""
    with learn.no_bar():
        return learn.get_preds(dl=dl, act=noop, with_loss=True)


def baseline(learn, dls, out, seed, rank, flipped):
    fine_tune(learn)
    torch.save(learn.model.state_dict(), out / f"model_seed{seed}.pth")  # --change reads it
    logits, targs, losses = predict(learn)
    top, idx = rank(logits, targs, K)
    pred, items = logits.argmax(1), dls.valid_ds.items
    rows = [(r, items[i][0].name, items[i][1], dls.vocab[int(pred[i])], f"{loss:.3f}")
            for r, (i, loss) in enumerate(zip(idx.tolist(), top.tolist()), 1)]
    with open(out / f"top_losses_seed{seed}.csv", "w", newline="") as fh:  # you fill in the category column
        csv.writer(fh).writerows([("rank", "file", "actual", "predicted", "loss", "category"), *rows])
    with learn.no_bar():
        ClassificationInterpretation(learn, dls.valid, losses).plot_top_losses(K, nrows=10, figsize=(30, 40))
    plt.tight_layout(rect=(0, 0, 1, 0.98))  # no overlapping titles; the top strip keeps the figure title
    plt.savefig(out / f"top_losses_seed{seed}.png", dpi=60)
    print(f"WROTE {out / f'top_losses_seed{seed}'}.png and .csv", flush=True)
    for row in ([] if labkit.smoke() else rows):
        print("TOP", *row, flush=True)
    wrong = pred != targs
    labkit.result("baseline.error_rate", wrong.float().mean(), unit="fraction")
    labkit.result("baseline.valid_errors", wrong.sum(), unit="images")
    labkit.result("baseline.top50_misclassified", wrong[idx].sum(), unit="images")


def change(learn, dls, out, seed, rank, flipped):
    weights = out / f"model_seed{seed}.pth"
    if not weights.exists():
        sys.exit(f"no baseline model: run python scripts/11_error_analysis.py --baseline --seed {seed} first")
    learn.model.load_state_dict(torch.load(weights, map_location="cpu"))
    with learn.no_bar():
        pairs = ClassificationInterpretation.from_learner(learn).most_confused(min_val=3)  # (actual, predicted, n)
    for pair in ([] if labkit.smoke() else pairs):
        print("CONFUSED", *pair, flush=True)
    actual, predicted, n = pairs[0] if pairs else ("none", "none", 0)
    labkit.result("P2.top_pair", f"{actual}/{predicted}", unit="actual/predicted")
    labkit.result("change.top_pair_count", n, unit="images")
    labkit.result("change.pairs_min3", len(pairs), unit="pairs")
    labkit.result("change.images_in_pairs_min3", sum(p[2] for p in pairs), unit="images")


def break_it(learn, dls, out, seed, rank, flipped):
    fine_tune(learn)
    train = dls.train_ds.items  # (file, label) pairs, with the flipped labels it trained on
    logits, targs, _ = predict(learn, dls.test_dl(train, with_labels=True))  # validation transforms: no augmentation
    is_flipped = torch.tensor([f in flipped for f, _ in train])
    top, idx = rank(logits, targs, K)
    labkit.result("P3.flipped_in_top50", is_flipped[idx].sum(), unit="images", k=K)
    labkit.result("break.chance_in_top50", K * is_flipped.float().mean(), unit="images")
    labkit.result("break.flipped_memorised", (logits.argmax(1) == targs)[is_flipped].float().mean(), unit="fraction")
    v_logits, v_targs, _ = predict(learn)
    labkit.result("break.error_rate", (v_logits.argmax(1) != v_targs).float().mean(), unit="fraction")


def check():
    """--check: top_losses against PyTorch on 20 rows of 5 classes; the last 5 rows have huge logits."""
    g = torch.Generator().manual_seed(0)
    logits = torch.randn(20, 5, generator=g) * torch.tensor([1.0] * 15 + [100.0] * 5).view(-1, 1)
    targets = torch.randint(0, 5, (20,), generator=g)
    for k in (1, 7, 20):
        (got, idx), (want, want_idx) = top_losses(logits, targets, k), library_top_losses(logits, targets, k)
        assert torch.isfinite(got).all(), f"k={k}: top_losses gave {got}: is it the log of softmax?"
        assert torch.allclose(got, want, rtol=1e-5, atol=1e-5), f"k={k}: losses {got}, PyTorch {want}"
        assert torch.equal(idx, want_idx), f"k={k}: idx {idx}, PyTorch {want_idx}"
    print("check: PASS")


def main():
    args = labkit.start(lab=11, device=labkit.pick_device(), extra_modes=("check",))
    if args.mode in ("check", "download"):
        return check() if args.mode == "check" else download()
    if not (PETS / "images").exists():
        sys.exit("no images: run python scripts/11_error_analysis.py --download first")
    rank = library_top_losses if labkit.smoke() else top_losses  # smoke checks the plumbing only: a library stand-in
    steps = {"baseline": baseline, "change": change, "break": break_it}
    with tempfile.TemporaryDirectory() as tmp:  # smoke keeps its model, plot and CSV here, out of results/
        out = Path(tmp) if labkit.smoke() else labkit.DATA / "results" / "lab11"
        out.mkdir(parents=True, exist_ok=True)
        for mode in (steps if labkit.smoke() else [args.mode]):  # smoke runs all three on tiny data
            set_seed(args.seed, reproducible=True)
            dls, flipped = pet_dataloaders(args.seed, args.device, flip=FLIP if mode == "break" else 0.0)
            print(f"DATA train={len(dls.train_ds)} valid={len(dls.valid_ds)} flipped={len(flipped)}", flush=True)
            learn = vision_learner(dls, resnet34, metrics=error_rate)  # ImageNet body + new head, as in lab 01
            steps[mode](learn, dls, out, args.seed, rank, flipped)


if __name__ == "__main__":  # safe if workers are turned on: macOS DataLoader workers re-import this file
    main()
