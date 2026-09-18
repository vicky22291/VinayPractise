# Databricks engineering blog harvest

Study material pulled from the Databricks engineering blog. Every post becomes one
markdown file, and every architecture image in it becomes text plus a Mermaid diagram
(colored with the repo legend), so the whole thing is greppable and renders in GitHub.

```
databricks/
  harvest.py      the tool (stdlib only, shells out to the Codex CLI)
  index.db        sqlite: post metadata, per-image verdicts, image -> post links
  index.md        generated table of every harvested post (newest first)
  posts/<slug>.md one file per post
```

## How it works

```mermaid
%% One post through the harvester
flowchart LR
    CAT[Catalog JSON<br/>827 engineering posts]
    HTML[Post HTML]
    MD[Markdown with<br/>image placeholders]
    IMG[Image bytes<br/>in a temp dir]
    CX[codex exec -i image]
    DB[(index.db)]
    OUT[posts/slug.md]

    CAT -->|slug, title, date, authors| HTML
    HTML -->|article--content div| MD
    HTML -->|img src| IMG
    IMG -->|md5 lookup, miss| CX
    IMG -.->|md5 hit| DB
    CX -->|ARCHITECTURE or IGNORE| DB
    DB -->|verdict + text + mermaid| OUT
    MD --> OUT
    IMG -->|unlink after annotation| BIN[Deleted]

    classDef client   fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#111
    classDef service  fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef store    fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef cache    fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
    class CAT,HTML external
    class MD,OUT service
    class IMG cache
    class CX external
    class DB store
    class BIN cache
```

- **Listing.** The blog's category filter is client-side. The page loads
  `/en-blog-assets/data/blog/posts/engineering.json` (every post in the category, 2013 to
  today) and filters on the `categories=` query param. `harvest.py` reads the same file, so
  it never needs to paginate and gets title, subtitle, ISO date, authors and categories for free.
- **Body.** The `article--content` div is converted to markdown with a small
  `html.parser` subclass. Headings, lists, links, code, tables and figures are kept.
- **Images.** Each `<img>` becomes a `{{IMG:n}}` placeholder. Obvious decoration (logos, icons,
  svg, gif, anything under 150 px) is dropped without a model call. The rest are downloaded to a
  temp dir and sent one at a time to `codex exec -i <file>` with a prompt that asks for a first
  line of `ARCHITECTURE` or `IGNORE`, then summary, components, flows, numbers and a Mermaid
  block. `IGNORE` images are removed from the markdown. Image files are deleted once annotated.
- **Cache.** Verdicts are stored by image MD5 in `index.db`, so a rerun (or a second post that
  reuses the same image) costs nothing. Failed annotations are not cached, so they retry.

This mirrors `CodexAnnotator` in VQTS-Python (`doc_pipeline/annotation/image_annotator.py`):
one ephemeral Codex turn per image, verdict on the first line, MD5 cache, rate-limit retry.
The difference is transport: `codex exec` per image instead of a long-lived `codex app-server`.

## Running it

```bash
python3 databricks/harvest.py --since 2026-08            # recent posts only
python3 databricks/harvest.py --since 2025 --limit 20    # a bounded batch
python3 databricks/harvest.py                            # everything (827 posts, hours of codex)
python3 databricks/harvest.py --skip-codex               # markdown only, images left as links
python3 databricks/harvest.py --force --slug <slug>      # redo one post
python3 databricks/harvest.py --validate-mermaid         # render every diagram with mermaid-cli
python3 databricks/harvest.py --list                     # what is in index.db
```

Reruns are incremental: posts already in `index.db` are skipped unless `--force`.
Useful knobs: `--effort low|medium|high` (Codex reasoning), `--max-workers 3`
(parallel codex processes), `--timeout 240`, `--model`.

Requirements: Python 3.11+, the `codex` CLI on PATH and logged in. `--validate-mermaid`
uses `mmdc` if present, else `npx -y @mermaid-js/mermaid-cli`.

## Querying the index

```bash
sqlite3 databricks/index.db "select published, title from posts order by published desc limit 10"
sqlite3 databricks/index.db "select verdict, count(*) from images group by verdict"
sqlite3 databricks/index.db "select slug, arch_count from posts where arch_count >= 3 order by arch_count desc"
```

## Gotchas found while building it

- `codex exec` appends piped stdin to the prompt and blocks until EOF. Run it with
  `stdin=DEVNULL` or every call hangs to the timeout.
- `?page=N` on the listing URL is ignored when `categories=` is present. Server-side
  pagination only exists for the unfiltered category URL. Use the catalog JSON instead.
- The `text-blog-summary` class also appears inside inline `<style>`; anchor the regex on
  `<div class="` or you scrape CSS.
