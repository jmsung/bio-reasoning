---
name: wiki-learn
description: Distill conversation insights into the team wiki — turn exploration and Q&A into compounding knowledge.
---

Distill insights from the current conversation into the team wiki at `knowledge/wiki/`. Turns exploratory Q&A, research, and study sessions into permanent, searchable pages.

This is the conversation → wiki compounding loop. Without it, knowledge gained through conversation is lost when the session ends.

Steps:

## 1. Resolve wiki path

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Not inside a git checkout — /wiki-learn needs the repo root to find knowledge/wiki/." >&2
  exit 1
}
WIKI="$REPO_ROOT/knowledge/wiki"
[ -d "$WIKI" ] || {
  echo "knowledge/wiki/ does not exist. See $WIKI/README.md for setup." >&2
  exit 1
}
```

Read `$WIKI/home.md` (if it exists) for project orientation.

## 2. Extract insights

Scan the current conversation for knowledge worth persisting:

1. **Answers to questions** — substantive answers that synthesize understanding (not one-liners).
2. **Research findings** — domain knowledge discovered through web search or paper reading.
3. **Design decisions** — architectural choices with rationale (why X over Y).
4. **Debugging insights** — root causes, non-obvious failure modes, workarounds.
5. **Patterns discovered** — techniques or approaches that generalize beyond this session.

For each insight, note:
- The core claim or finding (1–3 sentences).
- Supporting evidence or source (conversation context, URLs, papers).
- Which existing wiki pages it relates to.

Present the list to the user: "I found N insights worth filing. Here they are — confirm, edit, or skip any."

## 3. Classify and route

For each confirmed insight, determine where it goes. Default routing:

| Type | Destination |
|---|---|
| Cross-cutting synthesis answering a specific question | `findings/<slug>.md` |
| Concept, principle, or mental model | `concepts/<slug>.md` |
| Distilled paper / source summary | `papers/<slug>.md` |
| Method we tried, with rationale | `methods/<slug>.md` |
| Decision with rationale | `decisions/<slug>.md` |
| Append to an existing page | (target page) |

Subdirectories grow as needed — don't pre-create empty ones.

Check existing pages first — prefer appending over creating new pages. Use qmd search if available:

```bash
PROJECT=$(basename "$REPO_ROOT" | sed 's/-cb-.*//; s/^cb-//')
QMD_COLLECTION="${PROJECT}-wiki"
if command -v qmd >/dev/null 2>&1 && qmd collection list --json 2>/dev/null | grep -q "\"$QMD_COLLECTION\""; then
  qmd query "<insight summary>" -c "$QMD_COLLECTION" -n 5 --json
fi
```

Otherwise grep `$WIKI/**/*.md` for related concepts.

## 4. Write to wiki

For each routed insight:

### If appending to an existing page:
1. Read the target page.
2. Append the insight under an appropriate heading.
3. Update `cites:` frontmatter if the insight references other wiki pages.

### If creating a new page:
1. Create at the classified path with frontmatter:
   ```yaml
   ---
   title: <human title>
   cites:
     - <path or url>
   ---
   ```
2. Scan for cross-references — other pages that should cite this one.
3. Add bidirectional `cites:` links.

### Always:
4. Update `$WIKI/index.md` (add new pages, update descriptions if existing pages gained significant content).

## 5. Re-index (optional)

If qmd is available:

```bash
qmd embed -c "$QMD_COLLECTION"
```

Skip silently if qmd is not installed or no collection is registered.

## 6. Report

Print a summary:

```
Wiki-learn complete:
  Insights extracted: N
  New pages: <list with paths>
  Updated pages: <list with paths>
  Cross-references added: N
```

## 7. Commit

```bash
cd "$REPO_ROOT"
git add knowledge/wiki/
git commit -m "docs(wiki): learn <session topic>

New pages: <list or \"none\">
Updated pages: <list or \"none\">
Insights filed: N"
```

If nothing to commit, skip silently.

Rules:
- Present insights to user before writing — don't silently modify the wiki.
- Prefer appending to existing pages over creating new ones — avoid page sprawl.
- Every insight must have a source attribution (conversation, URL, paper, experiment).
- This skill is for conversation-sourced knowledge — use `/wiki-ingest` for papers/URLs, `/wiki-query` for explicit questions.
- The value is in the compounding: knowledge from exploration becomes permanent, searchable, cross-referenced.
