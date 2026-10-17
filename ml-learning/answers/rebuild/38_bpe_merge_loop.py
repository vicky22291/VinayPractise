"""Lab 38 rebuild: the BPE merge loop.

vocab_of(), encode() and decode() are given, as in the lab script. Write merge() and train()
from memory, then run from the module folder:
    python rebuild/38_bpe_merge_loop.py
check() compares merge() with Python's str.replace. It checks every pair train() picks against
numpy's pair counts. It round-trips 5 strings and times 256 merges on a 50 KB slice of TinyShakespeare.
It never compares with the lab's results.
"""
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

TEXT = Path(os.environ.get("ML_DATA", "~/ml-data")).expanduser() / "nanoGPT" / "data" / "shakespeare_char" / "input.txt"


def merge(ids, pair, new_id):
    """Replace each occurrence of pair (two adjacent ids) with new_id, scanning left to right. Returns a new list."""
    out, i = [], 0
    while i < len(ids):
        if i + 1 < len(ids) and ids[i] == pair[0] and ids[i + 1] == pair[1]:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


def train(text, num_merges):
    """Byte-level BPE on the whole text.

    Start from the UTF-8 bytes of text. Then num_merges times: count every adjacent pair with
    Counter(zip(ids, ids[1:])); take the most frequent with max(counts, key=counts.get); give it the
    next id (256, 257, ...); merge it everywhere in ids.
    Returns (merges, tokens): merges is {pair: new_id} in learned order, tokens is the token count of text.
    """
    ids = list(text.encode("utf-8"))
    merges = {}
    for k in range(num_merges):
        counts = Counter(zip(ids, ids[1:]))
        pair = max(counts, key=counts.get)
        merges[pair] = 256 + k
        ids = merge(ids, pair, 256 + k)
    return merges, len(ids)


def vocab_of(merges):  # given
    vocab = {i: bytes([i]) for i in range(256)}
    for (a, b), new_id in merges.items():
        vocab[new_id] = vocab[a] + vocab[b]
    return vocab


def encode(text, merges):  # given
    ids = list(text.encode("utf-8"))
    for pair, new_id in merges.items():
        ids = merge(ids, pair, new_id)
    return ids


def decode(ids, vocab):  # given
    return b"".join(vocab[i] for i in ids).decode("utf-8", errors="replace")


def as_str(ids):
    """One character per id (code point 0x100 + id), so Python's str.replace can stand in for merge()."""
    return "".join(chr(0x100 + i) for i in ids)


def check():
    """Compare with Python's str.replace and numpy's pair counts, on random lists and on 50 KB of TinyShakespeare."""
    rng = np.random.default_rng(0)
    for _ in range(300):  # short random lists over 3 ids, so runs such as 2, 2, 2 are common
        ids = rng.integers(0, 3, size=rng.integers(0, 12)).tolist()
        pair = tuple(rng.integers(0, 3, size=2).tolist())
        want = [ord(c) - 0x100 for c in as_str(ids).replace(as_str(pair), as_str([300]))]
        got = merge(ids, pair, 300)
        assert got == want, f"merge({ids}, {pair}, 300) gave {got}; str.replace gives {want}"

    if not TEXT.exists():
        sys.exit(f"missing {TEXT}: run python scripts/38_bpe_tokenizer.py --download first")
    text = TEXT.read_text(encoding="utf-8")[:50_000]
    t0 = time.process_time()
    merges, tokens = train(text, 256)
    seconds = time.process_time() - t0
    assert list(merges.values()) == list(range(256, 512)), "the new ids must be 256 to 511, in learned order"

    s = as_str(text.encode("utf-8"))
    for (a, b), new_id in merges.items():  # replay every merge with str.replace, counting pairs with numpy
        cp = np.frombuffer(s.encode("utf-32-le"), dtype="<u4").astype(np.int64)
        keys, counts = np.unique(cp[:-1] * 4096 + cp[1:], return_counts=True)
        mine = counts[keys == (0x100 + a) * 4096 + 0x100 + b]
        assert mine.size and mine[0] == counts.max(), \
            f"merge {new_id} took {(a, b)}, seen {mine.sum()} times; numpy's most frequent pair is seen {counts.max()} times"
        s = s.replace(as_str((a, b)), as_str([new_id]))
    assert tokens == len(s), f"train() counted {tokens} tokens; replaying its merges gives {len(s)}"

    vocab = vocab_of(merges)
    for t in ["To be, or not to be", "naïve café", "Thanks 👍", "Grüße aus Zürich", "東京で会いましょう"]:
        assert decode(encode(t, merges), vocab) == t, f"{t!r} does not round-trip"
    assert seconds < 2.0, f"train() took {seconds:.1f} CPU seconds for 256 merges on 50 KB; aim for under 2"
    print("check: PASS")


if __name__ == "__main__":
    check()
