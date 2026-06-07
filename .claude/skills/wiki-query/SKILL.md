---
name: wiki-query
description: Query the team wiki — search, synthesize, and optionally file the answer back as a page.

argument-hint: <question>
---

Query the team wiki at `knowledge/wiki/` — search relevant pages, synthesize a cited answer, and optionally file it back as a new page.

Steps:

## 1. Resolve wiki path

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Not inside a git checkout — /wiki-query needs the repo root to find knowledge/wiki/." >&2
  exit 1
}
WIKI="$REPO_ROOT/knowledge/wiki"
[ -d "$WIKI" ] || {
  echo "knowledge/wiki/ does not exist. See $WIKI/README.md for setup (or create it)." >&2
  exit 1
}
[ -f "$WIKI/index.md" ] || {
  echo "knowledge/wiki/index.md missing — the wiki hasn't been initialized." >&2
  exit 1
}
```

Read `$WIKI/home.md` (if it exists) for project orientation before searching.

## 2. Search

### Primary: qmd hybrid search (if available)

If the `qmd` CLI is on PATH AND a collection is registered for this project, use it for hybrid (BM25 + vector + LLM rerank) search:

```bash
PROJECT=$(basename "$REPO_ROOT" | sed 's/-cb-.*//; s/^cb-//')   # strip worktree prefix
QMD_COLLECTION="${PROJECT}-wiki"
if command -v qmd >/dev/null 2>&1 && qmd collection list --json 2>/dev/null | grep -q "\"$QMD_COLLECTION\""; then
  qmd query "<question>" -c "$QMD_COLLECTION" -n 10 --json --files
fi
```

Parse the JSON to get ranked file paths and scores. For each result above `min-score 0.3`, read the full page content.

### Fallback: index.md + grep

If qmd is not available or no collection is registered:

1. Read `$WIKI/index.md` to get the page catalog.
2. Identify candidate pages relevant to the question using titles, descriptions, and directory structure.
3. `grep -r` across BOTH `$WIKI/**/*.md` and `$REPO_ROOT/knowledge/source/**/*.md` for question keywords — the wiki layer indexes the source layer, so search both.
4. Read each candidate page to gather relevant content.

### Follow cites (both paths)

5. Follow `cites:` links from candidate pages to find related pages (one hop). This catches connections that search alone may miss.

## 3. Synthesize

1. Synthesize an answer from the gathered pages.
2. Cite sources inline: `(see [page](path))` for each claim.
3. Note any gaps: questions the wiki cannot answer, or areas where pages conflict.
4. If conflict exists, flag it — don't silently pick one.

## 4. File back (optional)

Ask the user: "File this answer into the wiki?"

If yes:
1. Determine the appropriate location in `$WIKI/` — `findings/` for cross-cutting synthesis, `methods/` for methods we tried, `decisions/` for decisions with rationale, `concepts/` for cross-source entity pages. (Source layer `knowledge/source/` is flat and per-artifact — file-back never writes there; use `/wiki-ingest` to add a source page.)
2. Create the page with frontmatter:
   ```yaml
   ---
   title: <answer title>
   cites:
     - <path or url>
   ---
   ```
3. Update `$WIKI/index.md` with the new entry.
4. If qmd is available, re-index: `qmd embed -c $QMD_COLLECTION`.

If no: print the answer and stop.

## 5. Commit (if filed back)

```bash
cd "$REPO_ROOT"
git add "knowledge/wiki/<new-page-path>" knowledge/wiki/index.md
git commit -m "docs(wiki): query \"<short question>\" — filed as <path>"
```

If nothing was filed back, skip silently.

Rules:
- Prefer qmd hybrid search over grep when available — it finds semantically related pages keyword matching misses.
- Always follow `cites:` links after search — the wiki graph has connections search alone won't find.
- Cite every claim back to its source page.
- If the wiki lacks sufficient information, say so — don't hallucinate beyond what the pages contain.
- Filing back is the compounding mechanism — encourage it for reusable answers.
