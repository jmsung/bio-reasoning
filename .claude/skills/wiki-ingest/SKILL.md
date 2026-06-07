---
name: wiki-ingest
description: Ingest an artifact (paper, web page, repo, talk) into the team wiki as a single distilled page. Human-gated.

argument-hint: [--type <type>] <url-or-path>
---

Ingest an external artifact: read it, draft a distilled summary, and (on user approval) write a single page at `docs/wiki/<type>/<slug>.md`.

**Human-gated.** The skill reads the source, drafts the distillation, and **proposes** the write. Nothing lands without per-artifact approval.

**Raw artifacts go to Drive, not the repo.** Drop the PDF / screenshot / etc. into the team Drive (`02-papers/`, `01-challenge/`, etc.) and cite the Drive link from the wiki page. The wiki holds **distilled, cited markdown only**.

Steps:

## 1. Resolve wiki path

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Not inside a git checkout — /wiki-ingest needs the repo root to find docs/wiki/." >&2
  exit 1
}
WIKI="$REPO_ROOT/docs/wiki"
[ -d "$WIKI" ] || {
  echo "docs/wiki/ does not exist. See $WIKI/README.md for setup." >&2
  exit 1
}
```

Parse arguments: optional `--type <type>`, required `<url-or-path>`.

## 2. Determine source type

Infer from the `<url-or-path>` argument:

| Pattern | Type |
|---|---|
| `arxiv.org/*`, `*.pdf` URL with academic context | `papers` |
| `github.com/*`, `gitlab.com/*` | `repos` |
| `youtube.com/*`, `youtu.be/*`, `vimeo.com/*` | `talks` |
| any other `http(s)://` URL | `web` |
| local `.pdf` | ask; default `papers` |
| local `.md`, `.txt`, `.html` | ask user |

If `--type <type>` was given, use it. Valid types: `papers`, `web`, `repos`, `talks`, `methods`, `decisions`.

## 3. Read source

- **URL:** use `WebFetch`. If it fails (paywall, auth, 4xx/5xx), ask the user to provide a local copy or paste relevant text.
- **Local PDF:** `Read` with `pages: "1-3"` for metadata (title, author, year). If the body is needed for distillation, `Read` more pages or ask the user to convert to markdown first (`pandoc` or open-the-PDF-and-paste). The wiki does NOT store raw PDFs — those go to Drive.
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
| `repos` | `<org>-<repo>` |
| `talks` | `<venue>-<year>-<speaker>-<slug>` |
| `web` | `<domain>-<slug>` |
| `methods`, `decisions` | `<slug>` |

Target path: `docs/wiki/<type>/<stem>.md`.

## 5. Dedup check

```bash
TARGET="$WIKI/<type>/<stem>.md"
if [ -f "$TARGET" ]; then
  echo "Page already exists: $TARGET"
  echo "Choose: [s]kip / [o]verwrite / [v]new-version (append -v2 to stem)"
  read CHOICE
fi
```

- **`s`** → stop. No writes.
- **`o`** → continue to step 6 with existing stem.
- **`v`** → re-derive stem with `-v2` suffix (or `-v3` if `-v2` exists).

No filename collision → continue.

## 6. Draft distillation

Apply the per-type template from "Distillation templates" below. Produce a ~300–600 word distilled markdown body.

## 7. Propose

Print:

```
Proposed ingest:
  Source: <URL or path>
  Type:   <type>
  Target: docs/wiki/<type>/<stem>.md

  Preview:
    ---
    title: <title>
    cites:
      - <url or path>
    source_type: <type>
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
mkdir -p "$WIKI/<type>"
# Write $WIKI/<type>/<stem>.md with frontmatter + body
```

Frontmatter shape:

```yaml
---
title: <title>
cites:
  - <url or path>
source_type: <type>
author: <author>          # optional for web/methods/decisions
retrieved: <YYYY-MM-DD>
drive: <drive-link>       # optional — link to raw artifact in Drive
---
```

## 9. Update index.md

Add an entry to `$WIKI/index.md` under the appropriate `## <type>` section. Create the section if it doesn't exist.

## 10. Re-index (optional)

If qmd is available:

```bash
PROJECT=$(basename "$REPO_ROOT" | sed 's/-cb-.*//; s/^cb-//')
QMD_COLLECTION="${PROJECT}-wiki"
command -v qmd >/dev/null && qmd collection list --json 2>/dev/null | \
  grep -q "\"$QMD_COLLECTION\"" && qmd embed -c "$QMD_COLLECTION"
```

Skip silently if qmd or the collection is unavailable.

## 11. Commit

```bash
cd "$REPO_ROOT"
git add "docs/wiki/<type>/<stem>.md" docs/wiki/index.md
git commit -m "docs(wiki): ingest <type>/<stem>"
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

### methods

```markdown
# <method name>

## What we did

<1 paragraph>

## Why this approach

<1 paragraph: the rationale, what alternatives we considered>

## Results

- <metric / observation 1>
- ...

## What we learned

- <takeaway 1>
- ...
```

### decisions

```markdown
# <decision title>

**Date:** <YYYY-MM-DD>
**Status:** <accepted / superseded / rejected>

## Context

<1 paragraph: what problem we were solving>

## Decision

<1 paragraph: what we decided>

## Rationale

- <reason 1>
- ...

## Consequences

- <consequence 1>
- ...
```

## What this skill does NOT do

- **Does not save raw artifacts in the repo.** PDFs / screenshots / large files go to Drive — link to them via `drive:` in frontmatter.
- **Does not auto-ingest.** Approval per artifact is mandatory.
- **Does not scan for cross-references.** Use `/wiki-lint` later to find and add them.

## Rules

- **Human-gated.** Step 7's approval gate is mandatory.
- **One page per artifact.** Don't try to combine multiple sources in one page — make separate pages and cross-link.
- **Cite the source URL or path** in `cites:` — every wiki page must trace back to its source.
- **`docs/wiki/` holds distilled markdown only.** Raw artifacts go to Drive.
- If WebFetch fails, ask the user for a local copy or pasted text.
