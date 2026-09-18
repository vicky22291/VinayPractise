#!/usr/bin/env python3
"""Harvest Databricks engineering blog posts into markdown, with images turned into text.

Pipeline per post (stdlib only, no third-party deps):

    listing page  ->  post HTML  ->  markdown (images as placeholders)
                                 ->  download images to a temp dir
                                 ->  codex exec -i <image>  (ARCHITECTURE | IGNORE)
                                 ->  splice codex text + mermaid into the markdown
                                 ->  delete the image files
                                 ->  posts/<slug>.md  +  rows in index.db

Inspired by CodexAnnotator in VQTS-Python (doc_pipeline/annotation/image_annotator.py):
one ephemeral codex turn per image, first line of the reply is the verdict, everything
after it is the extracted content, and results are cached by image MD5 so a rerun never
re-spends quota on bytes it has already seen. This version shells out to ``codex exec``
instead of driving ``codex app-server`` over JSON-RPC, which keeps it a single file.

Usage:
    python3 databricks/harvest.py                 # every post in the listing (827), annotate, write md
    python3 databricks/harvest.py --since 2026 --limit 5
    python3 databricks/harvest.py --skip-codex    # markdown only, images left as placeholders
    python3 databricks/harvest.py --force SLUG    # redo one post
    python3 databricks/harvest.py --list          # print what is in index.db
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

logger = logging.getLogger("harvest")

HERE = Path(__file__).resolve().parent
BASE = "https://www.databricks.com"
DEFAULT_LISTING = (
    BASE + "/blog/category/engineering?categories="
    "engineering%2Copen-source%2Cdata-engineering%2Cdata-science-machine-learning"
    "%2Cdata-warehousing%2Cdata-streaming%2Ctutorials%2Csolution-accelerators"
)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X) blog-harvest/1.0"

VERDICT_ARCH = "ARCHITECTURE"
VERDICT_IGNORE = "IGNORE"

# Same classDefs as templates/color-legend.md so harvested diagrams match the rest of the repo.
COLOR_LEGEND = """classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
classDef queue    fill:#cffafe,stroke:#0891b2,stroke-width:2px,color:#111
classDef critical fill:#fee2e2,stroke:#dc2626,stroke-width:4px,color:#111
classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
classDef decision fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111"""

# First line = verdict (mirrors the INFORMATIONAL / NON_INFORMATIONAL contract in CodexAnnotator).
# Everything after is spliced into the markdown verbatim, so the prompt dictates the final shape.
PROMPT_TEMPLATE = """You are looking at ONE image from a Databricks engineering blog post.

Post title: {title}
{context_block}Instructions:
1. The first line of your response MUST be exactly one of:
   ARCHITECTURE  -- the image shows a system/architecture diagram, data flow, component layout,
                    sequence of calls, state machine, storage layout, or a chart/table/benchmark
                    with technical numbers (latency, throughput, cost, scale).
   IGNORE        -- the image is a logo, stock photo, marketing banner, a UI screenshot with no
                    architectural information, a person, or decoration.

2. If IGNORE, stop after the first line.

3. If ARCHITECTURE, output these sections in this exact order:

**Summary:** one sentence stating what the diagram shows.

**Components:** a bullet per box/label naming the component and the technology it uses.

**Flows:** a bullet per arrow: `A -> B: what flows` (write, async event, WAL, cache miss, ...).

**Numbers:** every number, unit, percentage or size visible. Write `none` if there are none.

Then a Mermaid diagram that reproduces the image. Rules for the diagram:
- Use `flowchart LR` (or `flowchart TD`, `sequenceDiagram`, `stateDiagram-v2` if that fits better).
- For flowcharts: keep it under 15 nodes, label every arrow, and put this legend at the bottom,
  then assign every node a class with `class A,B service` style lines:
{legend}
  client = clients/edge/gateway/LB, service = stateless compute, store = databases/durable storage,
  cache = Redis/CDN/anything losable, queue = Kafka/streams/async pipes, critical = the bottleneck
  or SPOF (use sparingly), external = third-party, decision = a trade-off point.
- Node text must not contain parentheses, brackets, quotes or semicolons. Use plain words.
- Start the diagram with a `%% comment` line saying what it shows.
- Wrap it in a ```mermaid fenced block.

Hard rules:
- Do NOT describe the image type ("This is a diagram of...").
- Do NOT invent components, arrows or numbers that are not visible.
- Do not use em dashes anywhere. Use a plain hyphen or a new sentence.
- Use the attached image, not your memory, as the only source."""

# Cheap pre-filter. Anything matching is not worth a codex call.
SKIP_SRC_PATTERNS = re.compile(r"(logo|icon|avatar|headshot|author|badge|/themes/|\.svg($|\?)|\.gif($|\?))", re.I)
MIN_IMAGE_PX = 150

# Stderr fragments that mean "quota", so we sleep instead of failing the image.
RATE_LIMIT_MARKERS = ("rate limit", "usage limit", "usage_limit", "429", "quota", "too many requests")


# --------------------------------------------------------------------------- HTTP


def fetch(url: str, *, binary: bool = False, retries: int = 3) -> bytes | str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if binary:
                return data
            # A stray NUL in a post body (seen in the wild) makes subprocess reject the prompt
            # with "embedded null byte"; it carries no content, so drop it at the door.
            return data.decode("utf-8", errors="replace").replace("\x00", "")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            logger.warning("fetch %s failed (attempt %d/%d): %s", url, attempt, retries, exc)
            time.sleep(2 * attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


# --------------------------------------------------------------------------- catalog

# The blog's filter UI does not paginate server-side. It loads one JSON file with every
# post in the top-level category (827 for engineering, 2013 to today) and filters
# client-side on the `categories=` query param. We do the same.
CATALOG_URL = BASE + "/en-blog-assets/data/blog/posts/{category}.json"


@dataclass
class PostMeta:
    slug: str
    title: str
    subtitle: str
    published: str  # ISO date, YYYY-MM-DD
    authors: list[str]
    categories: list[str]
    word_count: int

    @property
    def url(self) -> str:
        return f"{BASE}/blog/{self.slug}"


def load_catalog(listing_url: str) -> list[PostMeta]:
    """Every post the listing URL would show, newest first."""
    parsed = urllib.parse.urlparse(listing_url)
    m = re.search(r"/blog/category/([^/]+)", parsed.path)
    category = m.group(1) if m else "engineering"
    wanted = set(filter(None, urllib.parse.parse_qs(parsed.query).get("categories", [""])[0].split(",")))
    raw = json.loads(fetch(CATALOG_URL.format(category=category)))
    posts: list[PostMeta] = []
    for it in raw:
        cats = [c["entity"]["fieldSlug"] for c in it.get("fieldCategories") or [] if c.get("entity")]
        if wanted and not (wanted & set(cats)):
            continue
        path = (it.get("entityUrl") or {}).get("path", "")
        if not path.startswith("/blog/"):
            continue
        posts.append(
            PostMeta(
                slug=path.removeprefix("/blog/").strip("/"),
                title=html.unescape(it.get("title") or ""),
                subtitle=html.unescape(it.get("fieldSubtitle") or ""),
                published=(it.get("isoDate") or "")[:10],
                authors=[a["entity"]["name"] for a in it.get("fieldAuthors") or [] if a.get("entity")],
                categories=cats,
                word_count=int(it.get("bodyWordCount") or 0),
            )
        )
    posts.sort(key=lambda p: p.published, reverse=True)
    logger.info("catalog %s: %d posts in category, %d after filter", category, len(raw), len(posts))
    return posts


# --------------------------------------------------------------------------- HTML -> markdown


@dataclass
class ImageRef:
    index: int
    src: str
    alt: str
    width: int | None
    height: int | None
    caption: str = ""

    @property
    def placeholder(self) -> str:
        return f"{{{{IMG:{self.index}}}}}"


@dataclass
class ParsedPost:
    slug: str
    url: str
    title: str
    subtitle: str
    published: str
    authors: list[str]
    categories: list[str]
    word_count: int
    summary: list[str]
    markdown: str
    images: list[ImageRef] = field(default_factory=list)


class BodyToMarkdown(HTMLParser):
    """Convert the ``article--content`` div of a Databricks post into markdown.

    Images become ``{{IMG:n}}`` placeholders on their own line so a later pass can
    swap in the codex annotation. Deliberately small: headings, paragraphs, lists,
    links, emphasis, code, tables, blockquotes and figures cover every post seen.
    """

    BODY_CLASS = "article--content"

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.images: list[ImageRef] = []
        self._capturing = False
        self._depth = 0  # div nesting depth inside the body container
        self._list_stack: list[tuple[str, int]] = []  # (ul|ol, counter)
        self._in_pre = False
        self._in_code = False
        self._href: str | None = None
        self._link_text: list[str] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._skip_depth = 0  # inside <script>/<style>/<noscript>
        self._pending_caption_for: ImageRef | None = None
        self._in_figcaption = False

    # -- helpers
    def _emit(self, text: str) -> None:
        if self._cell is not None:
            self._cell.append(text)
        elif self._href is not None:
            self._link_text.append(text)
        else:
            self.out.append(text)

    def _newline(self, n: int = 2) -> None:
        if self._cell is not None:
            return
        joined = "".join(self.out)
        trailing = len(joined) - len(joined.rstrip("\n"))
        if trailing < n:
            self.out.append("\n" * (n - trailing))

    # -- parser callbacks
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if not self._capturing:
            if tag == "div" and self.BODY_CLASS in a.get("class", ""):
                self._capturing = True
                self._depth = 1
            return
        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "div":
            self._depth += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newline()
            self._emit("#" * int(tag[1]) + " ")
        elif tag == "p":
            self._newline()
        elif tag == "br":
            self._emit("\n")
        elif tag in ("ul", "ol"):
            self._newline(1 if self._list_stack else 2)
            self._list_stack.append((tag, 0))
        elif tag == "li":
            if not self._list_stack:
                self._list_stack.append(("ul", 0))
            kind, n = self._list_stack[-1]
            self._list_stack[-1] = (kind, n + 1)
            self._newline(1)
            indent = "  " * (len(self._list_stack) - 1)
            self._emit(f"{indent}{n + 1}. " if kind == "ol" else f"{indent}- ")
        elif tag == "pre":
            self._newline()
            self._in_pre = True
            self._emit("```\n")
        elif tag == "code":
            if not self._in_pre:
                self._in_code = True
                self._emit("`")
        elif tag == "a":
            self._href = a.get("href") or None
            self._link_text = []
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "blockquote":
            self._newline()
            self._emit("> ")
        elif tag == "img":
            src = a.get("src", "")
            if src.startswith("/"):
                src = BASE + src
            if not src or src.startswith("data:"):
                return
            ref = ImageRef(
                index=len(self.images) + 1,
                src=src,
                alt=a.get("alt", "").strip(),
                width=_int_or_none(a.get("width")),
                height=_int_or_none(a.get("height")),
            )
            self.images.append(ref)
            self._pending_caption_for = ref
            self._newline()
            self.out.append(ref.placeholder)
            self._newline()
        elif tag == "figcaption":
            self._in_figcaption = True
        elif tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "hr":
            self._newline()
            self._emit("---")
            self._newline()

    def handle_endtag(self, tag: str) -> None:
        if not self._capturing:
            return
        if tag in ("script", "style", "noscript"):
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag == "div":
            self._depth -= 1
            if self._depth == 0:
                self._capturing = False
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote"):
            self._newline()
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._newline(1 if self._list_stack else 2)
        elif tag == "li":
            self._newline(1)
        elif tag == "pre":
            self._in_pre = False
            self._newline(1)
            self._emit("```")
            self._newline()
        elif tag == "code":
            if self._in_code:
                self._in_code = False
                self._emit("`")
        elif tag == "a":
            text = "".join(self._link_text).strip()
            href = self._href
            self._href = None
            self._link_text = []
            if text:
                if href and not href.startswith("#"):
                    if href.startswith("/"):
                        href = BASE + href
                    self._emit(f"[{text}]({href})")
                else:
                    self._emit(text)
        elif tag in ("strong", "b"):
            self._emit("**")
        elif tag in ("em", "i"):
            self._emit("*")
        elif tag == "figcaption":
            self._in_figcaption = False
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            rows = [r for r in self._table if r]
            self._table = None
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                self._newline()
                self.out.append("| " + " | ".join(rows[0]) + " |\n")
                self.out.append("|" + "---|" * width + "\n")
                for r in rows[1:]:
                    self.out.append("| " + " | ".join(r) + " |\n")
                self._newline()

    def handle_data(self, data: str) -> None:
        if not self._capturing or self._skip_depth:
            return
        if self._in_figcaption and self._pending_caption_for is not None:
            self._pending_caption_for.caption += data
        if self._in_pre:
            self._emit(data)
            return
        text = re.sub(r"[ \t\r\n]+", " ", data)
        if not text:
            return
        # Drop whitespace-only runs at the start of a block.
        if text == " " and (not self.out or self.out[-1].endswith("\n")):
            return
        self._emit(text)

    def markdown(self) -> str:
        text = "".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"^#{1,6}\s*$", "", text, flags=re.M)  # empty headings in the source
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def file_stem(slug: str) -> str:
    """Filesystem-safe name for a post. Legacy posts have slugs like ``2023/04/20/foo.html``."""
    stem = re.sub(r"\.html?$", "", slug).strip("/").replace("/", "-")
    return re.sub(r"[^A-Za-z0-9._-]+", "-", stem)


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _meta(page: str, pattern: str) -> str:
    m = re.search(pattern, page, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def parse_post(slug: str, page: str, meta: PostMeta | None = None) -> ParsedPost:
    """Body comes from the HTML; metadata from the catalog when we have it, else scraped."""
    url = f"{BASE}/blog/{slug}"
    if meta is not None:
        title, subtitle, published = meta.title, meta.subtitle, meta.published
        authors, categories, word_count = meta.authors, meta.categories, meta.word_count
    else:
        title = _meta(page, r'"og:title" content="([^"]+)"') or _meta(page, r"<h1[^>]*>(.*?)</h1>")
        title = re.sub(r"<[^>]+>", "", title)
        subtitle = ""
        published = _to_iso_date(_meta(page, r"<time[^>]*>([^<]+)</time>"))
        authors = [_slug_to_name(a) for a in dict.fromkeys(re.findall(r'/blog/author/([^"?#/]+)"', page))]
        categories = list(dict.fromkeys(re.findall(r'/blog/category/([^"?#/]+)"', page)))
        word_count = 0

    conv = BodyToMarkdown()
    conv.feed(page)
    conv.close()
    markdown = conv.markdown()
    return ParsedPost(
        slug=slug,
        url=url,
        title=title,
        subtitle=subtitle,
        published=published,
        authors=authors,
        categories=categories,
        word_count=word_count or len(markdown.split()),
        summary=_summary(page),
        markdown=markdown,
        images=conv.images,
    )


def _summary(page: str) -> list[str]:
    """The post's key-takeaway bullets (a <ul> inside the ``text-blog-summary`` div)."""
    m = re.search(r'<div class="[^"]*text-blog-summary[^"]*">(.*?)</div>', page, re.S)
    if not m:
        return []
    items = re.findall(r"<li[^>]*>(.*?)</li>", m.group(1), re.S)
    if not items:
        items = [m.group(1)]
    return [" ".join(html.unescape(re.sub(r"<[^>]+>", "", it)).split()) for it in items if it.strip()]


def _to_iso_date(text: str) -> str:
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def _slug_to_name(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.split("-"))


# --------------------------------------------------------------------------- sqlite index


SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    slug        TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT NOT NULL,
    subtitle    TEXT,
    published   TEXT,           -- ISO date
    authors     TEXT,           -- JSON list
    categories  TEXT,           -- JSON list
    summary     TEXT,           -- JSON list of key-takeaway bullets
    word_count  INTEGER DEFAULT 0,
    md_path     TEXT,
    image_count INTEGER DEFAULT 0,
    arch_count  INTEGER DEFAULT 0,
    annotated   INTEGER DEFAULT 0,  -- 0 = --skip-codex run, images still owed
    fetched_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS images (
    md5          TEXT PRIMARY KEY,
    src_url      TEXT NOT NULL,
    first_slug   TEXT NOT NULL,
    verdict      TEXT NOT NULL,  -- ARCHITECTURE | IGNORE | SKIPPED | FAILED
    body         TEXT,           -- codex text incl. mermaid (ARCHITECTURE only)
    reason       TEXT,           -- why SKIPPED / FAILED
    annotator    TEXT,           -- codex | prefilter
    model        TEXT,
    annotated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS post_images (
    slug     TEXT NOT NULL,
    position INTEGER NOT NULL,
    md5      TEXT,
    src_url  TEXT NOT NULL,
    PRIMARY KEY (slug, position)
);
"""


class Index:
    """Thin sqlite wrapper. One connection, guarded by a lock (annotations arrive from threads)."""

    def __init__(self, path: Path) -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.lock = threading.Lock()

    def has_post(self, slug: str, *, need_annotated: bool) -> bool:
        """True when the post is done for this run's purpose (annotated if codex is on)."""
        with self.lock:
            row = self.conn.execute("SELECT annotated FROM posts WHERE slug=?", (slug,)).fetchone()
        return row is not None and (bool(row["annotated"]) or not need_annotated)

    def upsert_post(
        self, post: ParsedPost, md_path: Path, image_count: int, arch_count: int, annotated: bool
    ) -> None:
        with self.lock:
            self.conn.execute(
                """INSERT INTO posts (slug,url,title,subtitle,published,authors,categories,summary,
                                      word_count,md_path,image_count,arch_count,annotated,fetched_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(slug) DO UPDATE SET url=excluded.url, title=excluded.title,
                     subtitle=excluded.subtitle, published=excluded.published,
                     authors=excluded.authors, categories=excluded.categories,
                     summary=excluded.summary, word_count=excluded.word_count,
                     md_path=excluded.md_path, image_count=excluded.image_count,
                     arch_count=excluded.arch_count, annotated=excluded.annotated,
                     fetched_at=excluded.fetched_at""",
                (
                    post.slug,
                    post.url,
                    post.title,
                    post.subtitle,
                    post.published,
                    json.dumps(post.authors),
                    json.dumps(post.categories),
                    json.dumps(post.summary),
                    post.word_count,
                    str(md_path.relative_to(HERE)),
                    image_count,
                    arch_count,
                    int(annotated),
                    _now(),
                ),
            )
            self.conn.commit()

    def get_image(self, md5: str) -> sqlite3.Row | None:
        with self.lock:
            return self.conn.execute("SELECT * FROM images WHERE md5=?", (md5,)).fetchone()

    def record_image(
        self, md5: str, src: str, slug: str, verdict: str, body: str, reason: str, annotator: str, model: str
    ) -> None:
        with self.lock:
            self.conn.execute(
                """INSERT INTO images (md5,src_url,first_slug,verdict,body,reason,annotator,model,annotated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(md5) DO UPDATE SET verdict=excluded.verdict, body=excluded.body,
                     reason=excluded.reason, annotator=excluded.annotator, model=excluded.model,
                     annotated_at=excluded.annotated_at""",
                (md5, src, slug, verdict, body, reason, annotator, model, _now()),
            )
            self.conn.commit()

    def link_post_image(self, slug: str, position: int, md5: str | None, src: str) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO post_images (slug,position,md5,src_url) VALUES (?,?,?,?)",
                (slug, position, md5, src),
            )
            self.conn.commit()

    def list_posts(self) -> list[sqlite3.Row]:
        with self.lock:
            return self.conn.execute(
                "SELECT slug,title,published,image_count,arch_count,annotated,md_path FROM posts ORDER BY published DESC"
            ).fetchall()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- codex


class CodexRateLimited(Exception):
    pass


@dataclass
class Annotation:
    verdict: str
    body: str = ""
    reason: str = ""
    annotator: str = "codex"


class CodexImageAnnotator:
    """One ``codex exec -i <image>`` per image, retried on rate limit, cached by MD5 in sqlite."""

    def __init__(
        self,
        index: Index,
        *,
        model: str = "",
        reasoning_effort: str = "low",
        timeout_seconds: int = 240,
        max_workers: int = 3,
        context_chars: int = 400,
        rate_limit_attempts: int = 3,
        rate_limit_wait: int = 120,
        validate_mermaid: bool = False,
    ) -> None:
        self.index = index
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self.max_workers = max_workers
        self.context_chars = context_chars
        self.rate_limit_attempts = rate_limit_attempts
        self.rate_limit_wait = rate_limit_wait
        self.mmdc_cmd: list[str] = []
        if validate_mermaid:
            if shutil.which("mmdc"):
                self.mmdc_cmd = ["mmdc"]
            elif shutil.which("npx"):
                self.mmdc_cmd = ["npx", "-y", "@mermaid-js/mermaid-cli"]
            else:
                logger.warning("--validate-mermaid: neither `mmdc` nor `npx` on PATH; skipping validation")
        self.validate_mermaid = bool(self.mmdc_cmd)

    @staticmethod
    def is_available() -> bool:
        return shutil.which("codex") is not None

    # -- prefilter
    @staticmethod
    def prefilter(ref: ImageRef) -> str | None:
        """Return a skip reason for images that are obviously not diagrams, else None."""
        if SKIP_SRC_PATTERNS.search(ref.src):
            return "src looks like logo/icon/svg/gif"
        if ref.width is not None and ref.height is not None and (ref.width < MIN_IMAGE_PX or ref.height < MIN_IMAGE_PX):
            return f"too small ({ref.width}x{ref.height})"
        return None

    # -- one image
    def annotate(self, post: ParsedPost, ref: ImageRef, image_path: Path, workdir: Path) -> Annotation:
        prompt = PROMPT_TEMPLATE.format(
            title=post.title,
            context_block=self._context_block(post, ref),
            legend=_indent(COLOR_LEGEND, "  "),
        )
        last_reason = ""
        for attempt in range(1, self.rate_limit_attempts + 1):
            try:
                raw = self._run_codex(prompt, image_path, workdir)
                return self._parse(raw)
            except CodexRateLimited as exc:
                last_reason = str(exc)
                if attempt == self.rate_limit_attempts:
                    break
                logger.warning(
                    "codex rate-limited on %s (attempt %d/%d); sleeping %ds",
                    image_path.name, attempt, self.rate_limit_attempts, self.rate_limit_wait,
                )
                time.sleep(self.rate_limit_wait)
            except subprocess.TimeoutExpired:
                return Annotation("FAILED", reason=f"codex timed out after {self.timeout_seconds}s")
            except RuntimeError as exc:
                return Annotation("FAILED", reason=str(exc))
        return Annotation("FAILED", reason=f"rate-limited: {last_reason}")

    def _run_codex(self, prompt: str, image_path: Path, workdir: Path) -> str:
        out_file = workdir / f"{image_path.stem}.codex.txt"
        cmd = [
            "codex", "exec",
            "--skip-git-repo-check",
            "-s", "read-only",
            "-c", f"model_reasoning_effort={self.reasoning_effort}",
            "-i", str(image_path),
            "-o", str(out_file),
        ]
        if self.model:
            cmd += ["-m", self.model]
        cmd.append(prompt)
        # stdin MUST be closed: `codex exec` appends piped stdin to the prompt and blocks until
        # EOF, so an inherited pipe (cron, an IDE, another tool) hangs every call to the timeout.
        proc = subprocess.run(
            cmd, cwd=workdir, stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=self.timeout_seconds, check=False,
        )
        stderr = proc.stderr or ""
        if proc.returncode != 0:
            low = stderr.lower()
            if any(marker in low for marker in RATE_LIMIT_MARKERS):
                raise CodexRateLimited(stderr.strip()[-300:])
            raise RuntimeError(f"codex exit {proc.returncode}: {stderr.strip()[-300:]}")
        text = out_file.read_text(encoding="utf-8") if out_file.exists() else proc.stdout
        return text.strip()

    def _parse(self, raw: str) -> Annotation:
        if not raw:
            return Annotation("FAILED", reason="empty codex reply")
        first, _, rest = raw.partition("\n")
        verdict = first.strip().strip("*` ").upper()
        if verdict.startswith(VERDICT_IGNORE):
            return Annotation(VERDICT_IGNORE)
        if not verdict.startswith(VERDICT_ARCH):
            return Annotation("FAILED", reason=f"unexpected first line: {first[:80]!r}")
        body = rest.strip().replace("—", " - ").replace("–", "-")
        if self.validate_mermaid:
            body = self._validate_mermaid_blocks(body)
        return Annotation(VERDICT_ARCH, body=body)

    def _validate_mermaid_blocks(self, body: str) -> str:
        """Render every mermaid block with mmdc; downgrade a broken block to a plain fence."""

        def check(match: re.Match[str]) -> str:
            code = match.group(1)
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "d.mmd"
                src.write_text(code, encoding="utf-8")
                proc = subprocess.run(
                    [*self.mmdc_cmd, "-i", str(src), "-o", str(Path(td) / "d.svg"), "-q"],
                    stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120, check=False,
                )
            if proc.returncode == 0:
                return match.group(0)
            logger.warning("mermaid block failed to render; keeping as plain text")
            return "```text\n%% mermaid failed to render; kept as text\n" + code + "\n```"

        return re.sub(r"```mermaid\n(.*?)\n```", check, body, flags=re.S)

    def _context_block(self, post: ParsedPost, ref: ImageRef) -> str:
        if self.context_chars <= 0:
            return ""
        idx = post.markdown.find(ref.placeholder)
        if idx == -1:
            return ""
        start = max(0, idx - self.context_chars)
        end = min(len(post.markdown), idx + len(ref.placeholder) + self.context_chars)
        snippet = re.sub(r"\{\{IMG:\d+\}\}", "", post.markdown[start:end]).strip()
        caption = f"Caption: {ref.caption.strip()}\n" if ref.caption.strip() else ""
        alt = f"Alt text: {ref.alt}\n" if ref.alt and not re.fullmatch(r"image\d*\.\w+", ref.alt) else ""
        return f"{caption}{alt}Surrounding post text (for disambiguating labels):\n---\n{snippet}\n---\n\n"


def _indent(text: str, prefix: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())


# --------------------------------------------------------------------------- per-post pipeline


def render_annotation(ref: ImageRef, ann: Annotation) -> str:
    """Markdown that replaces the ``{{IMG:n}}`` placeholder."""
    if ann.verdict == VERDICT_IGNORE:
        return ""  # dropped, like non-informational images in CodexAnnotator
    if ann.verdict == "SKIPPED":
        return ""  # prefiltered decoration
    if ann.verdict == "FAILED":
        return f"> [image {ref.index} not annotated: {ann.reason}. source: {ref.src}]\n"
    if ann.verdict == "PLACEHOLDER":
        return f"![{ref.alt or f'image {ref.index}'}]({ref.src})\n"
    caption = f"*{ref.caption.strip()}*\n\n" if ref.caption.strip() else ""
    return f"{caption}{ann.body}\n\n<sub>source image: {ref.src}</sub>\n"


def write_post_markdown(post: ParsedPost, annotations: dict[int, Annotation], out_path: Path) -> None:
    body = post.markdown
    for ref in post.images:
        ann = annotations.get(ref.index, Annotation("PLACEHOLDER"))
        body = body.replace(ref.placeholder, render_annotation(ref, ann))
    body = re.sub(r"\n{3,}", "\n\n", body)
    arch = sum(1 for a in annotations.values() if a.verdict == VERDICT_ARCH)
    header = [
        f"# {post.title}",
        "",
        *([f"*{post.subtitle}*", ""] if post.subtitle else []),
        f"- Source: {post.url}",
        f"- Published: {post.published or 'unknown'}",
        f"- Authors: {', '.join(post.authors) or 'unknown'}",
        f"- Categories: {', '.join(post.categories) or 'unknown'}",
        f"- Images: {len(post.images)} total, {arch} extracted as architecture",
        "",
    ]
    if post.summary:
        header += ["**Key takeaways**", ""] + [f"- {s}" for s in post.summary] + [""]
    out_path.write_text("\n".join(header) + "\n" + body.strip() + "\n", encoding="utf-8")


def process_post(
    slug: str,
    meta: PostMeta | None,
    index: Index,
    posts_dir: Path,
    annotator: CodexImageAnnotator | None,
    workdir: Path,
    keep_images: bool,
) -> tuple[ParsedPost, int, int]:
    page = fetch(f"{BASE}/blog/{slug}")
    post = parse_post(slug, page, meta)
    if not post.markdown.strip():
        raise RuntimeError(f"{slug}: empty body (body container not found?)")

    annotations: dict[int, Annotation] = {}
    if annotator is not None:
        annotations = annotate_images(post, index, annotator, workdir, keep_images)

    out_path = posts_dir / f"{file_stem(slug)}.md"
    write_post_markdown(post, annotations, out_path)
    arch = sum(1 for a in annotations.values() if a.verdict == VERDICT_ARCH)
    index.upsert_post(post, out_path, len(post.images), arch, annotated=annotator is not None)
    return post, len(post.images), arch


def annotate_images(
    post: ParsedPost, index: Index, annotator: CodexImageAnnotator, workdir: Path, keep_images: bool
) -> dict[int, Annotation]:
    """Download, prefilter, cache-check, then annotate the remaining images concurrently."""
    results: dict[int, Annotation] = {}
    todo: list[tuple[ImageRef, Path, str]] = []
    post_dir = workdir / file_stem(post.slug)
    post_dir.mkdir(parents=True, exist_ok=True)

    for ref in post.images:
        reason = annotator.prefilter(ref)
        if reason:
            results[ref.index] = Annotation("SKIPPED", reason=reason, annotator="prefilter")
            index.link_post_image(post.slug, ref.index, None, ref.src)
            continue
        try:
            data = fetch(ref.src, binary=True)
        except RuntimeError as exc:
            results[ref.index] = Annotation("FAILED", reason=f"download failed: {exc}")
            index.link_post_image(post.slug, ref.index, None, ref.src)
            continue
        md5 = hashlib.md5(data).hexdigest()
        index.link_post_image(post.slug, ref.index, md5, ref.src)
        cached = index.get_image(md5)
        if cached is not None and cached["verdict"] in (VERDICT_ARCH, VERDICT_IGNORE, "SKIPPED"):
            logger.info("cache hit %s img %d (%s)", post.slug, ref.index, cached["verdict"])
            results[ref.index] = Annotation(cached["verdict"], body=cached["body"] or "", annotator=cached["annotator"])
            continue
        if any(md5 == m for _, _, m in todo):
            # Same bytes twice in one post: annotate once, replay below.
            results[ref.index] = Annotation("DUP", reason=md5)
            continue
        ext = Path(urllib.parse.urlparse(ref.src).path).suffix or ".png"
        path = post_dir / f"img{ref.index:02d}{ext}"
        path.write_bytes(data)
        todo.append((ref, path, md5))

    def run(item: tuple[ImageRef, Path, str]) -> tuple[ImageRef, str, Annotation]:
        ref, path, md5 = item
        logger.info("codex: %s img %d/%d", post.slug, ref.index, len(post.images))
        ann = annotator.annotate(post, ref, path, post_dir)
        if not keep_images:
            path.unlink(missing_ok=True)  # the image has served its purpose
        return ref, md5, ann

    if todo:
        with ThreadPoolExecutor(max_workers=annotator.max_workers) as pool:
            for fut in as_completed([pool.submit(run, item) for item in todo]):
                ref, md5, ann = fut.result()
                results[ref.index] = ann
                if ann.verdict != "FAILED":  # failures are not cached so the next run retries
                    index.record_image(md5, ref.src, post.slug, ann.verdict, ann.body, ann.reason, ann.annotator, annotator.model or "default")
                logger.info("%s img %d -> %s", post.slug, ref.index, ann.verdict)

    # Replay duplicates.
    by_md5 = {m: results[r.index] for r, _, m in todo}
    for idx, ann in list(results.items()):
        if ann.verdict == "DUP":
            results[idx] = by_md5.get(ann.reason, Annotation("FAILED", reason="dup source failed"))

    if not keep_images:
        shutil.rmtree(post_dir, ignore_errors=True)
    return results


# --------------------------------------------------------------------------- index.md


def write_index_md(index: Index, out_path: Path) -> None:
    rows = index.list_posts()
    lines = [
        "# Databricks engineering blog harvest",
        "",
        "Generated by `harvest.py`. Metadata lives in `index.db` (sqlite); one markdown file per post in `posts/`.",
        "",
        "| Published | Title | Images | Arch |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['published'] or ''} | [{r['title']}]({r['md_path']}) | {r['image_count']} | {r['arch_count']} |")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listing", default=DEFAULT_LISTING, help="listing URL to crawl")
    ap.add_argument("--since", default=None, help="only posts published on/after this date (YYYY or YYYY-MM-DD)")
    ap.add_argument("--until", default=None, help="only posts published on/before this date")
    ap.add_argument("--limit", type=int, default=None, help="max posts to process this run")
    ap.add_argument("--slug", action="append", default=[], help="process only these slugs (repeatable)")
    ap.add_argument("--force", action="store_true", help="re-process posts already in index.db")
    ap.add_argument("--skip-codex", action="store_true", help="no annotation; images left as ![alt](url)")
    ap.add_argument("--keep-images", action="store_true", help="do not delete downloaded images (kept under --workdir)")
    ap.add_argument("--workdir", default=None, help="where images are downloaded (default: temp dir)")
    ap.add_argument("--model", default="", help="codex model (default: ~/.codex/config.toml)")
    ap.add_argument("--effort", default="low", choices=["minimal", "low", "medium", "high"])
    ap.add_argument("--max-workers", type=int, default=3, help="concurrent codex processes")
    ap.add_argument("--timeout", type=int, default=240, help="seconds per codex call")
    ap.add_argument("--validate-mermaid", action="store_true", help="render each mermaid block with mmdc")
    ap.add_argument("--list", action="store_true", help="print index.db and exit")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    posts_dir = HERE / "posts"
    posts_dir.mkdir(exist_ok=True)
    index = Index(HERE / "index.db")

    if args.list:
        for r in index.list_posts():
            flag = "" if r["annotated"] else "  (not annotated)"
            print(f"{r['published'] or '????-??-??'}  {r['arch_count']:>2}/{r['image_count']:<2}  {r['slug']}{flag}")
        return 0

    annotator: CodexImageAnnotator | None = None
    if not args.skip_codex:
        if not CodexImageAnnotator.is_available():
            logger.error("`codex` not on PATH; rerun with --skip-codex or install the Codex CLI")
            return 2
        annotator = CodexImageAnnotator(
            index,
            model=args.model,
            reasoning_effort=args.effort,
            timeout_seconds=args.timeout,
            max_workers=args.max_workers,
            validate_mermaid=args.validate_mermaid,
        )

    catalog = {m.slug: m for m in load_catalog(args.listing)}
    if args.slug:
        slugs = list(args.slug)
    else:
        slugs = [
            m.slug
            for m in catalog.values()
            if (not args.since or m.published >= args.since) and (not args.until or m.published <= args.until)
        ]
    if not args.force:
        before = len(slugs)
        slugs = [s for s in slugs if not index.has_post(s, need_annotated=annotator is not None)]
        logger.info("%d posts selected, %d already harvested, %d to do", before, before - len(slugs), len(slugs))
    if args.limit is not None:
        slugs = slugs[: args.limit]

    workdir_ctx = tempfile.TemporaryDirectory(prefix="databricks-harvest-") if args.workdir is None else None
    workdir = Path(args.workdir) if args.workdir else Path(workdir_ctx.name)  # type: ignore[union-attr]
    workdir.mkdir(parents=True, exist_ok=True)

    failures = 0
    try:
        for i, slug in enumerate(slugs, 1):
            logger.info("[%d/%d] %s", i, len(slugs), slug)
            try:
                post, n_img, n_arch = process_post(
                    slug, catalog.get(slug), index, posts_dir, annotator, workdir, args.keep_images
                )
                logger.info("wrote posts/%s.md (%d images, %d architecture)", file_stem(slug), n_img, n_arch)
            except Exception as exc:  # noqa: BLE001  -- one bad post must not kill the crawl
                failures += 1
                logger.error("%s failed: %s", slug, exc, exc_info=args.verbose)
            write_index_md(index, HERE / "index.md")
    finally:
        if workdir_ctx is not None:
            workdir_ctx.cleanup()

    write_index_md(index, HERE / "index.md")
    logger.info("done: %d posts, %d failures", len(slugs) - failures, failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
