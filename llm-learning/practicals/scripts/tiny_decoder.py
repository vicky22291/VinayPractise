#!/usr/bin/env python3
"""Educational byte decoder: explicit attention, training, evaluation, and KV caches.

No downloads or package installation. Synthetic fixtures are used only by --smoke
and an untrained --cache demonstration. Training requires --text and --out.
"""
import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import time
import torch
from torch import nn
import torch.nn.functional as F


@dataclass
class Config:
    context: int = 64
    width: int = 64
    layers: int = 2
    heads: int = 4

    def validate(self):
        if self.context < 8 or min(self.width, self.layers, self.heads) < 1:
            raise ValueError("context must be at least 8; dimensions must be positive")
        if self.width % self.heads:
            raise ValueError("width must be divisible by heads")


class Attention(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.heads = config.heads
        self.head_width = config.width // config.heads
        self.qkv = nn.Linear(config.width, 3 * config.width, bias=False)
        self.proj = nn.Linear(config.width, config.width, bias=False)

    def forward(self, x, past=None):
        batch, length, width = x.shape
        def split(t):
            return t.view(batch, length, self.heads, self.head_width).transpose(1, 2)
        q, k, v = [split(t) for t in self.qkv(x).chunk(3, dim=-1)]
        offset = 0 if past is None else past[0].size(-2)
        if past is not None:
            k = torch.cat([past[0], k], dim=-2)
            v = torch.cat([past[1], v], dim=-2)
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.head_width)
        query_positions = torch.arange(offset, offset + length, device=x.device)[:, None]
        key_positions = torch.arange(k.size(-2), device=x.device)[None, :]
        scores = scores.masked_fill(key_positions > query_positions, float("-inf"))
        values = scores.softmax(-1) @ v
        values = values.transpose(1, 2).contiguous().view(batch, length, width)
        return self.proj(values), (k, v)


class Block(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.norm1 = nn.LayerNorm(config.width)
        self.attention = Attention(config)
        self.norm2 = nn.LayerNorm(config.width)
        self.mlp = nn.Sequential(nn.Linear(config.width, 4 * config.width, bias=False),
                                 nn.GELU(), nn.Linear(4 * config.width, config.width, bias=False))

    def forward(self, x, past=None):
        update, cache = self.attention(self.norm1(x), past)
        x = x + update
        return x + self.mlp(self.norm2(x)), cache


class Decoder(nn.Module):
    def __init__(self, config):
        super().__init__()
        config.validate()
        self.config = config
        self.tokens = nn.Embedding(256, config.width)
        self.positions = nn.Embedding(config.context, config.width)
        self.blocks = nn.ModuleList(Block(config) for _ in range(config.layers))
        self.norm = nn.LayerNorm(config.width)
        self.apply(self.initialize)

    @staticmethod
    def initialize(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, ids, past=None):
        if ids.ndim != 2 or ids.size(1) == 0:
            raise ValueError("ids must be a nonempty B by T tensor")
        if past is not None and len(past) != len(self.blocks):
            raise ValueError("one cache pair is required per block")
        offset = 0 if past is None else past[0][0].size(-2)
        if offset + ids.size(1) > self.config.context:
            raise ValueError("context limit exceeded; no silent position rollover")
        pos = torch.arange(offset, offset + ids.size(1), device=ids.device)
        x = self.tokens(ids) + self.positions(pos)[None, :, :]
        caches = []
        for i, block in enumerate(self.blocks):
            x, cache = block(x, None if past is None else past[i])
            caches.append(cache)
        return F.linear(self.norm(x), self.tokens.weight), caches


def result(**fields):
    print("RESULT " + json.dumps(fields, allow_nan=False))


def device_for(name):
    if name == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS unavailable in this interpreter; choose a verified device")
    if name == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA unavailable in this interpreter")
    return torch.device(name)


def corpus(path, context):
    raw = Path(path).expanduser().read_bytes()
    boundary = int(len(raw) * 0.9)
    data = torch.tensor(list(raw), dtype=torch.long)
    train, valid = data[:boundary], data[boundary:]
    if min(len(train), len(valid)) < context + 1:
        raise ValueError("both partitions need at least context+1 bytes; supply a larger corpus")
    return train, valid, {"sha256": hashlib.sha256(raw).hexdigest(),
                          "bytes": len(raw), "split_byte": boundary,
                          "tokenizer": "utf8-bytes-v1"}


@torch.no_grad()
def evaluate(model, data, device, max_windows):
    was_training = model.training
    model.eval()
    length = model.config.context
    total, tokens, windows = 0.0, 0, 0
    for start in range(0, len(data) - length, length):
        if windows >= max_windows:
            break
        section = data[start:start + length + 1].to(device)
        logits, _ = model(section[:-1][None, :])
        loss = F.cross_entropy(logits.flatten(0, 1), section[1:], reduction="sum")
        total += float(loss)
        tokens += length
        windows += 1
    model.train(was_training)
    if not tokens:
        raise ValueError("no complete evaluation window")
    nll = total / tokens
    return {"nll_nats_per_byte": nll, "perplexity_per_byte": math.exp(nll),
            "scored_tokens": tokens, "windows": windows,
            "protocol": "fixed windows, reset context, held-out suffix"}


def load(path, device):
    checkpoint = torch.load(Path(path).expanduser(), map_location="cpu", weights_only=True)
    if checkpoint.get("format") != "llm-learning-byte-decoder-v1":
        raise ValueError("not this teaching decoder's checkpoint format")
    if checkpoint["data"]["tokenizer"] != "utf8-bytes-v1":
        raise ValueError("incompatible tokenizer")
    model = Decoder(Config(**checkpoint["config"])).to(device)
    model.load_state_dict(checkpoint["model"])
    return model, checkpoint


def device_rng(device):
    if device.type == "cuda":
        return torch.cuda.get_rng_state(device)
    if device.type == "mps":
        return torch.mps.get_rng_state()
    return None


def restore_rng(state, device):
    torch.set_rng_state(state["cpu"].cpu())
    if state["device"] is not None:
        if state["device_type"] != device.type:
            raise ValueError("resume device differs from saved generator state")
        if device.type == "cuda":
            torch.cuda.set_rng_state(state["device"].cpu(), device)
        elif device.type == "mps":
            torch.mps.set_rng_state(state["device"].cpu())
    elif state["device_type"] != device.type:
        raise ValueError("resume device changed; start an explicitly new experiment")


def train(args, device):
    if not args.text or not args.out:
        raise ValueError("--train requires --text and --out")
    output = Path(args.out).expanduser()
    if output.exists() and (not args.resume or output.resolve() != Path(args.resume).expanduser().resolve()):
        raise ValueError("output exists; choose a new path or explicitly resume that checkpoint")
    torch.manual_seed(args.seed)
    if args.resume:
        model, checkpoint = load(args.resume, device)
        settings = checkpoint["train_settings"]
        completed = checkpoint["step"]
    else:
        model = Decoder(Config(args.context, args.width, args.layers, args.heads)).to(device)
        settings = {"batch": args.batch, "lr": args.lr, "seed": args.seed, "clip": 1.0}
        completed, checkpoint = 0, None
    training, validation, identity = corpus(args.text, model.config.context)
    if checkpoint and identity != checkpoint["data"]:
        raise ValueError("corpus fingerprint or partition differs from checkpoint")
    optimizer = torch.optim.AdamW(model.parameters(), lr=settings["lr"])
    if checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer"])
        restore_rng(checkpoint["rng"], device)
    initial = evaluate(model, validation, device, args.max_eval_windows)
    model.train()
    started = time.perf_counter()
    last_loss = None
    for _ in range(args.steps):
        starts = torch.randint(len(training) - model.config.context, (settings["batch"],))
        slices = torch.stack([training[int(i):int(i) + model.config.context + 1] for i in starts]).to(device)
        logits, _ = model(slices[:, :-1])
        loss = F.cross_entropy(logits.reshape(-1, 256), slices[:, 1:].reshape(-1))
        if not torch.isfinite(loss):
            raise ValueError("nonfinite loss; checkpoint not replaced")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), settings["clip"], error_if_nonfinite=True)
        optimizer.step()
        last_loss = float(loss.detach())
    if device.type == "mps":
        torch.mps.synchronize()
    elif device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - started
    final = evaluate(model, validation, device, args.max_eval_windows)
    state = {"format": "llm-learning-byte-decoder-v1", "config": asdict(model.config),
             "model": model.state_dict(), "optimizer": optimizer.state_dict(),
             "step": completed + args.steps, "data": identity, "train_settings": settings,
             "rng": {"cpu": torch.get_rng_state(), "device": device_rng(device), "device_type": device.type},
             "torch_version": str(torch.__version__)}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    torch.save(state, temporary)
    temporary.replace(output)
    result(device=str(device), torch=str(torch.__version__), config=asdict(model.config),
           updates_this_run=args.steps, completed_updates=state["step"], train_seconds=elapsed,
           last_training_batch_loss=last_loss, initial_validation=initial, final_validation=final,
           checkpoint=str(output), data=identity)


@torch.no_grad()
def cache_comparison(model, device, length):
    if length < 2 or length > model.config.context:
        raise ValueError("cache comparison length must be within context and at least two")
    model.eval()
    ids = torch.arange(length, device=device)[None, :] % 256
    full, _ = model(ids)
    prefix = length // 2
    first, cache = model(ids[:, :prefix])
    pieces = [first]
    for position in range(prefix, length):
        logits, cache = model(ids[:, position:position + 1], cache)
        pieces.append(logits)
    combined = torch.cat(pieces, dim=1)
    return {"max_logit_error": float((full - combined).abs().max()),
            "cache_payload_bytes": sum(t.numel() * t.element_size() for pair in cache for t in pair),
            "batch": 1, "cached_tokens": length, "scope": "structural comparison, not a serving benchmark"}


@torch.no_grad()
def generate(args, model, device):
    ids = list(args.prompt.encode("utf-8"))
    if not ids:
        raise ValueError("provide a nonempty prompt")
    if len(ids) + args.max_new_tokens > model.config.context:
        raise ValueError("prompt plus output budget exceeds this model's context")
    model.eval()
    torch.manual_seed(args.seed)
    logits, cache = model(torch.tensor([ids], device=device))
    for index in range(args.max_new_tokens):
        scores = logits[:, -1, :]
        if args.temperature == 0:
            token = scores.argmax(-1, keepdim=True)
        else:
            scores = scores / args.temperature
            if args.top_k:
                threshold = torch.topk(scores, args.top_k).values[:, -1:]
                scores = scores.masked_fill(scores < threshold, float("-inf"))
            probabilities = scores.softmax(-1)
            # Sample on CPU so the same explicit sampling path works on MPS too.
            token = torch.multinomial(probabilities.cpu(), 1).to(device)
        ids.append(int(token.item()))
        if index + 1 < args.max_new_tokens:
            logits, cache = model(token, cache)
    result(text=bytes(ids).decode("utf-8", errors="replace"), raw_byte_ids=ids,
           utf8_policy="replace invalid generated sequences for display", seed=args.seed,
           temperature=args.temperature, max_new_tokens=args.max_new_tokens)


def smoke():
    torch.set_num_threads(1)
    torch.manual_seed(0)
    model = Decoder(Config(context=16, width=16, layers=2, heads=2))
    ids = torch.arange(8)[None, :]
    logits, _ = model(ids)
    assert logits.shape == (1, 8, 256)
    altered = ids.clone()
    altered[:, 4:] += 20
    changed, _ = model(altered)
    assert torch.allclose(logits[:, :4], changed[:, :4], atol=1e-5, rtol=1e-5)
    check = cache_comparison(model, torch.device("cpu"), 8)
    assert check["max_logit_error"] < 1e-5
    batch_ids = torch.arange(16).reshape(2, 8)
    expected, _ = model(batch_ids)
    prefix, cached = model(batch_ids[:, :3])
    middle, cached = model(batch_ids[:, 3:5], cached)
    suffix, cached = model(batch_ids[:, 5:], cached)
    assert torch.allclose(expected, torch.cat([prefix, middle, suffix], dim=1), atol=1e-5, rtol=1e-5)
    loss = F.cross_entropy(logits.reshape(-1, 256), (ids + 1).reshape(-1))
    loss.backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    try:
        model(torch.zeros(1, 17, dtype=torch.long))
    except ValueError:
        pass
    else:
        raise AssertionError("context overflow was accepted")
    print("SMOKE decoder shapes, causality, cache, and gradients ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("smoke", "train", "evaluate", "generate", "cache"):
        mode.add_argument("--" + name, action="store_true")
    parser.add_argument("--text")
    parser.add_argument("--out")
    parser.add_argument("--resume")
    parser.add_argument("--checkpoint")
    parser.add_argument("--untrained", action="store_true", help="explicitly generate from a synthetic random model")
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--steps", type=int, default=40, help="additional updates, including on resume")
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--context", type=int, default=64)
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--max-eval-windows", type=int, default=32)
    parser.add_argument("--prompt", default="The ")
    parser.add_argument("--max-new-tokens", type=int, default=24)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=0)
    parser.add_argument("--tokens", type=int, default=16)
    args = parser.parse_args()
    if min(args.steps, args.batch, args.max_eval_windows) < 1 or args.lr <= 0:
        parser.error("steps, batch, eval windows, and learning rate must be positive")
    if args.max_new_tokens < 0 or args.temperature < 0 or not 0 <= args.top_k <= 256:
        parser.error("invalid generation settings")
    try:
        if args.smoke:
            smoke()
            return
        device = device_for(args.device)
        if args.train:
            train(args, device)
            return
        if args.cache and not args.checkpoint:
            torch.manual_seed(args.seed)
            model = Decoder(Config()).to(device)
            result(fixture="synthetic untrained model", **cache_comparison(model, device, args.tokens))
            return
        if args.generate and args.untrained:
            if args.checkpoint:
                raise ValueError("choose a checkpoint or --untrained, not both")
            torch.manual_seed(args.seed)
            model = Decoder(Config()).to(device)
            generate(args, model, device)
            return
        if not args.checkpoint:
            raise ValueError("this mode requires --checkpoint")
        model, state = load(args.checkpoint, device)
        if args.evaluate:
            if not args.text:
                raise ValueError("--evaluate requires --text")
            _, validation, identity = corpus(args.text, model.config.context)
            if identity != state["data"]:
                raise ValueError("evaluation data differs from checkpoint corpus identity")
            result(checkpoint=args.checkpoint, **evaluate(model, validation, device, args.max_eval_windows))
        elif args.generate:
            generate(args, model, device)
        elif args.cache:
            result(checkpoint=args.checkpoint, **cache_comparison(model, device, args.tokens))
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
