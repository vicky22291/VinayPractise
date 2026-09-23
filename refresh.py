#!/usr/bin/env python3
"""Fetch whatever is new on the harvested engineering blogs and push it through the pipeline.

Every stage is already incremental on its own: `harvest.py` skips slugs that are in
`index.db`, `classify.py` only looks at posts with no verdict, `rank.py` only scores posts
with no score. This just runs them in the one order that works and reports what changed.

Order matters. `harvest.py` writes an `index.md` listing every post it knows about, and
`classify.py` rewrites that same file to list technical posts only, so classify has to run
second or the marketing posts reappear in the index.

    databricks:  harvest -> classify (technical vs marketing) -> rank (interview score)
    openai:      harvest

Usage:
    python3 refresh.py                      # both blogs, full chain
    python3 refresh.py --dry-run            # just say what is new, spend nothing
    python3 refresh.py --only openai
    python3 refresh.py --since 2026-01      # bound the catalog scan
    python3 refresh.py --retry-failed       # also re-try posts whose images failed before
    python3 refresh.py --no-validate-mermaid
"""

from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent


@dataclass
class Blog:
    name: str
    db: Path
    #: extra stages run after harvest, as (script, [args]) pairs
    stages: list[tuple[str, list[str]]]


BLOGS = {
    "databricks": Blog(
        name="databricks",
        db=HERE / "databricks" / "index.db",
        stages=[("databricks/classify.py", []), ("databricks/rank.py", [])],
    ),
    "openai": Blog(name="openai", db=HERE / "openai" / "index.db", stages=[]),
}


def counts(blog: Blog) -> dict[str, int]:
    """A small snapshot of the index, used to report the delta after a run."""
    if not blog.db.exists():
        return {}
    conn = sqlite3.connect(blog.db)
    conn.row_factory = sqlite3.Row
    out: dict[str, int] = {}
    try:
        row = conn.execute("SELECT count(*) p, coalesce(sum(arch_count),0) a FROM posts").fetchone()
        out["posts"], out["diagrams"] = row["p"], row["a"]
        for label, sql in (
            ("technical", "SELECT count(*) n FROM posts WHERE kind='TECHNICAL'"),
            ("marketing", "SELECT count(*) n FROM posts WHERE kind='MARKETING'"),
            ("scored", "SELECT count(*) n FROM interview"),
            ("failed images", "SELECT count(*) n FROM images WHERE verdict='FAILED'"),
        ):
            try:
                out[label] = conn.execute(sql).fetchone()["n"]
            except sqlite3.OperationalError:
                pass  # that table/column does not exist for this blog
    finally:
        conn.close()
    return out


def run(script: str, args: list[str]) -> int:
    cmd = [sys.executable, str(HERE / script), *args]
    print(f"\n$ {' '.join(cmd[1:])}", flush=True)
    return subprocess.run(cmd, cwd=HERE, check=False).returncode


def harvest_args(a: argparse.Namespace) -> list[str]:
    args: list[str] = []
    if a.since:
        args += ["--since", a.since]
    if a.limit is not None:
        args += ["--limit", str(a.limit)]
    if a.retry_failed:
        args.append("--retry-failed")
    if a.validate_mermaid:
        args.append("--validate-mermaid")
    if a.dry_run:
        args.append("--dry-run")
    return args


def report(name: str, before: dict[str, int], after: dict[str, int]) -> None:
    print(f"\n{name}:")
    if not after:
        print("  no index.db yet")
        return
    for key, now in after.items():
        was = before.get(key, 0)
        delta = now - was
        mark = f"  (+{delta})" if delta > 0 else f"  ({delta})" if delta < 0 else ""
        print(f"  {key:<14} {now}{mark}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", choices=sorted(BLOGS), action="append", default=[],
                    help="run one blog only (repeatable); default is all of them")
    ap.add_argument("--since", default=None, help="only posts published on/after this date (YYYY or YYYY-MM-DD)")
    ap.add_argument("--limit", type=int, default=None, help="max new posts per blog this run")
    ap.add_argument("--dry-run", action="store_true", help="list what is new and stop; nothing is fetched or scored")
    ap.add_argument("--retry-failed", action="store_true",
                    help="also re-process posts whose images failed before (some fail permanently: dead image hosts)")
    ap.add_argument("--no-validate-mermaid", dest="validate_mermaid", action="store_false",
                    help="skip rendering each new diagram with mermaid-cli")
    ap.set_defaults(validate_mermaid=True)
    a = ap.parse_args(argv)

    names = a.only or sorted(BLOGS)
    failures = 0
    before = {n: counts(BLOGS[n]) for n in names}

    for name in names:
        blog = BLOGS[name]
        print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
        rc = run(f"{name}/harvest.py", harvest_args(a))
        if rc >= 2:  # 2 = codex missing or a bad invocation; later stages cannot help
            print(f"{name}: harvest could not run (exit {rc}); skipping the rest of its chain")
            failures += 1
            continue
        failures += 1 if rc else 0
        if a.dry_run:
            continue
        for script, extra in blog.stages:
            rc = run(script, extra)
            failures += 1 if rc else 0

    if a.dry_run:
        print("\ndry run: nothing was fetched, annotated or scored")
        return 0

    print(f"\n{'=' * 70}\nsummary\n{'=' * 70}")
    for name in names:
        report(name, before[name], counts(BLOGS[name]))
    print(f"\n{failures} stage(s) reported failures" if failures else "\nall stages clean")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
