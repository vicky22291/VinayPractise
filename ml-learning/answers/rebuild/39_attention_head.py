"""39 rebuild, solution: one head of causal self-attention, and a test that the mask holds.

Run: python rebuild/39_attention_head.py
check() compares your head with torch's F.scaled_dot_product_attention(is_causal=True), then runs your
assert_causal on your head, then again after setting its tril to all ones. It never uses this lab's results.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class Head(nn.Module):
    """One head of causal self-attention: x (B, T, n_embd) -> (B, T, head_size).

    Attributes check() uses: self.key, self.query and self.value, each nn.Linear(n_embd, head_size,
    bias=False), and a buffer self.tril of shape (block_size, block_size), lower-triangular ones.
    forward: scores q @ k^T scaled by head_size ** -0.5, masked_fill with -inf where tril is 0,
    softmax over the last dimension, then @ v.
    """

    def __init__(self, n_embd, head_size, block_size):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))

    def forward(self, x):
        T = x.shape[1]
        k, q, v = self.key(x), self.query(x), self.value(x)
        wei = q @ k.transpose(-2, -1) * k.shape[-1] ** -0.5
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))
        return F.softmax(wei, dim=-1) @ v


def assert_causal(head, x, t):
    """Change every token after position t, and assert the outputs at positions 0 to t stay the same."""
    x2 = x.clone()
    x2[:, t + 1:] = torch.randn_like(x2[:, t + 1:])
    assert torch.allclose(head(x)[:, :t + 1], head(x2)[:, :t + 1], atol=1e-6)


def check():
    torch.manual_seed(0)
    head = Head(32, 16, 64)
    x = torch.randn(2, 20, 32)
    with torch.no_grad():
        ref = F.scaled_dot_product_attention(head.query(x), head.key(x), head.value(x), is_causal=True)
        assert torch.allclose(head(x), ref, atol=1e-6), "Head differs from F.scaled_dot_product_attention"
        assert_causal(head, x, 9)
        head.tril.fill_(1.0)  # the same head with its mask deleted
        try:
            assert_causal(head, x, 9)
        except AssertionError:
            print("check: PASS")
            return
    raise AssertionError("assert_causal passed a head whose mask was deleted")


if __name__ == "__main__":
    check()
