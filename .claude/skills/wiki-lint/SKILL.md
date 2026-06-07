---
name: wiki-lint
description: Lint the team wiki — find orphans, stale claims, missing cites, and contradictions.

argument-hint: [--fix]
---

Lint the team wiki at `docs/wiki/` for health issues — orphan pages, broken cross-references, missing cites, and contradictions.

Steps:

## 1. Resolve wiki path

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Not inside a git checkout — /wiki-lint needs the repo root to find docs/wiki/." >&2
  exit 1
}
WIKI="$REPO_ROOT/docs/wiki"
[ -d "$WIKI" ] || {
  echo "docs/wiki/ does not exist. See $WIKI/README.md for setup." >&2
  exit 1
}
```

Parse `--fix` flag — without it the skill only reports.

## 2. Inventory

1. Read `$WIKI/index.md` to get the expected page list.
2. Glob `$WIKI/**/*.md` to get the actual page list.
3. Build a map of all pages with their frontmatter (`title:`, `cites:`).

## 3. Check: Orphans

Pages that exist on disk but are NOT listed in `index.md`:

- List each orphan with its path.
- If `--fix`: add missing entries to `index.md` under the appropriate section.

## 4. Check: Broken cites

For each page's `cites:` list, verify the target file exists:

- List each broken cite with source page and target path.
- If `--fix`: remove broken cites from frontmatter.

## 5. Check: Body links without frontmatter cites

For each page, scan its body for `[[cross-directory]]` wiki links (e.g., `[[papers/foo]]`, `[[findings/bar]]`). Every such link MUST have a matching entry in the page's `cites:` frontmatter:

- List each missing cite with: source page, body link target, expected `cites:` entry.
- If `--fix`: add the missing `cites:` entry to the page's frontmatter.
- Ignore same-directory links (siblings don't need explicit cites).

This is the most common oversight — authors add inline links but forget to update frontmatter.

## 6. Check: Missing cross-references

For each page, scan its content for references to concepts covered by other pages that are NOT in its `cites:` list:

- List candidate missing cites (source → suggested target).
- If `--fix`: ask user to confirm before adding cites.

## 7. Check: Contradictions

For pages on overlapping topics, scan for conflicting claims:

- Compare key assertions across pages.
- List each contradiction with: page A claim, page B claim, recommended action.
- Do NOT auto-fix contradictions — always report for human review.

## 8. Report

Print a summary:

```
Wiki lint for docs/wiki/:
  Pages:           N total, M in index
  Orphans:         N (fixed: M)
  Broken cites:    N (fixed: M)
  Body link gaps:  N (fixed: M)
  Missing cites:   N candidates
  Contradictions:  N (requires human review)
```

## 9. Commit (if `--fix` was used)

```bash
cd "$REPO_ROOT"
git add docs/wiki/
git commit -m "docs(wiki): lint — fix N orphans, N broken cites, N body link gaps"
```

Only mention categories that had fixes applied (omit zeros). If nothing was changed, skip silently.

Rules:
- Never auto-fix contradictions — always report for human review.
- Broken cites, orphans, and body link gaps are safe to auto-fix with `--fix`.
- Missing cross-references require user confirmation before adding.
- All `cites:` paths are **wiki-root-relative** (from `docs/wiki/`), never file-relative.
