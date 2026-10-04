"""Exercises 02 and 04: chunk the repo's concepts/*.md notes, embed, load into pgvector.

Chunking: split each file on markdown headings, then pack paragraphs into
chunks of about --size characters, carrying --overlap characters of the
previous chunk forward so a sentence cut at a boundary is still findable.

Run:  python ingest.py                         (table chunks, 1200 chars, 200 overlap)
      python ingest.py --table chunks_tiny --size 200 --overlap 0
      python ingest.py --table chunks_file --by-file         (one chunk per file: breaks)
"""
import argparse
import glob
import os
import re
import time

from llm import EMBED_MODEL, db, embed, vec

CORPUS = os.path.join(os.path.dirname(__file__), "../../../concepts/*.md")


def sections(text):
    """Yield (heading, body) per markdown heading. Drops mermaid styling lines."""
    text = re.sub(r"^\s*(classDef|class) .*$", "", text, flags=re.M)
    heading, buf = "(top)", []
    for line in text.splitlines():
        if re.match(r"^#{1,3} ", line):
            if buf:
                yield heading, "\n".join(buf)
            heading, buf = line.lstrip("# ").strip(), []
        else:
            buf.append(line)
    if buf:
        yield heading, "\n".join(buf)


def chunks(body, size, overlap):
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    paras = [p[i:i + size] for p in paras for i in range(0, len(p), size)]  # cut giant paragraphs
    cur = ""
    for p in paras:
        if cur and len(cur) + len(p) > size:
            yield cur
            cur = cur[-overlap:] if overlap else ""
        cur = (cur + "\n\n" + p).strip()
    if cur:
        yield cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default="chunks")
    ap.add_argument("--size", type=int, default=1200)
    ap.add_argument("--overlap", type=int, default=200)
    ap.add_argument("--model", default=EMBED_MODEL)
    ap.add_argument("--dim", type=int, default=768)
    ap.add_argument("--no-prefix", action="store_true", help="skip nomic task prefixes")
    ap.add_argument("--by-file", action="store_true", help="no chunking: one row per file")
    a = ap.parse_args()

    rows = []
    for path in sorted(glob.glob(CORPUS)):
        if a.by_file:
            rows.append((os.path.basename(path), "(whole file)", open(path).read()))
            continue
        for heading, body in sections(open(path).read()):
            for c in chunks(body, a.size, a.overlap):
                rows.append((os.path.basename(path), heading, c))

    conn = db()
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {a.table} (
        id        bigserial PRIMARY KEY,
        file      text NOT NULL,
        heading   text NOT NULL,
        body      text NOT NULL,
        embedding vector({a.dim}) NOT NULL,
        tsv       tsvector GENERATED ALWAYS AS
                  (to_tsvector('english', heading || ' ' || body)) STORED)""")
    conn.execute(f"TRUNCATE {a.table}")

    t0, batch = time.perf_counter(), 32
    for i in range(0, len(rows), batch):
        part = rows[i:i + batch]
        vecs = embed([f"{h}\n{b}" for _, h, b in part], "document",
                     prefix=not a.no_prefix, model=a.model)
        with conn.cursor() as cur:
            cur.executemany(
                f"INSERT INTO {a.table} (file, heading, body, embedding) VALUES (%s, %s, %s, %s::vector)",
                [(f, h, b, vec(v)) for (f, h, b), v in zip(part, vecs)])
        print(f"\r  embedded {min(i + batch, len(rows))}/{len(rows)}", end="", flush=True)
    secs = time.perf_counter() - t0

    conn.execute(f"CREATE INDEX IF NOT EXISTS {a.table}_hnsw ON {a.table} USING hnsw (embedding vector_cosine_ops)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS {a.table}_tsv ON {a.table} USING gin (tsv)")
    avg = sum(len(b) for _, _, b in rows) / max(len(rows), 1)
    print(f"\n{a.table}: {len(rows)} chunks from {len({r[0] for r in rows})} files, "
          f"avg {avg:.0f} chars, embedded in {secs:.1f}s ({len(rows) / secs:.0f} chunks/s)")


if __name__ == "__main__":
    main()
