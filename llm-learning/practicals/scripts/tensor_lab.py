#!/usr/bin/env python3
"""Synthetic tensor mechanisms. No datasets, downloads, or LLM training."""
import argparse
import json
import math
import torch
import torch.nn.functional as F


def rotation(theta):
    c, s = math.cos(theta), math.sin(theta)
    return torch.tensor([[c, -s], [s, c]])


def quantize(weights, bits, group_size):
    if bits not in (4, 8) or group_size < 1:
        raise ValueError("bits must be 4 or 8 and group size must be positive")
    limit = 2 ** (bits - 1) - 1
    codes, scales = [], []
    for group in weights.flatten().split(group_size):
        maximum = float(group.abs().max())
        scale = maximum / limit if maximum else 1.0
        scales.append(scale)
        codes.extend(torch.round(group / scale).clamp(-limit, limit).to(torch.int64).tolist())
    if bits == 8:
        packed = bytes(c + 128 for c in codes)
        restored_codes = [c - 128 for c in packed]
    else:
        unsigned = [c + 7 for c in codes]
        if len(unsigned) % 2:
            unsigned.append(7)
        packed = bytes(unsigned[i] | (unsigned[i + 1] << 4) for i in range(0, len(unsigned), 2))
        restored_codes = []
        for value in packed:
            restored_codes.extend([(value & 15) - 7, (value >> 4) - 7])
        restored_codes = restored_codes[:len(codes)]
    scales = torch.tensor(scales, dtype=torch.float32)
    decoded = torch.tensor([
        c * float(scales[i // group_size]) for i, c in enumerate(restored_codes)
    ], dtype=weights.dtype).reshape(weights.shape)
    return decoded, packed, scales


def run(args):
    torch.manual_seed(args.seed)
    topic = args.topic
    if topic == "shapes":
        table = torch.randn(16, 8)
        ids = torch.tensor([[1, 2, 3]])
        hidden = table[ids]
        logits = hidden @ table.T
        return {"ids": list(ids.shape), "hidden": list(hidden.shape), "logits": list(logits.shape)}
    if topic == "loss":
        z = torch.tensor([[0.8, -0.2, 0.1]], requires_grad=True)
        loss = F.cross_entropy(z, torch.tensor([1]))
        loss.backward()
        analytic = z.detach().softmax(-1) - torch.tensor([[0.0, 1.0, 0.0]])
        return {"loss": float(loss.detach()), "probabilities": z.detach().softmax(-1).tolist(),
                "gradient": z.grad.tolist(), "gradient_identity": torch.allclose(z.grad, analytic)}
    if topic == "attention":
        x = torch.randn(1, 4, 8)
        wq, wk, wv = [torch.randn(8, 4) for _ in range(3)]
        def attend(states):
            q, k, v = states @ wq, states @ wk, states @ wv
            scores = q @ k.transpose(-2, -1) / 2
            if not args.unmasked:
                scores = scores.masked_fill(torch.ones(4, 4, dtype=torch.bool).triu(1), float("-inf"))
            weights = scores.softmax(-1)
            return weights @ v, weights
        out, weights = attend(x)
        changed = x.clone()
        changed[:, 2:, :] += args.future_shift
        out_changed, _ = attend(changed)
        return {"weights": weights.tolist(), "output_shape": list(out.shape),
                "prefix_change": float((out[:, :2] - out_changed[:, :2]).abs().max()),
                "mask_enabled": not args.unmasked}
    if topic == "positions":
        q, k = torch.tensor([1.0, 2.0]), torch.tensor([-1.0, 0.5])
        m, n, theta = 2, 5, 0.3
        left = (rotation(m * theta) @ q) @ (rotation(n * theta) @ k)
        right = q @ (rotation((n - m) * theta) @ k)
        return {"rotated_dot": float(left), "relative_dot": float(right),
                "identity_error": float((left - right).abs())}
    if topic == "precision":
        x = torch.tensor([1.0, 1.001, 1e-8, 1e5], dtype=torch.float32)
        return {str(dtype): {"stored_bytes": x.numel() * torch.tensor([], dtype=dtype).element_size(),
                            "values": [float(v) if math.isfinite(float(v)) else str(float(v))
                                       for v in x.to(dtype).float()]}
                for dtype in [torch.float32, torch.float16, torch.bfloat16]}
    if topic == "instruction":
        logits = torch.randn(1, 3, 16)
        targets = torch.tensor([[11, 12, 13]])
        losses = F.cross_entropy(logits.flatten(0, 1), targets.flatten(), reduction="none")
        mask = torch.tensor([False, True, True])
        return {"per_position_loss": losses.tolist(), "all_token_mean": float(losses.mean()),
                "response_token_mean": float(losses[mask].mean()), "supervised_tokens": int(mask.sum())}
    if topic == "lora":
        w0 = torch.randn(12, 16)
        x = torch.randn(24, 16)
        desired = x @ (w0 + torch.randn(12, 2) @ torch.randn(2, 16) * 0.05).T
        a = torch.nn.Parameter(torch.randn(args.rank, 16) * 0.02)
        b = torch.nn.Parameter(torch.zeros(12, args.rank))
        optimizer = torch.optim.Adam([a, b], lr=0.03)
        def loss():
            return F.mse_loss(x @ w0.T + (x @ a.T) @ b.T, desired)
        before = float(loss().detach())
        for _ in range(args.steps):
            optimizer.zero_grad()
            value = loss()
            value.backward()
            optimizer.step()
        return {"initial_mse": before, "final_mse": float(loss().detach()),
                "rank": args.rank, "adapter_entries": a.numel() + b.numel(),
                "base_entries": w0.numel(), "base_frozen": not w0.requires_grad,
                "scope": "synthetic linear-map fitting, not LLM fine-tuning"}
    if topic == "preferences":
        chosen = torch.tensor(-2.0, requires_grad=True)
        rejected = torch.tensor(-3.0, requires_grad=True)
        margin = args.beta * ((chosen - (-2.4)) - (rejected - (-2.8)))
        loss = -F.logsigmoid(margin)
        loss.backward()
        return {"margin": float(margin.detach()), "pair_loss": float(loss.detach()),
                "chosen_logprob_gradient": float(chosen.grad),
                "rejected_logprob_gradient": float(rejected.grad),
                "scope": "synthetic scalar objective, not a normalized sequence model"}
    if topic == "quantization":
        w = torch.randn(65)
        if args.outlier:
            w[0] = args.outlier
        decoded, packed, scales = quantize(w, args.bits, args.group_size)
        return {"bits": args.bits, "group_size": args.group_size,
                "mse": float((w - decoded).square().mean()), "max_error": float((w - decoded).abs().max()),
                "code_bytes": len(packed), "fp32_scale_bytes": scales.numel() * scales.element_size(),
                "original_fp32_bytes": w.numel() * w.element_size(),
                "scope": "packed uniform codes and reconstruction; no optimized matmul kernel"}
    raise ValueError(topic)


def smoke():
    z = torch.tensor([[1.0, 2.0, -1.0]], requires_grad=True)
    loss = F.cross_entropy(z, torch.tensor([2]))
    loss.backward()
    assert torch.allclose(z.grad, z.detach().softmax(-1) - torch.tensor([[0.0, 0.0, 1.0]]))
    for bits in (4, 8):
        for w in (torch.zeros(7), torch.tensor([-1.0, 0.3, 2.0, -0.2, 0.0])):
            decoded, packed, scales = quantize(w, bits, 3)
            assert decoded.shape == w.shape and torch.isfinite(decoded).all()
            assert len(packed) == (w.numel() if bits == 8 else (w.numel() + 1) // 2)
            bound = torch.tensor([scales[i // 3] / 2 + 1e-6 for i in range(w.numel())])
            assert torch.all((w - decoded).abs() <= bound)
    print("SMOKE tensor mechanisms ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--topic", choices=["shapes", "loss", "attention", "positions", "precision",
                        "instruction", "lora", "preferences", "quantization"], default="shapes")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--future-shift", type=float, default=3.0)
    parser.add_argument("--unmasked", action="store_true")
    parser.add_argument("--rank", type=int, default=2)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--beta", type=float, default=1.0)
    parser.add_argument("--bits", type=int, choices=[4, 8], default=8)
    parser.add_argument("--group-size", type=int, default=16)
    parser.add_argument("--outlier", type=float, default=0.0)
    args = parser.parse_args()
    if args.rank < 1 or args.steps < 0 or args.group_size < 1 or args.beta <= 0:
        parser.error("rank/group-size/beta must be positive; steps must be nonnegative")
    if args.smoke:
        smoke()
    else:
        print("RESULT " + json.dumps({"fixture": "synthetic", "topic": args.topic, **run(args)}, allow_nan=False))


if __name__ == "__main__":
    main()
