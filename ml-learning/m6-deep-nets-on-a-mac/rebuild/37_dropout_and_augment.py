"""Lab 37 rebuild: inverted dropout, and a random crop plus flip, written from memory.

Write both bodies (about 12 lines), then run: python rebuild/37_dropout_and_augment.py
check() compares with torch (F.dropout, F.pad with mode="reflect", Tensor.flip), never with the lab's results.
"""
import torch
import torch.nn.functional as F


def dropout(x, p, training):
    """Inverted dropout. If training is false, return x unchanged. Otherwise keep each element with
    probability 1 - p (the mask torch.rand_like(x) >= p) and return x * mask / (1 - p), so every element
    keeps its expected value. Same shape, dtype and device as x.
    """
    raise NotImplementedError("write this from memory")


def augment(batch, pad=4, flip_p=0.5):
    """A random crop and a horizontal flip, drawn for each image on its own. batch is N x C x H x W.

    Reflect-pad the last two dims by pad on every side (F.pad with mode="reflect"), then for each image draw
    a top-left offset dy, dx in 0 to 2 * pad and keep the H x W window there. Then flip that image left to
    right (the last dim) with probability flip_p. Return N x C x H x W, the input's shape.
    """
    raise NotImplementedError("write this from memory")


def check():
    torch.manual_seed(0)
    ones = torch.ones(200_000)
    y, lib = dropout(ones, 0.3, training=True), F.dropout(ones, 0.3, training=True)
    assert y.shape == ones.shape and y.dtype == ones.dtype, "dropout changed the shape or dtype"
    assert abs(y.mean().item() - 1) < 0.01, f"mean {y.mean().item():.4f}, not 1 within 1%: scale by 1 / (1 - p)"
    kept, lib_kept = y[y != 0], lib[lib != 0]
    assert torch.allclose(kept, lib_kept[0].expand_as(kept)), "survivors differ from F.dropout's 1 / (1 - p)"
    assert abs(kept.numel() - lib_kept.numel()) < 0.01 * ones.numel(), "keep rate differs from F.dropout's"
    x = torch.randn(4, 8)
    assert torch.equal(dropout(x, 0.3, training=False), x), "eval mode must return x unchanged"
    batch = torch.randn(16, 3, 32, 32)
    out = augment(batch)
    assert out.shape == batch.shape, f"augment changed the batch shape to {tuple(out.shape)}"
    padded = F.pad(batch, (4, 4, 4, 4), mode="reflect")
    for i in range(len(batch)):
        windows = [padded[i, :, dy:dy + 32, dx:dx + 32] for dy in range(9) for dx in range(9)]
        assert any(torch.equal(out[i], w) or torch.equal(out[i], w.flip(-1)) for w in windows), \
            f"image {i} is not a 32 x 32 window of F.pad(..., mode='reflect'), flipped or not"
    same = augment(batch[:1].expand(64, -1, -1, -1).contiguous())
    assert not all(torch.equal(same[0], s) for s in same[1:]), "draw the crop and flip per image, not per batch"
    assert torch.equal(augment(batch, pad=0, flip_p=0.0), batch), "pad 0 and flip_p 0 must return the batch"
    assert torch.equal(augment(batch, pad=0, flip_p=1.0), batch.flip(-1)), "flip_p 1 must flip every image"
    print("check: PASS")


if __name__ == "__main__":
    check()
