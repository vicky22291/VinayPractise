"""Lab 28 rebuild: the mean-image baseline and one epoch of SGD by hand.

Write the three function bodies from memory, then run from the module folder:
    python rebuild/28_mean_image_and_sgd.py
check() compares with scipy, scikit-learn and torch on made-up data, never with the lab's results.
"""
import numpy as np
import torch
import torch.nn.functional as F
from scipy.spatial.distance import cdist
from sklearn.metrics import accuracy_score


def mean_image_accuracy(train3, train7, valid3, valid7):
    """Accuracy of 'closer to the mean 3 or the mean 7' on valid3 plus valid7.

    Inputs are float tensors of shape (N, 28, 28). The two mean images come from
    train3 and train7. Distance is L1: the mean absolute pixel difference.
    Returns correct / total as a float.
    """
    mean3, mean7 = train3.mean(0), train7.mean(0)

    def is_3(x):
        return (x - mean3).abs().mean((-1, -2)) < (x - mean7).abs().mean((-1, -2))
    correct = is_3(valid3).sum() + (~is_3(valid7)).sum()
    return correct.item() / (len(valid3) + len(valid7))


def mnist_loss(preds, targets):
    """fastbook's mnist_loss. preds are raw model outputs, targets are 1 (a 3) or 0 (a 7), both shape (N, 1)."""
    preds = preds.sigmoid()
    return torch.where(targets == 1, 1 - preds, preds).mean()


def sgd_epoch(w, b, x, y, lr, bs):
    """One pass over x and y in order, in batches of bs, for the model x @ w + b.

    Per batch: mnist_loss, backward, then under torch.no_grad() move w and b
    by -lr times their gradients and zero the gradients. Changes w and b in place.
    """
    for i in range(0, len(x), bs):
        loss = mnist_loss(x[i:i + bs] @ w + b, y[i:i + bs])
        loss.backward()
        with torch.no_grad():
            for p in (w, b):
                p -= lr * p.grad
                p.grad.zero_()


def check():
    """Compare with scipy, scikit-learn and torch on made-up data."""
    rng = np.random.default_rng(0)
    proto3, proto7 = rng.random((28, 28)), rng.random((28, 28))

    def digits(proto, n):  # made-up float64 images: a prototype plus noise
        return torch.from_numpy(proto + rng.normal(0, 3.0, (n, 28, 28)))
    t3, t7, v3, v7 = digits(proto3, 40), digits(proto7, 40), digits(proto3, 25), digits(proto7, 25)
    centres = torch.stack([t3.mean(0), t7.mean(0)]).reshape(2, -1).numpy()
    nearest = cdist(torch.cat([v3, v7]).reshape(50, -1).numpy(), centres, metric="cityblock").argmin(1)
    want = accuracy_score([0] * 25 + [1] * 25, nearest)
    got = mean_image_accuracy(t3, t7, v3, v7)
    assert abs(got - want) < 1e-12, f"mean_image_accuracy gave {got}; scipy cdist plus accuracy_score give {want}"

    torch.manual_seed(0)
    preds, targets = torch.randn(64, 1) * 3, (torch.rand(64, 1) > 0.5).float()
    want = F.l1_loss(preds.sigmoid(), targets)
    assert torch.allclose(mnist_loss(preds, targets), want, rtol=0, atol=1e-7), "mnist_loss differs from F.l1_loss on sigmoid outputs"

    x, y = torch.rand(20, 12), (torch.arange(20) % 2).float().unsqueeze(1)
    w0, b0 = torch.randn(12, 1) * 0.5, torch.randn(1) * 0.5
    for bs in (20, 8):  # one step on all 20 rows, then three steps of 8, 8 and 4
        w, b = w0.clone().requires_grad_(), b0.clone().requires_grad_()
        sgd_epoch(w, b, x, y, lr=0.5, bs=bs)
        w2, b2 = w0.clone().requires_grad_(), b0.clone().requires_grad_()
        opt = torch.optim.SGD([w2, b2], lr=0.5)
        for i in range(0, len(x), bs):
            opt.zero_grad()
            mnist_loss(x[i:i + bs] @ w2 + b2, y[i:i + bs]).backward()
            opt.step()
        assert not torch.equal(w2, w0), "fixture problem: torch.optim.SGD did not move the weights"
        assert torch.equal(w, w2) and torch.equal(b, b2), f"sgd_epoch with bs={bs} differs from torch.optim.SGD"
    print("check: PASS")


if __name__ == "__main__":
    check()
