"""28. Pixel baseline, then SGD by hand: loss, gradient and learning rate. A mean-image baseline on 3s vs 7s, then hand-written SGD on a linear model and on a net with one hidden layer of 30 ReLU units.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy and torch: it sets cache defaults
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image

URL = "https://s3.amazonaws.com/fast-ai-sample/mnist_sample.tgz"  # fastai URLs.MNIST_SAMPLE
ROOT = labkit.DATA / "mnist_sample"
LR, BS, EPOCHS, HIDDEN = 1.0, 256, 20, 30  # fastbook ch 4: learning rate 1.0, batch size 256

args = labkit.start(lab=28, device="cpu")


def load(split, digit, limit=None):
    """Every PNG in <split>/<digit> as floats in [0, 1], shape (N, 28, 28)."""
    files = sorted((ROOT / "mnist_sample" / split / digit).glob("*.png"))[:limit]
    return torch.tensor(np.stack([np.array(Image.open(f)) for f in files])).float() / 255


def mean_image_accuracy(train3, train7, valid3, valid7):
    """Share of validation images that sit closer to their own digit's mean image, by L1 distance."""
    mean3, mean7 = train3.mean(0), train7.mean(0)

    def is_3(x):  # mean absolute pixel difference to each mean image
        return (x - mean3).abs().mean((-1, -2)) < (x - mean7).abs().mean((-1, -2))
    correct = is_3(valid3).sum() + (~is_3(valid7)).sum()
    return correct.item() / (len(valid3) + len(valid7))


def mnist_loss(preds, targets):
    """fastbook's mnist_loss: the sigmoid of each prediction, scored against a target of 1 (a 3) or 0 (a 7)."""
    preds = preds.sigmoid()
    return torch.where(targets == 1, 1 - preds, preds).mean()  # Q: what does mnist_loss return for a perfect prediction?


def init(*shape):
    """Parameters drawn from N(0, 1) that record gradients, like fastbook's init_params."""
    return torch.randn(shape).requires_grad_()


def linear(params, x):
    w, b = params
    return x @ w + b


def hidden(params, x):
    w1, b1, w2, b2 = params
    return (x @ w1 + b1).relu() @ w2 + b2  # relu(z) = max(z, 0): the non-linearity


def sgd_epoch(model, params, x, y, lr, bs):
    """One pass over (x, y) in batches of bs: loss, gradients, update. Returns every batch loss."""
    losses = []
    for i in range(0, len(x), bs):
        loss = mnist_loss(model(params, x[i:i + bs]), y[i:i + bs])
        loss.backward()  # backward pass: gradient of loss for every parameter, in p.grad
        with torch.no_grad():  # Q: why does the update run under torch.no_grad()?
            for p in params:
                p -= lr * p.grad
                p.grad.zero_()  # Q: why are the gradients zeroed after every step?
        losses.append(loss.item())
    return losses


def accuracy(model, params, x, y):
    with torch.no_grad():
        return ((model(params, x).sigmoid() > 0.5).float() == y).float().mean().item()


def train(model, params, lr):
    """EPOCHS rounds of: shuffle, one SGD pass, validation accuracy."""
    shuffles = torch.Generator().manual_seed(args.seed)  # its own RNG, apart from init: every model gets the same batch order
    steps, epoch_losses, accs = [], [], []
    for _ in range(EPOCHS):
        order = torch.randperm(len(train_x), generator=shuffles)  # a new seeded shuffle every epoch
        losses = sgd_epoch(model, params, train_x[order], train_y[order], lr, BS)
        steps += losses
        epoch_losses.append(np.average(losses, weights=[len(b) for b in order.split(BS)]))  # mean loss per image: the last batch is smaller
        accs.append(accuracy(model, params, valid_x, valid_y))
    return steps, epoch_losses, accs


def loss_outcome(steps, epoch_losses):
    """P3's options, judged on the training loss: any NaN or inf, a fall to under half, or neither."""
    if not np.isfinite(steps).all():
        return "diverges_to_nan"
    return "still_falls" if epoch_losses[-1] < 0.5 * epoch_losses[0] else "oscillates_or_stalls"


def report_loss(step_name, steps, epoch_losses):
    """Print the loss curve (one mean per epoch) and save the per-step curve as a plot."""
    labkit.result(f"{step_name}.epoch_losses", ",".join(f"{v:.4g}" for v in epoch_losses))
    labkit.result(f"{step_name}.loss_ratio", epoch_losses[-1] / epoch_losses[0], unit="epoch20/epoch1")
    out = labkit.DATA / "results" / "lab28" / f"loss-{step_name}-seed{args.seed}.png"
    plt.figure(figsize=(7, 3))
    plt.plot(steps)
    plt.gca().set(xlabel="SGD step", ylabel="batch loss", title=f"lab 28 {step_name}, seed {args.seed}")
    if labkit.smoke():  # a loss curve is a result, so smoke draws the plot but saves no file
        plt.gcf().canvas.draw()
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out, dpi=100, bbox_inches="tight")
        print(f"PLOT {out}", flush=True)
    plt.close()


if args.mode == "download":
    labkit.extract(labkit.fetch(URL, ROOT / "mnist_sample.tgz", size=3_214_948), ROOT)
    print(f"DATA {ROOT / 'mnist_sample'}", flush=True)
    sys.exit(0)

n = 40 if labkit.smoke() else None  # smoke: 40 images per folder, same code path
train3, train7 = load("train", "3", n), load("train", "7", n)
valid3, valid7 = load("valid", "3", n), load("valid", "7", n)
train_x = torch.cat([train3, train7]).view(-1, 28 * 28)  # one row of 784 pixels per image
train_y = torch.tensor([1.0] * len(train3) + [0.0] * len(train7)).unsqueeze(1)  # a 3 is 1, a 7 is 0
valid_x = torch.cat([valid3, valid7]).view(-1, 28 * 28)
valid_y = torch.tensor([1.0] * len(valid3) + [0.0] * len(valid7)).unsqueeze(1)

if args.mode in ("baseline", "smoke"):  # P1: no learning at all; then the linear model at LR
    labkit.result("P1.mean_image_acc", mean_image_accuracy(train3, train7, valid3, valid7), unit="fraction")
    steps, epoch_losses, accs = train(linear, [init(28 * 28, 1), init(1)], LR)
    for e in (1, 5, 20):
        labkit.result(f"baseline.acc_epoch{e}", accs[e - 1], unit="fraction")
    report_loss("baseline", steps, epoch_losses)
    labkit.result("baseline.loss_outcome", loss_outcome(steps, epoch_losses))

if args.mode in ("change", "smoke"):  # P2: one hidden layer of 30 ReLU units, everything else the same
    linear_acc = accs[-1] if labkit.smoke() else labkit.prior("baseline.acc_epoch20")  # smoke: the linear run above
    steps, epoch_losses, accs = train(hidden, [init(28 * 28, HIDDEN), init(HIDDEN), init(HIDDEN, 1), init(1)], LR)
    for e in (1, 5):
        labkit.result(f"change.acc_epoch{e}", accs[e - 1], unit="fraction")
    labkit.result("P2.acc_epoch20", accs[-1], unit="fraction")
    if linear_acc is None:  # prior() reads what your --baseline run stored for this seed
        print("NOTE run --baseline with this seed first to get P2.delta_vs_linear", flush=True)
    else:
        labkit.result("P2.delta_vs_linear", accs[-1] - linear_acc, unit="fraction")
    report_loss("change", steps, epoch_losses)

if args.mode in ("break", "smoke"):  # P3: the linear model again, with the learning rate x 100
    steps, epoch_losses, accs = train(linear, [init(28 * 28, 1), init(1)], LR * 100)
    labkit.result("break.acc_epoch20", accs[-1], unit="fraction")
    report_loss("break", steps, epoch_losses)
    labkit.result("P3.loss_outcome", loss_outcome(steps, epoch_losses))
