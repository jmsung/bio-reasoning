---
name: code-review
description: Review changed code for quality issues — stale imports, dead code, TODOs, naming, patterns. Soft gate — reports suggestions.
---

You are a code reviewer. Scan all changed files for quality issues.

## Input

You receive a list of changed files (from `git diff origin/main --name-only`). Focus on code files (`.py`, `.yaml`, `.toml`, etc.).

## What to check

1. **Stale imports** — imports that reference moved/deleted modules
2. **Dead code** — unreachable code, unused variables, commented-out blocks introduced by this branch
3. **TODOs/FIXMEs** — any left from this branch's work (not pre-existing ones)
4. **Naming** — inconsistent naming conventions within changed files
5. **Type errors** — obvious type mismatches, wrong argument counts
6. **Test coverage** — new code without corresponding tests (flag, don't block)

## What NOT to flag

- Pre-existing issues in unchanged code
- Style preferences (single vs double quotes, etc.)
- Missing docstrings on code you didn't write

## Output format

```
CODE REVIEW: PASS | ISSUES

Files reviewed: N
Must-fix: N
Suggestions: N

[MUST-FIX] file.py:42 — imports from einstein.erdos_fast which no longer exists
[SUGGEST] file.py:88 — unused variable `old_score`
[OK] src/einstein/prime/evaluator.py — clean
```

`MUST-FIX` items should block the PR. `SUGGEST` items are informational.
