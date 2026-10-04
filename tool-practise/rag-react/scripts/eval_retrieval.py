"""Exercises 04 and 05: measure retrieval before touching the prompt.

golden.jsonl holds questions with the answer we expect to find. A retrieved
chunk is a HIT when it comes from the expected file ("*" = any file) and its
text contains the needle. For each question we record the rank of the first hit.

  recall@k  share of questions with a hit in the top k
  MRR       mean of 1 / rank of the first hit (0 if none). 1.0 = always first.

Run:  python eval_retrieval.py                          (table chunks, vector)
      python eval_retrieval.py --mode hybrid
      python eval_retrieval.py --table chunks_tiny
      python eval_retrieval.py --no-prefix              (query without 'search_query: ')
"""
import argparse
import json
import os
import statistics

from llm import db
from search import retrieve

GOLDEN = os.path.join(os.path.dirname(__file__), "golden.jsonl")


def first_hit(rows, g):
    for rank, r in enumerate(rows, 1):
        file_ok = g["file"] == "*" or r[1] == g["file"]
        if file_ok and g["needle"].lower() in (r[2] + " " + r[3]).lower():
            return rank
    return None


def summarise(label, ranks):
    n = len(ranks)
    rec = {k: sum(1 for r in ranks if r and r <= k) / n for k in (1, 5, 10)}
    mrr = sum(1 / r for r in ranks if r) / n
    print(f"{label:<9} n={n:<3} recall@1 {rec[1]:.2f}  recall@5 {rec[5]:.2f}  "
          f"recall@10 {rec[10]:.2f}  MRR {mrr:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default="chunks")
    ap.add_argument("--mode", choices=["vector", "text", "hybrid"], default="vector")
    ap.add_argument("--no-prefix", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    a = ap.parse_args()

    golden = [json.loads(line) for line in open(GOLDEN) if line.strip()]
    conn, by_kind, lat = db(), {}, []
    for g in golden:
        rows, t = retrieve(g["q"], 10, a.mode, a.table, prefix=not a.no_prefix, conn=conn)
        rank = first_hit(rows, g)
        by_kind.setdefault(g["kind"], []).append(rank)
        lat.append(t["embed_ms"] + t["search_ms"])
        if not a.quiet:
            top = f"{rows[0][1]} :: {rows[0][2][:35]}" if rows else "(no rows)"
            print(f"{rank or 'MISS':>4}  {g['q'][:58]:<58}  top1: {top}")

    print(f"\n{a.table} / {a.mode} / prefix={'off' if a.no_prefix else 'on'}")
    for kind, ranks in by_kind.items():
        summarise(kind, ranks)
    summarise("all", [r for ranks in by_kind.values() for r in ranks])
    print(f"latency p50 {statistics.median(lat):.0f} ms, max {max(lat):.0f} ms per query")


if __name__ == "__main__":
    main()
