"""Exercises 02 and 05: top-k retrieval three ways.

  vector  embed the question, ORDER BY cosine distance (HNSW index)
  text    Postgres full-text search: any question word, ranked by ts_rank_cd
  hybrid  both lists, fused with Reciprocal Rank Fusion: score = sum 1 / (60 + rank)

Run:  python search.py "how does raft pick a leader"
      python search.py "ef_search" --mode text
      python search.py "ef_search" --mode hybrid --k 5
"""
import argparse
import re
import time

from llm import db, embed, vec

VECTOR = """SELECT id, row_number() OVER (ORDER BY embedding <=> %(q)s::vector) AS r
            FROM {t} ORDER BY embedding <=> %(q)s::vector LIMIT %(n)s"""
TEXT = """SELECT id, row_number() OVER (ORDER BY ts_rank_cd(tsv, query) DESC) AS r
          FROM {t}, to_tsquery('english', %(tsq)s) query WHERE tsv @@ query
          ORDER BY ts_rank_cd(tsv, query) DESC LIMIT %(n)s"""
FUSE = """WITH v AS ({v}), t AS ({x})
          SELECT c.id, c.file, c.heading, c.body, v.r AS vrank, t.r AS trank,
                 1 - (c.embedding <=> %(q)s::vector) AS cos,
                 COALESCE(1.0 / (60 + v.r), 0) + COALESCE(1.0 / (60 + t.r), 0) AS score
          FROM v FULL JOIN t USING (id) JOIN {t} c USING (id)
          ORDER BY score DESC LIMIT %(k)s"""


def or_query(question):
    """'how does raft elect' -> 'how | does | raft | elect'. Postgres drops stop words."""
    words = re.findall(r"[A-Za-z0-9_]+", question)
    return " | ".join(words) or "nothing"


def retrieve(question, k=5, mode="vector", table="chunks", prefix=True, conn=None):
    """Return (rows, timings). Row: id, file, heading, body, vrank, trank, cos, score."""
    conn = conn or db()
    t0 = time.perf_counter()
    q = vec(embed([question], "query", prefix=prefix)[0]) if mode != "text" else None
    t1 = time.perf_counter()
    v = VECTOR.format(t=table) if mode != "text" else "SELECT NULL::bigint AS id, NULL::bigint AS r WHERE false"
    x = TEXT.format(t=table) if mode != "vector" else "SELECT NULL::bigint AS id, NULL::bigint AS r WHERE false"
    sql = FUSE.format(v=v, x=x, t=table)
    params = {"q": q, "tsq": or_query(question), "n": max(k, 20), "k": k}
    rows = conn.execute(sql, params).fetchall()
    t2 = time.perf_counter()
    return rows, {"embed_ms": (t1 - t0) * 1000, "search_ms": (t2 - t1) * 1000}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--mode", choices=["vector", "text", "hybrid"], default="vector")
    ap.add_argument("--table", default="chunks")
    ap.add_argument("--no-prefix", action="store_true")
    a = ap.parse_args()

    rows, t = retrieve(a.question, a.k, a.mode, a.table, prefix=not a.no_prefix)
    print(f"{'#':>2}  {'vec':>4} {'txt':>4}  {'cos':>5}  {'rrf':>6}  file :: heading")
    for i, (cid, file, heading, body, vr, tr, cos, score) in enumerate(rows, 1):
        cos = f"{cos:.3f}" if cos is not None else "-"
        print(f"{i:>2}  {vr or '-':>4} {tr or '-':>4}  {cos:>5}  {score:.4f}  {file} :: {heading[:55]}")
        print(f"      {body[:110].replace(chr(10), ' ')}...")
    print(f"embed {t['embed_ms']:.0f} ms, search {t['search_ms']:.0f} ms")


if __name__ == "__main__":
    main()
