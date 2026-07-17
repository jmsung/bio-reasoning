---
name: wiki-ingest
description: Ingest an artifact (paper, web page, repo, talk) into knowledge/source/ as a single distilled page. Human-gated.

argument-hint: [--type <type>] <url-or-path>
---

Ingest an external artifact: read it, draft a distilled summary, and (on user approval) write a single page at `knowledge/source/<slug>.md`. The **local** `source/` is flat — type lives in frontmatter (`source_type:`), not folders.

**Human-gated.** The skill reads the source, drafts the distillation, and **proposes** the write. Nothing lands without per-artifact approval.

**Knowledge layers** (full spec in `knowledge/wiki/README.md`):

| Layer | Job | Written by |
|---|---|---|
| `knowledge/raw/` | Native originals (PDF, HTML) | gitignored — local cache |
| `knowledge/source/` | Flat, local ingest front door — one distilled markdown per artifact | this skill (`/wiki-ingest`) |
| `knowledge/domains/<domain>/source/` | **Read-only synced mirror** of the central `knowledge-base` (per domain) | `/knowledge-sync` + `promote` — **NOT this skill** |
| `knowledge/wiki/` | Hand-curated synthesis (findings, methods, decisions, concepts) | humans + `/wiki-learn` + `/wiki-query --file-back` |

**This skill writes ONLY to the flat `knowledge/source/`.** It must **never** write into
`knowledge/domains/**` — that tree is a read-only mirror synced down from the central
`knowledge-base` repo (each page marked `<!-- synced from knowledge-base — do not edit here -->`);
anything written there is clobbered by the next `/knowledge-sync`. Durable pages reach `domains/`
via the separate **ingest-flat → human-gated `promote` → sync-down** lifecycle, not here.
Synthesis pages in `knowledge/wiki/` are also not created here.

> **Mid-migration note (2026-07):** the domains/ layout + knowledge-base subscription are
> still rolling out. Keep ingesting flat as normal; promotion to `domains/` happens out-of-band.

**Raw artifacts go to Drive** (`02-papers/`, `01-challenge/`, etc.), not the repo. Cite the Drive link from the source page's `drive:` field. `knowledge/raw/` is a local cache — gitignored.

Steps:

## 1. Resolve paths

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Not inside a git checkout — /wiki-ingest needs the repo root to find knowledge/source/." >&2
  exit 1
}
SOURCE="$REPO_ROOT/knowledge/source"
WIKI="$REPO_ROOT/knowledge/wiki"
[ -d "$SOURCE" ] || {
  echo "knowledge/source/ does not exist. See $WIKI/README.md for the 3-layer setup." >&2
  exit 1
}
```

Parse arguments: optional `--type <type>`, required `<url-or-path>`.

## 2. Determine source type

Infer from the `<url-or-path>` argument:

| Pattern | Type |
|---|---|
| `arxiv.org/*`, `*.pdf` URL with academic context | `papers` |
| `github.com/<org>/<repo>` (top-level repo) | `repos` |
| `gist.github.com/*` | `web` (it's a writeup, not source code) |
| `youtube.com/*`, `youtu.be/*`, `vimeo.com/*` | `talks` |
| `*.notion.so/*` | `notion` |
| `*.slack.com/*` | `slack` |
| any other `http(s)://` URL | `web` |
| local `.pdf` | ask; default `papers` |
| local `.md`, `.txt`, `.html` | ask user |

If `--type <type>` was given, use it. Valid types: `papers`, `web`, `repos`, `talks`, `notion`, `slack`.

## 3. Read source

- **URL:** use `WebFetch`. If it fails (paywall, auth, 4xx/5xx), ask the user to provide a local copy or paste relevant text.
- **Local PDF:** `Read` with `pages: "1-3"` for metadata (title, author, year). If the body is needed for distillation, `Read` more pages or ask the user to convert to markdown first (`pandoc` or open-the-PDF-and-paste). The skill does NOT store raw PDFs in `knowledge/source/` — those go to Drive, optionally cached in `knowledge/raw/` (gitignored).
- **Local `.md` / `.txt` / `.html`:** `Read` directly.

Extract: **title**, **author / source**, **date**.

## 4. Derive filename

Filename stem rules:
- All lowercase-kebab.
- ≤ 60 chars.
- No spaces, no special chars except `-`.

Per-type conventions:

| Type | Stem template |
|---|---|
| `papers` | `<year>-<firstAuthor>-<slug>` (e.g. `2025-edwards-bioreasoning-overview`) |
| `repos` | `<org>-<repo>` (e.g. `tobi-qmd`) |
| `talks` | `<venue>-<year>-<speaker>-<slug>` |
| `web` | `<domain>-<slug>` or `<author>-<slug>` for personal sites |
| `notion`, `slack` | `<channel-or-page>-<slug>` |

Target path: `knowledge/source/<stem>.md` (flat — no type subfolder).

## 5. Dedup check

```bash
TARGET="$SOURCE/<stem>.md"
# Also check the synced domains/ mirror — a paper may already exist there (promoted
# earlier) even if the flat copy was retired. Re-ingesting a synced page is a no-op waste.
DOMAIN_HIT=$(find "$REPO_ROOT/knowledge/domains" -path '*/source/<stem>.md' 2>/dev/null | head -1)
if [ -f "$TARGET" ] || [ -n "$DOMAIN_HIT" ]; then
  echo "Page already exists: ${TARGET:-$DOMAIN_HIT}${DOMAIN_HIT:+ (synced mirror — edit upstream, don't re-ingest)}"
  echo "Choose: [s]kip / [o]verwrite / [v]new-version (append -v2 to stem)"
  read CHOICE
fi
```

Beyond the exact-stem check, also scan for a **title/DOI** match across both `source/` and
`domains/**/source/` (stems can differ for the same paper) — if a match surfaces, prefer `s`kip.

- **`s`** → stop. No writes.
- **`o`** → continue to step 6 with existing stem. Never overwrite a `domains/` mirror page.
- **`v`** → re-derive stem with `-v2` suffix (or `-v3` if `-v2` exists).

No collision in either layer → continue.

## 6. Draft distillation

Apply the per-type template from "Distillation templates" below. Produce a ~300–600 word distilled markdown body.

## 7. Propose

Print:

```
Proposed ingest:
  Source: <URL or path>
  Type:   <type>
  Target: knowledge/source/<stem>.md

  Preview:
    ---
    source_url: <url or "local file: <path>">
    source_type: <type>
    title: <title>
    author: <author>
    retrieved: <YYYY-MM-DD>
    ---

    # <title>

    <distilled body — first ~6 lines>
    ...

Approve? [y / n / edit]
```

- **`n`** → stop.
- **`edit`** → ask which fields to change (filename, type, frontmatter, body). Re-derive and re-prompt.
- **`y`** → proceed to step 8.

This approval gate is mandatory. Never skip.

## 8. Write the page

```bash
# Write $SOURCE/<stem>.md with frontmatter + body. $SOURCE already exists; no mkdir.
```

Frontmatter shape:

```yaml
---
source_url: <url or "local file: <path>">
source_type: <type>
title: <title>
author: <author>          # optional when no clear author
retrieved: <YYYY-MM-DD>
drive: <drive-link>       # optional — link to raw artifact in Drive
license: <license>        # optional, for repos
---
```

## 9. Update index.md

Add an entry to `$WIKI/index.md` under the appropriate `### <type>` heading within the `## source/` section. Create the heading if it doesn't exist.

Entry format:
```
- [<title>](../source/<stem>.md) — <domain or org> · <YYYY-MM-DD>
```

## 10. Append to log.md

```bash
cat >> "$WIKI/log.md" <<EOF

## <YYYY-MM-DD> — Ingested source/<stem>
- Source: <URL or local path>
- Type: <type>
EOF
```

## 11. Re-index (optional)

If qmd is available:

```bash
# Pinned for this repo — see the note in wiki-query/SKILL.md on why the generic
# basename-derivation misfires under the umbrella layout. `bio-reasoning` is also on
# the harness skills' legacy-fallback list, so this stays forward-compatible.
QMD_COLLECTION="bio-reasoning"
command -v qmd >/dev/null && qmd collection list --json 2>/dev/null | \
  grep -q "\"$QMD_COLLECTION\"" && qmd embed -c "$QMD_COLLECTION"
```

Skip silently if qmd or the collection is unavailable.

## 12. Commit

```bash
cd "$REPO_ROOT"
git add "knowledge/source/<stem>.md" knowledge/wiki/index.md knowledge/wiki/log.md
git commit -m "docs(source): ingest <stem>"
```

## Distillation templates

Apply the template matching the artifact's `<type>`. Distillations should be self-contained — readable without the original — and dense.

### papers

```markdown
# <title>

**Authors:** <full author list>
**Year:** <year>
**Venue:** <venue / journal / arxiv>

## Abstract

<1 paragraph; rewrite for clarity if needed>

## Key contributions

- <contribution 1: one line>
- <contribution 2>
- ...

## Methods

<1–2 paragraphs: what the paper actually does. Skip if abstract covers it.>

## Key results

- <result 1 with magnitude / metric>
- <result 2>
- ...

## Why it matters for our work

<1 paragraph: how this connects to the BioReasoning Challenge or our methods>

## Limitations / open questions

- <limitation 1>
- ...
```

### web

```markdown
# <title>

**Source:** <domain> · <YYYY-MM-DD>
**Author:** <author or "—">

## TL;DR

<1–2 sentences>

## Key claims

- <claim 1>
- ...

## Why it matters for our work

<1 sentence>
```

### repos

```markdown
# <org>/<repo>

**Language:** <primary language>
**License:** <license>

## What it is

<1 paragraph>

## Key features

- <feature 1>
- ...

## Relevant techniques

- <technique 1>
- ...

## Why it matters for our work

<1 paragraph>
```

### talks

```markdown
# <talk title>

**Speaker:** <speaker>
**Venue:** <venue> · <YYYY>

## Summary

<1 paragraph: what the talk argues>

## Key claims

- <claim 1>
- ...

## References cited

- <reference 1>
- ...
```

### notion / slack

```markdown
# <document or thread title>

**Source:** #<channel> or <page-name> · <YYYY-MM-DD>
**Participants:** <list>

## Summary

<1 paragraph>

## Decisions / takeaways

- <takeaway 1>
- ...

## Action items

- <person>: <action>, due <when>
- ...
```

## What this skill does NOT do

- **Does not write to `knowledge/wiki/`** (except `index.md` + `log.md`). Synthesis pages are hand-curated, or via `/wiki-learn` / `/wiki-query --file-back`.
- **Does not save raw artifacts in git.** PDFs / large files go to Drive — link to them via `drive:` in frontmatter. Local `knowledge/raw/` cache is gitignored.
- **Does not auto-ingest.** Approval per artifact is mandatory.
- **Does not scan for cross-references.** Use `/wiki-lint` later to find and add them.

## Rules

- **Human-gated.** Step 7's approval gate is mandatory.
- **One source page per artifact.** Don't try to combine multiple sources in one page — make separate pages and cross-link.
- **Cite the source URL or path** in `source_url:` — every page must trace back to its origin.
- **`knowledge/source/` holds distilled markdown only.** Raw artifacts go to Drive (optionally cached in `knowledge/raw/`, gitignored).
- If WebFetch fails, ask the user for a local copy or pasted text.
