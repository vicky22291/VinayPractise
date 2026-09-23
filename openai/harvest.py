#!/usr/bin/env python3
"""Harvest OpenAI engineering blog posts into markdown, with images turned into text.

Same pipeline and same output shape as ``databricks/harvest.py`` (stdlib only):

    RSS + category sitemap  ->  post HTML  ->  markdown (images as placeholders)
                                           ->  download images to a temp dir
                                           ->  codex exec -i <image>  (ARCHITECTURE | IGNORE)
                                           ->  splice codex text + mermaid into the markdown
                                           ->  delete the image files
                                           ->  posts/<slug>.md  +  rows in index.db

Three things differ from the Databricks harvester, all forced by how openai.com is built:

1. openai.com answers HTTP/2 requests for HTML with 403 and HTTP/1.1 requests with 200,
   and it 403s the default ``Python-urllib`` User-Agent. urllib speaks HTTP/1.1, so the
   only thing we have to do is send a browser UA. ``curl`` needs ``--http1.1``.
2. There is no catalog JSON. The site RSS feed carries every post with its category,
   date and summary; the per-category sitemap carries the canonical slug list. We union
   the two, so a post missing from either source is still harvested.
3. Every architecture diagram on the OpenAI blog is an SVG served by Contentful, and a
   vision model cannot read SVG. Contentful's image API rasterises on request, so we
   download ``<url>.svg?fm=png`` instead of skipping SVG the way the Databricks one does.

Usage:
    python3 openai/harvest.py                     # every engineering post, annotate, write md
    python3 openai/harvest.py --category security # any category the sitemap index lists
    python3 openai/harvest.py --since 2026 --limit 5
    python3 openai/harvest.py --skip-codex        # markdown only, images left as ![alt](url)
    python3 openai/harvest.py --force --slug scaling-postgresql
    python3 openai/harvest.py --list              # print what is in index.db
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
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

logger = logging.getLogger("harvest")

HERE = Path(__file__).resolve().parent
BASE = "https://openai.com"
RSS_URL = BASE + "/news/rss.xml"
SITEMAP_URL = BASE + "/sitemap.xml/{category}/"
DEFAULT_CATEGORY = "engineering"
# The default urllib UA gets a 403. Any browser-shaped UA is served normally.
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

# First line = verdict, so a reply can be routed without parsing the rest.
PROMPT_TEMPLATE = """You are looking at ONE image from an OpenAI engineering blog post.

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

# Some diagrams on this blog are not images at all: they are animated HTML that draws itself
# with positioned divs. There are no bytes to look at, only labels in DOM order, so those go
# to the model as text with the same verdict contract.
FIGURE_PROMPT_TEMPLATE = """You are looking at the text content of ONE interactive diagram from an OpenAI engineering
blog post. The diagram is drawn in HTML, so all you get is its labels in reading order:
caption first, then node names, edge labels and axis labels, and possibly stray playback
controls like "Play" or "Replay" which you should ignore.

Post title: {title}
{context_block}Diagram text:
---
{figure_text}
---

Instructions:
1. The first line of your response MUST be exactly one of:
   ARCHITECTURE  -- the labels describe a system/architecture diagram, data flow, component
                    layout, sequence of calls, state machine, storage layout, or a chart with
                    technical numbers (latency, throughput, cost, scale).
   IGNORE        -- the labels are decoration, navigation, or carry no technical content.

2. If IGNORE, stop after the first line.

3. If ARCHITECTURE, output these sections in this exact order:

**Summary:** one sentence stating what the diagram shows.

**Components:** a bullet per node naming the component and the technology it uses.

**Flows:** a bullet per edge: `A -> B: what flows` (request, response, CDC, cache miss, ...).

**Numbers:** every number, unit, percentage or size in the labels. Write `none` if there are none.

Then a Mermaid diagram that reproduces it. Rules for the diagram:
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
- Do NOT invent components, arrows or numbers that are not in the labels above.
- Do NOT describe the diagram type ("This is a diagram of...").
- Do not use em dashes anywhere. Use a plain hyphen or a new sentence.
- The labels above are your only source."""

MIN_FIGURE_CHARS = 60

# Cheap pre-filter, matched against the image filename. Note SVG is NOT here: on this blog
# every real diagram is an SVG, so they are rasterised instead of skipped (see png_url).
SKIP_SRC_PATTERNS = re.compile(
    r"(art[-_]?card|1x1|1080_1080|[-_]cover|hero|logo|icon|avatar|headshot|badge|seo[-_]16x9|\.gif($|\?))",
    re.I,
)
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
            # A stray NUL makes subprocess reject the prompt with "embedded null byte".
            return data.decode("utf-8", errors="replace").replace("\x00", "")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            logger.warning("fetch %s failed (attempt %d/%d): %s", url, attempt, retries, exc)
            time.sleep(2 * attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


# --------------------------------------------------------------------------- catalog


@dataclass
class PostMeta:
    slug: str
    title: str
    subtitle: str
    published: str  # ISO date, YYYY-MM-DD
    authors: list[str]
    categories: list[str]
    word_count: int = 0

    @property
    def url(self) -> str:
        return f"{BASE}/index/{self.slug}/"


def _slug_from_url(url: str) -> str:
    return urllib.parse.urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]


def _rss_date(text: str) -> str:
    """RFC 822 pubDate -> ISO date."""
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def load_catalog(category: str) -> list[PostMeta]:
    """Every post in a category, newest first.

    Two sources, unioned. The RSS feed has title/summary/date/categories for every post on
    the site; the category sitemap has the canonical slug list for one category. Neither is
    guaranteed complete on its own, so a slug in either one is harvested.
    """
    by_slug: dict[str, PostMeta] = {}
    wanted = category.replace("-", " ").lower()

    root = ET.fromstring(fetch(RSS_URL))
    for item in root.iterfind("./channel/item"):
        link = (item.findtext("link") or "").strip()
        if "/index/" not in link:
            continue
        cats = [(c.text or "").strip() for c in item.iterfind("category")]
        if wanted not in [c.lower() for c in cats]:
            continue
        slug = _slug_from_url(link)
        by_slug[slug] = PostMeta(
            slug=slug,
            title=(item.findtext("title") or "").strip(),
            subtitle=(item.findtext("description") or "").strip(),
            published=_rss_date(item.findtext("pubDate") or ""),
            authors=[],
            categories=cats,
        )
    from_rss = len(by_slug)

    # Sitemap: canonical slug list, but no metadata and no publish date. Anything it knows
    # about that RSS did not mention is harvested with metadata scraped off the page.
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    try:
        sm = ET.fromstring(fetch(SITEMAP_URL.format(category=category)))
    except (ET.ParseError, RuntimeError) as exc:
        logger.warning("sitemap for %s unavailable (%s); using RSS only", category, exc)
    else:
        for loc in sm.iterfind(".//sm:url/sm:loc", ns):
            url = (loc.text or "").strip()
            if "/index/" not in url or re.search(r"openai\.com/[a-z]{2}-[A-Z]{2}/", url):
                continue  # translated locale copies of the same post
            slug = _slug_from_url(url)
            by_slug.setdefault(
                slug,
                PostMeta(slug=slug, title="", subtitle="", published="", authors=[], categories=[category]),
            )

    posts = sorted(by_slug.values(), key=lambda p: (p.published, p.slug), reverse=True)
    logger.info("catalog %s: %d posts (%d from rss, %d sitemap-only)", category, len(posts), from_rss, len(posts) - from_rss)
    return posts


# --------------------------------------------------------------------------- HTML -> markdown


@dataclass
class ImageRef:
    index: int
    src: str  # canonical URL, no query string; this is what the markdown cites
    alt: str
    width: int | None
    height: int | None
    caption: str = ""

    @property
    def placeholder(self) -> str:
        return f"{{{{IMG:{self.index}}}}}"

    @property
    def fetch_url(self) -> str:
        """What we actually download. Contentful rasterises SVG when asked for ``fm=png``."""
        if "images.ctfassets.net" not in self.src:
            return self.src
        return self.src + "?fm=png&w=1600&q=90"


@dataclass
class FigureRef:
    """An animated HTML diagram: no image bytes, only the labels it renders."""

    index: int
    text: str

    @property
    def placeholder(self) -> str:
        return f"{{{{FIG:{self.index}}}}}"

    @property
    def md5(self) -> str:
        return hashlib.md5(self.text.encode("utf-8")).hexdigest()


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
    figures: list[FigureRef] = field(default_factory=list)


VOID_TAGS = {
    "img", "br", "hr", "input", "meta", "link", "source", "use", "path", "col",
    "area", "base", "embed", "param", "track", "wbr", "circle", "rect", "line",
}
# Page furniture that never carries post content.
SKIP_TAGS = {"script", "style", "noscript", "nav", "button", "svg", "audio", "video", "form", "select", "textarea", "template", "aside"}


class ArticleToMarkdown(HTMLParser):
    """Convert the ``<article>`` of an openai.com post into markdown.

    Images become ``{{IMG:n}}`` placeholders on their own line so a later pass can swap in
    the codex annotation. The page is a Tailwind soup with no semantic body container, so
    the boundaries are drawn by what we throw away rather than by what we select:

    - everything before the first ``<article>`` and after it closes;
    - the hero block (``data-article-hero-copy-region``, ``--hero-aspect-ratio``), whose
      title/date/byline we read as metadata instead;
    - the ``citations`` section and the "Keep reading" carousel, which end the post;
    - nav, buttons, svg, audio and ``sr-only`` text.

    Code blocks need their own handling: openai.com renders them as ``<code><pre>`` (that
    nesting, not the usual one) with one ``<div>`` per line and the line number in a
    sibling ``<span>``, so a naive walk interleaves line numbers with code.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.images: list[ImageRef] = []
        self.figures: list[FigureRef] = []
        self._figure_stack: list[tuple[int, int]] = []  # (out mark, image count) per open <figure>
        self._stack: list[str] = []
        self._article_depth = 0
        self._done = False  # hit citations / "Keep reading": ignore the rest of the article
        self._skip_from: int | None = None  # stack depth at which a skipped subtree started
        self._list_stack: list[tuple[str, int]] = []
        self._in_pre = False
        self._pre_rows = 0
        self._in_code = False
        self._href: str | None = None
        self._link_text: list[str] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._heading_mark: int | None = None
        self._last_h4: tuple[int, str] | None = None  # (out mark, text) -> code fence language
        self._pending_caption_for: ImageRef | None = None
        self._in_figcaption = False

    # -- helpers
    @property
    def _capturing(self) -> bool:
        return self._article_depth > 0 and not self._done and self._skip_from is None

    def _emit(self, text: str) -> None:
        if self._cell is not None:
            self._cell.append(text)
        elif self._href is not None:
            self._link_text.append(text)
        else:
            self.out.append(text)

    def _newline(self, n: int = 2) -> None:
        if self._cell is not None or self._in_pre:
            return
        joined = "".join(self.out)
        trailing = len(joined) - len(joined.rstrip("\n"))
        if trailing < n:
            self.out.append("\n" * (n - trailing))

    def _should_skip(self, tag: str, a: dict[str, str]) -> bool:
        if tag in SKIP_TAGS:
            return True
        cls = a.get("class", "")
        if "sr-only" in cls:
            return True  # "(opens in a new window)"
        if a.get("aria-hidden") == "true":
            return True
        if "data-article-hero-copy-region" in a:
            return True  # title/date/byline, read from the page metadata instead
        if "--hero-aspect-ratio" in a.get("style", ""):
            return True  # hero art card
        if self._in_pre and "min-w-5" in cls:
            return True  # the line-number gutter of a code block
        return False

    # -- parser callbacks
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "article":
            self._article_depth += 1
        if tag not in VOID_TAGS:
            self._stack.append(tag)
        if self._article_depth == 0 or self._done or self._skip_from is not None:
            return
        if a.get("id") == "citations" or a.get("data-testid") == "citations":
            self._done = True
            return
        if self._should_skip(tag, a):
            self._skip_from = len(self._stack)
            return
        self._handle_open(tag, a)

    def _handle_open(self, tag: str, a: dict[str, str]) -> None:
        cls = a.get("class", "")
        if self._in_pre:
            if tag == "div" and "flex-row" in cls:
                if self._pre_rows:
                    self._emit("\n")
                self._pre_rows += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._newline()
            self._heading_mark = len(self.out)
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
        elif tag == "code" and "syntaxHighlight" in cls:
            self._open_code_block()
        elif tag == "code":
            self._in_code = True
            self._emit("`")
        elif tag == "pre":
            if not self._in_pre:  # a bare <pre> with no <code> wrapper
                self._open_code_block()
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
            self._handle_image(a)
        elif tag == "figure":
            self._newline()
            self._figure_stack.append((len(self.out), len(self.images)))
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

    def _open_code_block(self) -> None:
        """Open a fence, stealing the label heading above the block as the language."""
        lang = ""
        if self._last_h4 is not None:
            mark, text = self._last_h4
            emitted = "".join(self.out[mark:]).strip()
            if emitted == f"#### {text}".strip():  # nothing but the label since
                del self.out[mark:]
                if text.lower() != "plain text":
                    lang = re.sub(r"[^a-z0-9+#]", "", text.lower())
        self._last_h4 = None
        self._newline()
        self._emit(f"```{lang}\n")
        self._in_pre = True
        self._pre_rows = 0

    def _handle_image(self, a: dict[str, str]) -> None:
        src = a.get("src") or _largest_srcset(a.get("srcset", ""))
        if src.startswith("/"):
            src = BASE + src
        if not src or src.startswith("data:"):
            return
        src = src.split("?", 1)[0]
        if any(src == ref.src for ref in self.images):
            return  # the same asset rendered again at another breakpoint
        ref = ImageRef(
            index=len(self.images) + 1,
            src=src,
            alt=html.unescape(a.get("alt", "")).strip().strip('"'),
            width=_int_or_none(a.get("width")),
            height=_int_or_none(a.get("height")),
        )
        self.images.append(ref)
        self._pending_caption_for = ref
        self._newline()
        self.out.append(ref.placeholder)
        self._newline()

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        if tag in self._stack:  # unwind, tolerating unclosed inline tags
            while self._stack:
                if self._stack.pop() == tag:
                    break
        if self._skip_from is not None:
            if len(self._stack) < self._skip_from:
                self._skip_from = None
            return
        if tag == "article":
            self._article_depth = max(0, self._article_depth - 1)
            return
        if self._article_depth == 0 or self._done:
            return
        self._handle_close(tag)

    def _handle_close(self, tag: str) -> None:
        if self._in_pre:
            if tag in ("code", "pre"):
                self._in_pre = False
                self._emit("\n```")
                self._newline()
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._close_heading(tag)
        elif tag in ("p", "blockquote"):
            self._newline()
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            self._newline(1 if self._list_stack else 2)
        elif tag == "li":
            self._newline(1)
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
        elif tag == "figure":
            self._close_figure()
        elif tag == "figcaption":
            self._in_figcaption = False
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self._close_table()

    def _close_figure(self) -> None:
        """A <figure> with no <img> inside draws itself in HTML. Keep its labels as one unit."""
        if not self._figure_stack:
            return
        mark, images_before = self._figure_stack.pop()
        if len(self.images) != images_before:
            return  # it had an image; that placeholder already stands in for it
        text = " ".join("".join(self.out[mark:]).replace("\n", " ").split())
        del self.out[mark:]
        if len(text) < MIN_FIGURE_CHARS:
            return  # not a diagram, just a stray wrapper
        ref = FigureRef(index=len(self.figures) + 1, text=text)
        self.figures.append(ref)
        self._newline()
        self.out.append(ref.placeholder)
        self._newline()

    def _close_heading(self, tag: str) -> None:
        mark, self._heading_mark = self._heading_mark, None
        if mark is None:
            self._newline()
            return
        text = "".join(self.out[mark:]).lstrip("# ").strip()
        if text.lower() in ("keep reading", "author", "authors", "acknowledgements", "acknowledgments"):
            del self.out[mark:]
            self._done = True  # everything below is site furniture
            return
        if tag == "h4":
            self._last_h4 = (mark, text)
        self._newline()

    def _close_table(self) -> None:
        rows = [r for r in self._table or [] if r]
        self._table = None
        if not rows:
            return
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        self._newline()
        self.out.append("| " + " | ".join(rows[0]) + " |\n")
        self.out.append("|" + "---|" * width + "\n")
        for r in rows[1:]:
            self.out.append("| " + " | ".join(r) + " |\n")
        self._newline()

    def handle_data(self, data: str) -> None:
        if not self._capturing:
            return
        if self._in_figcaption and self._pending_caption_for is not None:
            self._pending_caption_for.caption += data
        if self._in_pre:
            self._emit(data)
            return
        text = re.sub(r"[ \t\r\n]+", " ", data)
        if not text:
            return
        if text == " " and (not self.out or self.out[-1].endswith("\n")):
            return
        self._emit(text)

    def markdown(self) -> str:
        text = "".join(self.out)
        text = text.replace("⁠", "").replace("​", "")  # word joiners left by link markup
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"^#{1,6}\s*$", "", text, flags=re.M)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def _largest_srcset(srcset: str) -> str:
    """Pick the widest candidate out of a ``srcset``."""
    best, best_w = "", -1
    for part in srcset.split(","):
        bits = part.strip().split()
        if not bits:
            continue
        w = int(bits[1][:-1]) if len(bits) > 1 and bits[1].endswith("w") and bits[1][:-1].isdigit() else 0
        if w >= best_w:
            best, best_w = bits[0], w
    return best


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _meta(page: str, pattern: str) -> str:
    m = re.search(pattern, page, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def _strip_tags(text: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def parse_post(slug: str, page: str, meta: PostMeta | None = None) -> ParsedPost:
    """Body from the HTML. Metadata from the catalog when we have it, page as the fallback."""
    scraped_title = _strip_tags(_meta(page, r'<meta property="og:title" content="([^"]*)"'))
    scraped_sub = _strip_tags(_meta(page, r'<meta property="og:description" content="([^"]*)"'))
    scraped_date = _hero_date(page)
    categories = _hero_categories(page)
    authors = _authors(page)

    title = (meta.title if meta else "") or scraped_title
    subtitle = (meta.subtitle if meta else "") or scraped_sub
    published = (meta.published if meta else "") or scraped_date
    if meta and meta.categories:
        categories = list(dict.fromkeys(meta.categories + categories))

    conv = ArticleToMarkdown()
    conv.feed(page)
    conv.close()
    markdown = conv.markdown()
    return ParsedPost(
        slug=slug,
        url=f"{BASE}/index/{slug}/",
        title=title,
        subtitle=subtitle,
        published=published,
        authors=authors,
        categories=categories,
        word_count=len(markdown.split()),
        summary=[],
        markdown=markdown,
        images=conv.images,
        figures=conv.figures,
    )


def _hero_meta_block(page: str) -> str:
    return _meta(page, r'data-article-hero-copy-region="meta"[^>]*>(.*?)</div>') or ""


def _hero_date(page: str) -> str:
    block = _hero_meta_block(page)
    for chunk in re.split(r"<[^>]+>", block):
        iso = _to_iso_date(chunk)
        if iso:
            return iso
    return ""


def _hero_categories(page: str) -> list[str]:
    block = _hero_meta_block(page)
    return [_strip_tags(m) for m in re.findall(r'<a[^>]*href="/news/[^"]*"[^>]*>(.*?)</a>', block, re.S) if _strip_tags(m)]


def _authors(page: str) -> list[str]:
    """The ``Author``/``Authors`` block in the citations section, else the hero byline."""
    for block in re.findall(r'data-testid="author-list"[^>]*>(.*?)</div>\s*</div>', page, re.S):
        heading = _strip_tags(_meta(block, r"<h2[^>]*>(.*?)</h2>"))
        if heading.lower().startswith("author"):
            names = _strip_tags(re.sub(r"<h2[^>]*>.*?</h2>", "", block, flags=re.S))
            if names:
                return [n.strip() for n in re.split(r",| and |&", names) if n.strip()]
    byline = _strip_tags(_meta(page, r'data-article-hero-copy-region="subhead"[^>]*>(.*?)</p>'))
    m = re.match(r"By (?:Members? of (?:the )?Technical Staff:\s*)?(.+?)(?:,\s*Members?\b.*)?$", byline)
    if not m:
        return []
    return [n.strip() for n in re.split(r",| and |&", m.group(1)) if n.strip()]


def _to_iso_date(text: str) -> str:
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def file_stem(slug: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", slug.strip("/").replace("/", "-"))


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
    summary     TEXT,           -- JSON list
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
    reason       TEXT,
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
        with self.lock:
            row = self.conn.execute("SELECT annotated FROM posts WHERE slug=?", (slug,)).fetchone()
        return row is not None and (bool(row["annotated"]) or not need_annotated)

    def upsert_post(self, post: ParsedPost, md_path: Path, image_count: int, arch_count: int, annotated: bool) -> None:
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
                    post.slug, post.url, post.title, post.subtitle, post.published,
                    json.dumps(post.authors), json.dumps(post.categories), json.dumps(post.summary),
                    post.word_count, str(md_path.relative_to(HERE)), image_count, arch_count,
                    int(annotated), _now(),
                ),
            )
            self.conn.commit()

    def get_image(self, md5: str) -> sqlite3.Row | None:
        with self.lock:
            return self.conn.execute("SELECT * FROM images WHERE md5=?", (md5,)).fetchone()

    def record_image(self, md5: str, src: str, slug: str, verdict: str, body: str, reason: str, annotator: str, model: str) -> None:
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

    def failed_slugs(self) -> list[str]:
        """Posts holding an image that download or codex could not turn into an annotation."""
        with self.lock:
            rows = self.conn.execute(
                "SELECT DISTINCT pi.slug FROM post_images pi JOIN images i ON i.md5 = pi.md5 "
                "WHERE i.verdict = 'FAILED' ORDER BY pi.slug"
            ).fetchall()
        return [r["slug"] for r in rows]

    def clear_failure(self, md5: str) -> None:
        with self.lock:
            self.conn.execute("DELETE FROM images WHERE md5=? AND verdict='FAILED'", (md5,))
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

    @staticmethod
    def prefilter(ref: ImageRef) -> str | None:
        """Return a skip reason for images that are obviously not diagrams, else None."""
        name = urllib.parse.unquote(ref.src.rsplit("/", 1)[-1])
        if SKIP_SRC_PATTERNS.search(name):
            return "filename looks like an art card / logo / cover"
        if ref.width is not None and ref.height is not None and (ref.width < MIN_IMAGE_PX or ref.height < MIN_IMAGE_PX):
            return f"too small ({ref.width}x{ref.height})"
        return None

    def annotate(self, post: ParsedPost, ref: ImageRef, image_path: Path, workdir: Path) -> Annotation:
        prompt = PROMPT_TEMPLATE.format(
            title=post.title,
            context_block=self._context_block(post, ref),
            legend=_indent(COLOR_LEGEND, "  "),
        )
        return self._attempt(prompt, image_path, workdir, stem=image_path.stem)

    def annotate_figure(self, post: ParsedPost, ref: FigureRef, workdir: Path) -> Annotation:
        """Same contract as annotate(), but the diagram arrives as labels instead of pixels."""
        prompt = FIGURE_PROMPT_TEMPLATE.format(
            title=post.title,
            context_block=self._context_block(post, ref),
            figure_text=ref.text,
            legend=_indent(COLOR_LEGEND, "  "),
        )
        return self._attempt(prompt, None, workdir, stem=f"fig{ref.index:02d}")

    def _attempt(self, prompt: str, image_path: Path | None, workdir: Path, *, stem: str) -> Annotation:
        last_reason = ""
        for attempt in range(1, self.rate_limit_attempts + 1):
            try:
                return self._parse(self._run_codex(prompt, image_path, workdir, stem))
            except CodexRateLimited as exc:
                last_reason = str(exc)
                if attempt == self.rate_limit_attempts:
                    break
                logger.warning(
                    "codex rate-limited on %s (attempt %d/%d); sleeping %ds",
                    stem, attempt, self.rate_limit_attempts, self.rate_limit_wait,
                )
                time.sleep(self.rate_limit_wait)
            except subprocess.TimeoutExpired:
                return Annotation("FAILED", reason=f"codex timed out after {self.timeout_seconds}s")
            except RuntimeError as exc:
                return Annotation("FAILED", reason=str(exc))
        return Annotation("FAILED", reason=f"rate-limited: {last_reason}")

    def _run_codex(self, prompt: str, image_path: Path | None, workdir: Path, stem: str) -> str:
        out_file = workdir / f"{stem}.codex.txt"
        cmd = [
            "codex", "exec",
            "--skip-git-repo-check",
            "-s", "read-only",
            "-c", f"model_reasoning_effort={self.reasoning_effort}",
            *(["-i", str(image_path)] if image_path is not None else []),
            "-o", str(out_file),
        ]
        if self.model:
            cmd += ["-m", self.model]
        cmd.append(prompt)
        # stdin MUST be closed: `codex exec` appends piped stdin to the prompt and blocks
        # until EOF, so an inherited pipe hangs every call to the timeout.
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

    def _context_block(self, post: ParsedPost, ref: ImageRef | FigureRef) -> str:
        if self.context_chars <= 0:
            return ""
        idx = post.markdown.find(ref.placeholder)
        if idx == -1:
            return ""
        start = max(0, idx - self.context_chars)
        end = min(len(post.markdown), idx + len(ref.placeholder) + self.context_chars)
        snippet = re.sub(r"\{\{(?:IMG|FIG):\d+\}\}", "", post.markdown[start:end]).strip()
        caption = alt = ""
        if isinstance(ref, ImageRef):
            caption = f"Caption: {ref.caption.strip()}\n" if ref.caption.strip() else ""
            if ref.alt and not re.fullmatch(r"image ?\d*(\.\w+)?", ref.alt, re.I):
                alt = f"Alt text: {ref.alt}\n"
        return f"{caption}{alt}Surrounding post text (for disambiguating labels):\n---\n{snippet}\n---\n\n"


def _indent(text: str, prefix: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())


# --------------------------------------------------------------------------- per-post pipeline


def render_annotation(ref: ImageRef, ann: Annotation) -> str:
    """Markdown that replaces the ``{{IMG:n}}`` placeholder."""
    if ann.verdict in (VERDICT_IGNORE, "SKIPPED"):
        return ""
    if ann.verdict == "FAILED":
        return f"> [image {ref.index} not annotated: {ann.reason}. source: {ref.src}]\n"
    if ann.verdict == "PLACEHOLDER":
        return f"![{ref.alt or f'image {ref.index}'}]({ref.src})\n"
    caption = f"*{ref.caption.strip()}*\n\n" if ref.caption.strip() else ""
    return f"{caption}{ann.body}\n\n<sub>source image: {ref.src}</sub>\n"


def render_figure(ref: FigureRef, ann: Annotation) -> str:
    """Markdown that replaces the ``{{FIG:n}}`` placeholder."""
    if ann.verdict in (VERDICT_IGNORE, "SKIPPED"):
        return ""
    if ann.verdict in ("FAILED", "PLACEHOLDER"):
        return f"> [interactive diagram, not annotated. Labels: {ref.text[:300]}]\n"
    return f"{ann.body}\n\n<sub>source: interactive diagram {ref.index} on the post page</sub>\n"


def write_post_markdown(
    post: ParsedPost,
    annotations: dict[int, Annotation],
    fig_annotations: dict[int, Annotation],
    out_path: Path,
) -> None:
    body = post.markdown
    for ref in post.images:
        ann = annotations.get(ref.index, Annotation("PLACEHOLDER"))
        body = body.replace(ref.placeholder, render_annotation(ref, ann))
    for fig in post.figures:
        ann = fig_annotations.get(fig.index, Annotation("PLACEHOLDER"))
        body = body.replace(fig.placeholder, render_figure(fig, ann))
    body = re.sub(r"\n{3,}", "\n\n", body)
    arch = sum(1 for a in [*annotations.values(), *fig_annotations.values()] if a.verdict == VERDICT_ARCH)
    header = [
        f"# {post.title}",
        "",
        *([f"*{post.subtitle}*", ""] if post.subtitle else []),
        f"- Source: {post.url}",
        f"- Published: {post.published or 'unknown'}",
        f"- Authors: {', '.join(post.authors) or 'unknown'}",
        f"- Categories: {', '.join(post.categories) or 'unknown'}",
        f"- Diagrams: {len(post.images) + len(post.figures)} candidates, {arch} extracted as architecture",
        "",
    ]
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
    page = fetch(f"{BASE}/index/{slug}/")
    post = parse_post(slug, page, meta)
    if not post.markdown.strip():
        raise RuntimeError(f"{slug}: empty body (article container not found?)")

    annotations: dict[int, Annotation] = {}
    fig_annotations: dict[int, Annotation] = {}
    if annotator is not None:
        annotations = annotate_images(post, index, annotator, workdir, keep_images)
        fig_annotations = annotate_figures(post, index, annotator, workdir)

    out_path = posts_dir / f"{file_stem(slug)}.md"
    write_post_markdown(post, annotations, fig_annotations, out_path)
    arch = sum(1 for a in [*annotations.values(), *fig_annotations.values()] if a.verdict == VERDICT_ARCH)
    total = len(post.images) + len(post.figures)
    index.upsert_post(post, out_path, total, arch, annotated=annotator is not None)
    return post, total, arch


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
        url_md5 = hashlib.md5(ref.src.encode("utf-8")).hexdigest()
        try:
            data = fetch(ref.fetch_url, binary=True)
        except RuntimeError as exc:
            reason = f"download failed: {exc}"
            results[ref.index] = Annotation("FAILED", reason=reason)
            # No bytes to hash, so the failure is keyed on the URL instead. This is the row
            # --retry-failed looks for; a plain rerun still skips the post as done.
            index.link_post_image(post.slug, ref.index, url_md5, ref.src)
            index.record_image(url_md5, ref.src, post.slug, "FAILED", "", reason, "fetch", "")
            continue
        index.clear_failure(url_md5)  # it downloads now; drop the stale failure row
        md5 = hashlib.md5(data).hexdigest()
        index.link_post_image(post.slug, ref.index, md5, ref.src)
        cached = index.get_image(md5)
        if cached is not None and cached["verdict"] in (VERDICT_ARCH, VERDICT_IGNORE, "SKIPPED"):
            logger.info("cache hit %s img %d (%s)", post.slug, ref.index, cached["verdict"])
            results[ref.index] = Annotation(cached["verdict"], body=cached["body"] or "", annotator=cached["annotator"])
            continue
        if any(md5 == m for _, _, m in todo):
            results[ref.index] = Annotation("DUP", reason=md5)  # same bytes twice in one post
            continue
        path = post_dir / f"img{ref.index:02d}.png"
        path.write_bytes(data)
        todo.append((ref, path, md5))

    def run(item: tuple[ImageRef, Path, str]) -> tuple[ImageRef, str, Annotation]:
        ref, path, md5 = item
        logger.info("codex: %s img %d/%d", post.slug, ref.index, len(post.images))
        ann = annotator.annotate(post, ref, path, post_dir)
        if not keep_images:
            path.unlink(missing_ok=True)
        return ref, md5, ann

    if todo:
        with ThreadPoolExecutor(max_workers=annotator.max_workers) as pool:
            for fut in as_completed([pool.submit(run, item) for item in todo]):
                ref, md5, ann = fut.result()
                results[ref.index] = ann
                # FAILED is recorded too, with its reason. It is not in the cache-hit list
                # below, so re-processing this post always retries it.
                index.record_image(
                    md5, ref.src, post.slug, ann.verdict, ann.body, ann.reason,
                    ann.annotator, annotator.model or "default",
                )
                logger.info("%s img %d -> %s", post.slug, ref.index, ann.verdict)

    by_md5 = {m: results[r.index] for r, _, m in todo}
    for idx, ann in list(results.items()):
        if ann.verdict == "DUP":
            results[idx] = by_md5.get(ann.reason, Annotation("FAILED", reason="dup source failed"))

    if not keep_images:
        shutil.rmtree(post_dir, ignore_errors=True)
    return results


def annotate_figures(
    post: ParsedPost, index: Index, annotator: CodexImageAnnotator, workdir: Path
) -> dict[int, Annotation]:
    """Same cache and concurrency as the image pass, keyed by the MD5 of the figure labels."""
    results: dict[int, Annotation] = {}
    todo: list[FigureRef] = []
    for fig in post.figures:
        cached = index.get_image(fig.md5)
        if cached is not None and cached["verdict"] in (VERDICT_ARCH, VERDICT_IGNORE, "SKIPPED"):
            logger.info("cache hit %s fig %d (%s)", post.slug, fig.index, cached["verdict"])
            results[fig.index] = Annotation(cached["verdict"], body=cached["body"] or "", annotator=cached["annotator"])
            continue
        todo.append(fig)

    if not todo:
        return results

    fig_dir = workdir / file_stem(post.slug)
    fig_dir.mkdir(parents=True, exist_ok=True)

    def run(fig: FigureRef) -> tuple[FigureRef, Annotation]:
        logger.info("codex: %s fig %d/%d (html diagram)", post.slug, fig.index, len(post.figures))
        return fig, annotator.annotate_figure(post, fig, fig_dir)

    with ThreadPoolExecutor(max_workers=annotator.max_workers) as pool:
        for fut in as_completed([pool.submit(run, fig) for fig in todo]):
            fig, ann = fut.result()
            results[fig.index] = ann
            if ann.verdict != "FAILED":
                index.record_image(
                    fig.md5, f"{post.url}#figure-{fig.index}", post.slug, ann.verdict,
                    ann.body, ann.reason, ann.annotator, annotator.model or "default",
                )
            logger.info("%s fig %d -> %s", post.slug, fig.index, ann.verdict)

    shutil.rmtree(fig_dir, ignore_errors=True)
    return results


# --------------------------------------------------------------------------- index.md


def write_index_md(index: Index, out_path: Path) -> None:
    rows = index.list_posts()
    lines = [
        "# OpenAI engineering blog harvest",
        "",
        "Generated by `harvest.py`. Metadata lives in `index.db` (sqlite); one markdown file per post in `posts/`.",
        "",
        "| Published | Title | Diagrams | Arch |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['published'] or ''} | [{r['title']}]({r['md_path']}) | {r['image_count']} | {r['arch_count']} |")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--category", default=DEFAULT_CATEGORY, help="openai.com news category (default: engineering)")
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
    ap.add_argument("--retry-failed", action="store_true",
                    help="also re-process posts whose images failed to download or annotate")
    ap.add_argument("--dry-run", action="store_true", help="print the slugs this run would process, then exit")
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

    catalog = {m.slug: m for m in load_catalog(args.category)}
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
        retry = set(index.failed_slugs()) if args.retry_failed else set()
        slugs = [s for s in slugs if s in retry or not index.has_post(s, need_annotated=annotator is not None)]
        logger.info(
            "%d posts selected, %d already harvested, %d to do%s",
            before, before - len(slugs), len(slugs),
            f" ({len(retry & set(slugs))} retried for failed images)" if retry else "",
        )
    if args.limit is not None:
        slugs = slugs[: args.limit]

    if args.dry_run:
        for slug in slugs:
            print(slug)
        logger.info("dry run: %d posts would be processed", len(slugs))
        return 0

    workdir_ctx = tempfile.TemporaryDirectory(prefix="openai-harvest-") if args.workdir is None else None
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
                logger.info("wrote posts/%s.md (%d diagram candidates, %d architecture)", file_stem(slug), n_img, n_arch)
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
    raise SystemExit(main())
