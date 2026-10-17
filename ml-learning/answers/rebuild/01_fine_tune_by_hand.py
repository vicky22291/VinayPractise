"""Rebuild 01: a simplified fine_tune, by hand, in plain PyTorch.

Write the two function bodies from memory, then run:  python rebuild/01_fine_tune_by_hand.py
check() compares with torch.nn and torchvision's resnet18, never with this lab's results.
"""
import math

import torch
from torch import nn
from torchvision.models import resnet18


def trainable(model):
    """Count the parameters an optimizer step can change: those with requires_grad True."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def fine_tune_by_hand(model, n_classes, train_one_epoch, epochs, base_lr):
    """A simplified fine_tune(epochs, base_lr) for a torchvision ResNet, in plain PyTorch.

    Its freezing, parameter groups and learning-rate schedule are simpler than fastai's,
    so follow these steps rather than fastai's code.
    1. Swap the head: model.fc becomes a new nn.Linear with n_classes outputs.
    2. Freeze every parameter except the new head's (the whole body), then train 1 epoch
       with Adam at base_lr.
    3. Unfreeze everything, then train `epochs` epochs with Adam and two parameter groups:
       the body at base_lr / 200 and the head at base_lr / 2. The rates stay constant.
    train_one_epoch(model, optimizer) runs one epoch. Return the model.

    Tools you may use:
        p.requires_grad = False        for p in model.parameters(), or model.fc.parameters()
        nn.Linear(model.fc.in_features, n_classes)
        model.named_parameters()       yields (name, p); the head's names start with "fc."
        torch.optim.Adam([{"params": body, "lr": a}, {"params": head, "lr": b}])
    """
    model.fc = nn.Linear(model.fc.in_features, n_classes)
    for p in model.parameters():
        p.requires_grad = False
    for p in model.fc.parameters():
        p.requires_grad = True
    train_one_epoch(model, torch.optim.Adam(model.fc.parameters(), lr=base_lr))
    for p in model.parameters():
        p.requires_grad = True
    body = [p for name, p in model.named_parameters() if not name.startswith("fc.")]
    head = list(model.fc.parameters())
    groups = [{"params": body, "lr": base_lr / 200}, {"params": head, "lr": base_lr / 2}]
    optimizer = torch.optim.Adam(groups)
    for _ in range(epochs):
        train_one_epoch(model, optimizer)
    return model


def check():
    seen = []

    def one_epoch(model, optimizer):  # one real step on random images, then record what could train
        before = model.conv1.weight.detach().clone()
        x, y = torch.randn(4, 3, 64, 64), torch.randint(0, 37, (4,))
        optimizer.zero_grad()
        nn.functional.cross_entropy(model(x), y).backward()
        optimizer.step()
        lrs = [g["lr"] for g in optimizer.param_groups]
        seen.append((trainable(model), lrs, not torch.equal(before, model.conv1.weight)))

    torch.manual_seed(0)
    model = fine_tune_by_hand(resnet18(weights=None), 37, one_epoch, epochs=2, base_lr=2e-3)
    head = sum(p.numel() for p in nn.Linear(512, 37).parameters())       # torch.nn's count
    full = sum(p.numel() for p in resnet18(num_classes=37).parameters())  # torchvision's count
    assert (head, full) == (18_981, 11_195_493), (head, full)
    assert model.fc.out_features == 37, "the new head needs 37 outputs"
    assert [s[0] for s in seen] == [head, full, full], f"trainable per epoch: {[s[0] for s in seen]}"
    assert math.isclose(seen[0][1][-1], 2e-3), f"the frozen epoch trains the head at base_lr: {seen[0][1]}"
    for _, lrs, _ in seen[1:]:
        assert len(lrs) == 2 and all(map(math.isclose, sorted(lrs), (1e-5, 1e-3))), f"unfrozen lrs: {lrs}"
    assert [s[2] for s in seen] == [False, True, True], "the body must change only after unfreezing"
    print("check: PASS")


if __name__ == "__main__":
    check()
