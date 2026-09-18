"""Score every TECHNICAL post for Staff/Principal interview value using the Codex CLI.

One ephemeral `codex exec` turn per post. The reply is a small key=value block:

    SCORE: 0-5
    TOPIC: one of TOPICS
    QUESTION: the interview question this post best prepares you for
    WHY: one sentence on what a staff candidate can steal from it
    NUMBERS: concrete figures worth quoting, or none

Results land in `interview` (index.db) and `staff-interview.md` (score >= 3, grouped by topic).

    python3 databricks/rank.py                # score unscored technical posts, write the guide
    python3 databricks/rank.py --min-score 4  # tighter guide
    python3 databricks/rank.py --write-only   # rebuild the markdown from the db
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sqlite3
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classify import HERE, POSTS_DIR, RateLimited, _now, post_text, run_codex  # noqa: E402
from harvest import Index  # noqa: E402

logger = logging.getLogger("rank")

TOPICS = [
    "distributed-storage",   # object storage, WAL, LSM, Delta/Iceberg internals, transactions
    "streaming",             # Kafka-style ingestion, exactly-once, watermarks, real-time mode
    "query-engine",          # optimizers, vectorization, Photon, caching, shuffles
    "sharding-scaling",      # sharding, autoscaling, partitioning, load balancing
    "reliability",           # HA, failover, incident response, chaos, feature flags, rate limits
    "control-plane",         # cluster managers, schedulers, config delivery, fleet management
    "ml-serving",            # inference platforms, feature stores, GPU scheduling, model serving
    "observability",         # metrics at scale, tracing, logging, debugging at scale
    "security-governance",   # auth, catalogs, lineage, PII, multi-tenancy isolation
    "data-modeling",         # schema evolution, file layout, compaction, indexing
    "not-interview",         # tutorials, API walkthroughs, product how-tos
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS interview (
    slug        TEXT PRIMARY KEY REFERENCES posts(slug),
    score       INTEGER NOT NULL,
    topic       TEXT NOT NULL,
    question    TEXT,
    why         TEXT,
    numbers     TEXT,
    model       TEXT,
    scored_at   TEXT
);
"""

PROMPT = """You are helping a senior engineer prepare for Staff / Principal Engineer system design
interviews. Read this Databricks engineering blog post and decide how useful it is as
interview material.

A post is interview-worthy when it describes a real system or a design decision at scale:
architecture with named components, why an alternative was rejected, a bottleneck and how
it was fixed, failure modes and blast radius, migration with rollback, consistency choices,
concrete numbers (QPS, latency, bytes, cost). Tutorials, API walkthroughs, release notes,
notebook how-tos and customer stories without internals score 0 or 1.

Scoring:
5  a full system design case study, could be an HLD interview question on its own
4  a deep dive into one component or decision, strong trade-off discussion
3  useful building block or war story, some transferable design insight
2  mostly product usage, one or two transferable ideas
1  tutorial or announcement, nothing a staff interviewer would probe
0  not technical enough to matter

Reply with exactly these five lines and nothing else:
SCORE: <0-5>
TOPIC: <one of: {topics}>
QUESTION: <the system design interview question this post best prepares you for, phrased as an interviewer would ask it, or none>
WHY: <one sentence, what a candidate can reuse from it>
NUMBERS: <comma separated concrete figures worth quoting, or none>

Title: {title}
Subtitle: {subtitle}
Key takeaways: {takeaways}
Word count: {word_count}

Post body:
{body}
"""


def ensure_schema(index: Index) -> None:
    with index.lock:
        index.conn.executescript(SCHEMA)
        index.conn.commit()


def build_prompt(row: sqlite3.Row, md_path: Path) -> str:
    takeaways = json.loads(row["summary"] or "[]")
    return PROMPT.format(
        topics=", ".join(TOPICS),
        title=row["title"],
        subtitle=row["subtitle"] or "",
        takeaways=" | ".join(takeaways) if takeaways else "none",
        word_count=row["word_count"],
        body=post_text(md_path),
    )


def parse(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for ln in raw.splitlines():
        ln = ln.strip().strip("*` ")
        if ":" not in ln:
            continue
        key, _, val = ln.partition(":")
        key = key.strip().upper()
        if key in ("SCORE", "TOPIC", "QUESTION", "WHY", "NUMBERS") and key not in out:
            out[key] = val.strip()
    if "SCORE" not in out or "TOPIC" not in out:
        raise ValueError(f"missing fields in: {raw[:120]!r}")
    score = int(out["SCORE"][0])
    if not 0 <= score <= 5:
        raise ValueError(f"score out of range: {out['SCORE']!r}")
    topic = out["TOPIC"].lower().strip("<> ")
    if topic not in TOPICS:
        # Model sometimes returns a near match; fall back to the closest known topic.
        topic = next((t for t in TOPICS if t in topic or topic in t), "not-interview")
    return {
        "score": score,
        "topic": topic,
        "question": out.get("QUESTION", ""),
        "why": out.get("WHY", ""),
        "numbers": out.get("NUMBERS", ""),
    }


def score_all(index: Index, rows: list[sqlite3.Row], *, model: str, effort: str, timeout: int, workers: int) -> int:
    failures = 0
    with tempfile.TemporaryDirectory(prefix="databricks-rank-") as td:
        workdir = Path(td)

        def one(row: sqlite3.Row) -> tuple[str, dict]:
            md_path = POSTS_DIR / Path(row["md_path"]).name
            if not md_path.exists():
                raise FileNotFoundError(md_path)
            for attempt in range(3):
                try:
                    raw = run_codex(build_prompt(row, md_path), model=model, effort=effort, timeout=timeout, workdir=workdir)
                    break
                except RateLimited as exc:
                    if attempt == 2:
                        raise
                    logger.warning("rate limited on %s, waiting 120s: %s", row["slug"], exc)
                    import time

                    time.sleep(120)
            return row["slug"], parse(raw)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(one, r): r["slug"] for r in rows}
            for i, fut in enumerate(as_completed(futs), 1):
                slug = futs[fut]
                try:
                    slug, res = fut.result()
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    logger.error("[%d/%d] %s failed: %s", i, len(rows), slug, exc)
                    continue
                with index.lock:
                    index.conn.execute(
                        "INSERT OR REPLACE INTO interview(slug,score,topic,question,why,numbers,model,scored_at) VALUES (?,?,?,?,?,?,?,?)",
                        (slug, res["score"], res["topic"], res["question"], res["why"], res["numbers"], model or "default", _now()),
                    )
                    index.conn.commit()
                logger.info("[%d/%d] %d %-18s %s", i, len(rows), res["score"], res["topic"], slug)
    return failures


def write_guide(index: Index, *, min_score: int) -> Path:
    with index.lock:
        rows = index.conn.execute(
            """SELECT p.slug, p.title, p.published, p.md_path, p.arch_count, i.score, i.topic, i.question, i.why, i.numbers
               FROM interview i JOIN posts p ON p.slug = i.slug
               WHERE i.score >= ? AND i.topic != 'not-interview'
               ORDER BY i.topic, i.score DESC, p.published DESC""",
            (min_score,),
        ).fetchall()
        total = index.conn.execute("SELECT count(*) FROM interview").fetchone()[0]
        hist = index.conn.execute("SELECT score, count(*) FROM interview GROUP BY score ORDER BY score DESC").fetchall()

    by_topic: dict[str, list[sqlite3.Row]] = {}
    for r in rows:
        by_topic.setdefault(r["topic"], []).append(r)

    lines = [
        "# Staff interview material from the Databricks engineering blog",
        "",
        f"{len(rows)} of {total} technical posts scored {min_score}+ by Codex (`rank.py`). Scores:",
        " ".join(f"{s}={n}" for s, n in hist) + ".",
        "Score 5 = a full HLD case study; 4 = one component or decision with real trade-offs;",
        "3 = a reusable building block or war story. Rebuild with `python3 databricks/rank.py --write-only`.",
        "",
        "Full verdicts: `sqlite3 databricks/index.db \"select score, topic, title from interview join posts using(slug) order by score desc\"`",
        "",
    ]
    for topic in TOPICS:
        items = by_topic.get(topic)
        if not items:
            continue
        lines += [f"## {topic} ({len(items)})", "", "| Score | Post | Interview question | What to reuse | Numbers |", "|---|---|---|---|---|"]
        for r in items:
            name = Path(r["md_path"]).name
            q = (r["question"] or "").replace("|", "/")
            why = (r["why"] or "").replace("|", "/")
            nums = (r["numbers"] or "").replace("|", "/")
            if nums.lower().strip(". ") == "none":
                nums = ""
            lines.append(f"| {r['score']} | [{r['title']}](posts/{name}) ({(r['published'] or '')[:4]}) | {q} | {why} | {nums} |")
        lines.append("")
    out = HERE / "staff-interview.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--effort", default="low", choices=["minimal", "low", "medium", "high"])
    ap.add_argument("--max-workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--min-score", type=int, default=3)
    ap.add_argument("--force", action="store_true", help="re-score posts that already have a verdict")
    ap.add_argument("--write-only", action="store_true", help="only rebuild staff-interview.md from the db")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    index = Index(HERE / "index.db")
    ensure_schema(index)

    failures = 0
    if not args.write_only:
        if shutil.which("codex") is None:
            logger.error("`codex` not on PATH")
            return 2
        where = "WHERE p.kind = 'TECHNICAL'" + ("" if args.force else " AND i.slug IS NULL")
        with index.lock:
            rows = index.conn.execute(
                f"SELECT p.* FROM posts p LEFT JOIN interview i ON i.slug = p.slug {where} ORDER BY p.published DESC"
            ).fetchall()
        if args.limit is not None:
            rows = rows[: args.limit]
        logger.info("%d posts to score (model=%s, effort=%s, workers=%d)", len(rows), args.model, args.effort, args.max_workers)
        if rows:
            failures = score_all(index, rows, model=args.model, effort=args.effort, timeout=args.timeout, workers=args.max_workers)

    out = write_guide(index, min_score=args.min_score)
    logger.info("wrote %s (%d failures)", out.relative_to(HERE.parent), failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
