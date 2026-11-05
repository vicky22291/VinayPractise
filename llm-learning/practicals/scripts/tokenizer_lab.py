#!/usr/bin/env python3
"""Small deterministic byte-pair tokenizer. Default input is synthetic text."""
import argparse
import json
from collections import Counter


def replace_pair(ids, pair, new_id):
    result, i = [], 0
    while i < len(ids):
        if i + 1 < len(ids) and (ids[i], ids[i + 1]) == pair:
            result.append(new_id)
            i += 2
        else:
            result.append(ids[i])
            i += 1
    return result


class ByteBPE:
    def __init__(self):
        self.vocab = {i: bytes([i]) for i in range(256)}
        self.merges = []

    def fit(self, texts, budget):
        if self.merges:
            raise ValueError("Create a fresh tokenizer for another fit")
        docs = [list(text.encode("utf-8")) for text in texts]
        for _ in range(budget):
            counts = Counter()
            for ids in docs:
                counts.update(zip(ids, ids[1:]))
            if not counts:
                break
            pair = min(counts, key=lambda p: (-counts[p], p))
            new_id = len(self.vocab)
            self.vocab[new_id] = self.vocab[pair[0]] + self.vocab[pair[1]]
            self.merges.append((pair, new_id))
            docs = [replace_pair(ids, pair, new_id) for ids in docs]
        return self

    def encode(self, text):
        ids = list(text.encode("utf-8"))
        for pair, new_id in self.merges:
            ids = replace_pair(ids, pair, new_id)
        return ids

    def decode(self, ids):
        return b"".join(self.vocab[i] for i in ids).decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--text", default="a small cat and a small dog")
    parser.add_argument("--merges", type=int, default=8)
    args = parser.parse_args()
    if args.merges < 0:
        parser.error("--merges must be nonnegative")
    if args.smoke:
        for text in ["", "abab", "hello 世界 👋", "aaaaa"]:
            tok = ByteBPE().fit([text], 12)
            assert tok.decode(tok.encode(text)) == text
            assert tok.decode(tok.encode(text + " café")) == text + " café"
        a = ByteBPE().fit(["abac"], 4)
        b = ByteBPE().fit(["abac"], 4)
        assert a.merges == b.merges
        assert replace_pair([1, 1, 1], (1, 1), 256) == [256, 1]
        print("SMOKE tokenizer ok")
        return
    tok = ByteBPE().fit([args.text], args.merges)
    ids = tok.encode(args.text)
    print("RESULT " + json.dumps({
        "fixture": "synthetic or learner-supplied text", "characters": len(args.text),
        "bytes": len(args.text.encode()), "tokens": len(ids), "vocab": len(tok.vocab),
        "ids": ids, "round_trip": tok.decode(ids) == args.text,
        "merges": [{"pair": pair, "id": i} for pair, i in tok.merges],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
