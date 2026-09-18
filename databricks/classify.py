#!/usr/bin/env python3
"""Classify each harvested post as TECHNICAL or MARKETING with codex, keep only technical.

Second pass over what ``harvest.py`` produced. For every post in ``index.db`` the title,
subtitle, key takeaways and the first ~2,500 words of the body (Mermaid blocks stripped)
go to ``codex exec`` on stdin. The reply's first line is the verdict, the second a
one-sentence reason. Both are stored on the ``posts`` row, so a rerun only classifies
posts that have no verdict yet.

Marketing posts are MOVED to ``marketing/`` (not deleted) and ``index.md`` is rewritten to
list technical posts only. ``--undo`` moves everything back.

Usage:
    python3 databricks/classify.py                 # classify unclassified posts, then apply
    python3 databricks/classify.py --dry-run       # classify, print the split, move nothing
    python3 databricks/classify.py --limit 20
    python3 databricks/classify.py --force         # re-classify everything
    python3 databricks/classify.py --report        # print the current split from index.db
    python3 databricks/classify.py --undo          # move marketing posts back into posts/
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest import Index, RATE_LIMIT_MARKERS, HERE  # noqa: E402

logger = logging.getLogger("classify")

POSTS_DIR = HERE / "posts"
MARKETING_DIR = HERE / "marketing"

KIND_TECHNICAL = "TECHNICAL"
KIND_MARKETING = "MARKETING"

MAX_BODY_WORDS = 2500

PROMPT = """You are triaging posts from the Databricks engineering blog for a staff-engineer study
library. Decide whether this post teaches something technical or is marketing.

First line of your reply MUST be exactly one of:
  TECHNICAL  -- the post explains how something works: architecture, internals, algorithms,
                data structures, protocols, performance analysis with numbers, benchmarks with
                method, a tutorial with real code, a post-mortem, a design trade-off discussion.
                An announcement still counts as TECHNICAL if it explains the internals.
  MARKETING  -- the post exists to sell or promote: a product/feature announcement with no
                internals, a customer success story, an event or webinar recap or promo,
                a partnership or funding note, an awards post, a listicle, a "what's new"
                roundup, a survey or ebook teaser, a conference agenda.

Second line: one sentence saying why, naming the strongest signal.

Judge by the content of the post, not the title. Nothing else in the reply.

---
Title: {title}
Subtitle: {subtitle}
Categories: {categories}
Key takeaways: {takeaways}
Word count: {word_count}

Body (truncated):
{body}
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_columns(index: Index) -> None:
    cols = {r["name"] for r in index.conn.execute("PRAGMA table_info(posts)")}
    with index.lock:
        for col, typ in (("kind", "TEXT"), ("kind_reason", "TEXT"), ("kind_model", "TEXT"), ("kind_at", "TEXT")):
            if col not in cols:
                index.conn.execute(f"ALTER TABLE posts ADD COLUMN {col} {typ}")
        index.conn.commit()


def post_text(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    text = re.sub(r"```mermaid\n.*?\n```", "[diagram]", text, flags=re.S)
    text = re.sub(r"```text\n.*?\n```", "[diagram]", text, flags=re.S)
    text = re.sub(r"<sub>source image: [^<]*</sub>", "", text)
    words = text.split()
    if len(words) > MAX_BODY_WORDS:
        text = " ".join(words[:MAX_BODY_WORDS]) + " ..."
    return text


def build_prompt(row: sqlite3.Row, md_path: Path) -> str:
    takeaways = json.loads(row["summary"] or "[]")
    return PROMPT.format(
        title=row["title"],
        subtitle=row["subtitle"] or "",
        categories=", ".join(json.loads(row["categories"] or "[]")),
        takeaways=" | ".join(takeaways) if takeaways else "none",
        word_count=row["word_count"],
        body=post_text(md_path),
    )


class RateLimited(Exception):
    pass


def run_codex(prompt: str, *, model: str, effort: str, timeout: int, workdir: Path) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", dir=workdir, delete=False) as out:
        out_path = Path(out.name)
    cmd = [
        "codex", "exec", "--skip-git-repo-check", "-s", "read-only",
        "-c", f"model_reasoning_effort={effort}", "-o", str(out_path),
    ]
    if model:
        cmd += ["-m", model]
    cmd.append("-")  # prompt on stdin
    try:
        proc = subprocess.run(
            cmd, cwd=workdir, input=prompt, capture_output=True, text=True, timeout=timeout, check=False
        )
        if proc.returncode != 0:
            low = (proc.stderr or "").lower()
            if any(m in low for m in RATE_LIMIT_MARKERS):
                raise RateLimited(proc.stderr.strip()[-300:])
            raise RuntimeError(f"codex exit {proc.returncode}: {proc.stderr.strip()[-300:]}")
        return (out_path.read_text(encoding="utf-8") if out_path.exists() else proc.stdout).strip()
    finally:
        out_path.unlink(missing_ok=True)


def parse(raw: str) -> tuple[str, str]:
    lines = [ln.strip().strip("*` ") for ln in raw.splitlines() if ln.strip()]
    if not lines:
        raise ValueError("empty reply")
    head = lines[0].upper()
    if head.startswith(KIND_TECHNICAL):
        kind = KIND_TECHNICAL
    elif head.startswith(KIND_MARKETING):
        kind = KIND_MARKETING
    else:
        raise ValueError(f"unexpected first line: {lines[0][:80]!r}")
    reason = lines[1] if len(lines) > 1 else ""
    return kind, reason


def classify_all(index: Index, rows: list[sqlite3.Row], *, model: str, effort: str, timeout: int, workers: int) -> int:
    failures = 0
    with tempfile.TemporaryDirectory(prefix="databricks-classify-") as td:
        workdir = Path(td)

        def one(row: sqlite3.Row) -> tuple[str, str, str]:
            md_path = HERE / row["md_path"]
            if not md_path.exists():
                alt = MARKETING_DIR / md_path.name
                if not alt.exists():
                    raise FileNotFoundError(md_path)
                md_path = alt
            raw = run_codex(build_prompt(row, md_path), model=model, effort=effort, timeout=timeout, workdir=workdir)
            kind, reason = parse(raw)
            return row["slug"], kind, reason

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(one, r): r["slug"] for r in rows}
            for i, fut in enumerate(as_completed(futs), 1):
                slug = futs[fut]
                try:
                    slug, kind, reason = fut.result()
                except Exception as exc:  # noqa: BLE001  -- one bad post must not kill the pass
                    failures += 1
                    logger.error("[%d/%d] %s failed: %s", i, len(rows), slug, exc)
                    continue
                with index.lock:
                    index.conn.execute(
                        "UPDATE posts SET kind=?, kind_reason=?, kind_model=?, kind_at=? WHERE slug=?",
                        (kind, reason, model or "default", _now(), slug),
                    )
                    index.conn.commit()
                logger.info("[%d/%d] %-9s %s  (%s)", i, len(rows), kind, slug, reason[:90])
    return failures


def apply_split(index: Index, *, undo: bool = False) -> tuple[int, int]:
    """Move MARKETING posts to marketing/ (or back with undo). Returns (moved, kept)."""
    MARKETING_DIR.mkdir(exist_ok=True)
    moved = kept = 0
    with index.lock:
        rows = index.conn.execute("SELECT slug, kind, md_path FROM posts").fetchall()
    for r in rows:
        name = Path(r["md_path"]).name
        in_posts, in_mkt = POSTS_DIR / name, MARKETING_DIR / name
        want_mkt = (r["kind"] == KIND_MARKETING) and not undo
        if want_mkt and in_posts.exists():
            shutil.move(in_posts, in_mkt)
            moved += 1
        elif not want_mkt and in_mkt.exists():
            shutil.move(in_mkt, in_posts)
            moved += 1
        if not want_mkt:
            kept += 1
    return moved, kept


def write_indexes(index: Index) -> None:
    with index.lock:
        rows = index.conn.execute(
            "SELECT slug,title,published,image_count,arch_count,kind,kind_reason,md_path FROM posts ORDER BY published DESC"
        ).fetchall()
    tech = [r for r in rows if r["kind"] != KIND_MARKETING]
    mkt = [r for r in rows if r["kind"] == KIND_MARKETING]

    def table(items: list[sqlite3.Row], folder: str, with_reason: bool) -> list[str]:
        head = "| Published | Title | Images | Arch |" + (" Why |" if with_reason else "")
        sep = "|---|---|---|---|" + ("---|" if with_reason else "")
        out = [head, sep]
        for r in items:
            name = Path(r["md_path"]).name
            line = f"| {r['published'] or ''} | [{r['title']}]({folder}/{name}) | {r['image_count']} | {r['arch_count']} |"
            if with_reason:
                line += f" {(r['kind_reason'] or '').replace('|', '/')} |"
            out.append(line)
        return out

    (HERE / "index.md").write_text(
        "\n".join(
            [
                "# Databricks engineering blog harvest",
                "",
                f"Technical posts only ({len(tech)} of {len(rows)}). Marketing posts ({len(mkt)}) are listed in",
                "`marketing.md` and live under `marketing/`. Verdicts are in `index.db` (`posts.kind`).",
                "",
                *table(tech, "posts", False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (HERE / "marketing.md").write_text(
        "\n".join(
            [
                "# Marketing posts (excluded from the study index)",
                "",
                f"{len(mkt)} posts codex classified as MARKETING. Moved out of `posts/`; `classify.py --undo` restores them.",
                "",
                *table(mkt, "marketing", True),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def report(index: Index) -> None:
    with index.lock:
        rows = index.conn.execute("SELECT kind, count(*) n FROM posts GROUP BY kind").fetchall()
    for r in rows:
        print(f"{r['kind'] or 'unclassified':<13} {r['n']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--effort", default="low", choices=["minimal", "low", "medium", "high"])
    ap.add_argument("--max-workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="re-classify posts that already have a verdict")
    ap.add_argument("--dry-run", action="store_true", help="classify but do not move files or rewrite indexes")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--undo", action="store_true", help="move marketing posts back into posts/")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    index = Index(HERE / "index.db")
    ensure_columns(index)

    if args.report:
        report(index)
        return 0
    if args.undo:
        moved, _ = apply_split(index, undo=True)
        write_indexes(index)
        logger.info("moved %d posts back into posts/", moved)
        return 0

    if shutil.which("codex") is None:
        logger.error("`codex` not on PATH")
        return 2

    where = "" if args.force else "WHERE kind IS NULL"
    with index.lock:
        rows = index.conn.execute(f"SELECT * FROM posts {where} ORDER BY published DESC").fetchall()
    if args.limit is not None:
        rows = rows[: args.limit]
    logger.info("%d posts to classify (model=%s, effort=%s, workers=%d)", len(rows), args.model, args.effort, args.max_workers)

    failures = classify_all(index, rows, model=args.model, effort=args.effort, timeout=args.timeout, workers=args.max_workers) if rows else 0
    report(index)
    if args.dry_run:
        logger.info("dry run: nothing moved")
        return 1 if failures else 0
    moved, kept = apply_split(index)
    write_indexes(index)
    logger.info("moved %d, kept %d technical posts; %d classify failures", moved, kept, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
