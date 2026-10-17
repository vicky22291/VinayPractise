"""Lab 34 rebuild: a 3x3 convolution with two loops, then a batched convolution as one matrix multiply.

Write both bodies from memory (about 15 lines in all), then run: python rebuild/34_conv2d.py
check() compares with torch's F.conv2d at stride 1 and 2 and padding 0 and 1, never with the lab's results.
"""
import torch
import torch.nn.functional as F


def conv_one(img, kernel):
    """Slide a 3x3 kernel over one (h, w) image, stride 1, no padding: an (h - 2, w - 2) output.

    Two loops over the output positions. Each output is the 3x3 window of img under the
    kernel, times the kernel, summed. No F.conv2d or F.unfold.
    """
    h, w = img.shape
    out = torch.zeros(h - 2, w - 2, dtype=img.dtype)
    for i in range(h - 2):
        for j in range(w - 2):
            out[i, j] = (img[i:i + 3, j:j + 3] * kernel).sum()
    return out


def conv_batch(x, weight, stride=1, padding=0):
    """A batch x of shape (n, c, h, w) and oc kernels weight of shape (oc, c, k, k), no bias.

    Return the (n, oc, out_h, out_w) output of F.conv2d(x, weight, stride=stride, padding=padding),
    built from F.unfold (every k x k window becomes one column) and one matrix multiply.
    Work out out_h and out_w yourself. No F.conv2d.
    """
    n, _, h, w = x.shape
    oc, _, k, _ = weight.shape
    cols = F.unfold(x, k, padding=padding, stride=stride)  # (n, c * k * k, out_h * out_w)
    out = weight.view(oc, -1) @ cols  # (oc, c * k * k) @ (n, c * k * k, L) -> (n, oc, L)
    out_h = (h + 2 * padding - k) // stride + 1
    out_w = (w + 2 * padding - k) // stride + 1
    return out.view(n, oc, out_h, out_w)


def check():
    g = torch.Generator().manual_seed(34)
    img, kernel = torch.rand(9, 11, generator=g), torch.randn(3, 3, generator=g)
    ref = F.conv2d(img[None, None], kernel[None, None])[0, 0]
    mine = conv_one(img, kernel)
    assert mine.shape == ref.shape, f"conv_one shape {tuple(mine.shape)} vs F.conv2d {tuple(ref.shape)}"
    assert torch.allclose(mine, ref, atol=1e-5), "conv_one differs from F.conv2d"
    x, weight = torch.randn(4, 3, 10, 9, generator=g), torch.randn(5, 3, 3, 3, generator=g)
    for stride in (1, 2):
        for padding in (0, 1):
            ref = F.conv2d(x, weight, stride=stride, padding=padding)
            mine = conv_batch(x, weight, stride, padding)
            where = f"at stride {stride}, padding {padding}"
            assert mine.shape == ref.shape, f"conv_batch shape {tuple(mine.shape)} vs F.conv2d {tuple(ref.shape)} {where}"
            assert torch.allclose(mine, ref, atol=1e-5), f"conv_batch differs from F.conv2d {where}"
    print("check: PASS")


if __name__ == "__main__":
    check()
