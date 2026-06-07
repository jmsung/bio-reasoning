---
name: pr-open
description: Run all pre-PR checks, push the branch, open the PR, and tick matching roadmap items with (#N). Stops at human squash-merge.

disable-model-invocation: true
---

Runs the full PR-time gate before main: rebase → checks → 4 parallel
reviews → push → `gh pr create` → update `docs/roadmap.md` with `(#N)`.
**Does not auto-merge** — the human clicks "Squash and merge" in the
GitHub UI.

Pairs with [`/pr-merge`](../pr-merge/SKILL.md) (post-merge cleanup) and
[`/dev-setup`](../dev-setup/SKILL.md) (one-time onboarding). See
`knowledge/wiki/decisions/0001-pr-workflow.md` for the 3-gate model.

## Steps

### 1. Verify state

```bash
REPO=$(git rev-parse --show-toplevel) || { echo "Not in a git repo." >&2; exit 1; }
BRANCH=$(git -C "$REPO" branch --show-current)
[ "$BRANCH" = "main" ] && { echo "Refusing to open PR from main." >&2; exit 1; }
```

Find the branch's tracking file at `mb/active/<slug>.md` (slug =
`BRANCH` with `/` → `-`). Read it once. If missing, abort with: "No
`mb/active/<slug>.md` — start the branch with `/worktree-start`."

Verify every `# Goals` entry is `[x]`. If any `[ ]` remain, list them
and abort: "Unfinished goals — finish or `/revise` before opening PR."

### 2. Rebase on main

```bash
git -C "$REPO" fetch origin
git -C "$REPO" rebase origin/main
```

If rebase conflicts, stop and surface — never `--force` or `--abort`
silently. User resolves, then re-runs `/pr-open`.

### 3. Run local checks

In order, abort on first failure:

```bash
uv run pre-commit run --all-files     # full hook sweep, not just staged
uv run pytest -q                       # tests
uv run mypy                            # type check (config in pyproject.toml)
```

If any step fails, print the failure verbatim and stop. Do not push.

### 4. Quality gate — 4 reviews in parallel

Run these as parallel subagents (they're independent reports):

| Review | Tool / Agent | What it catches |
|---|---|---|
| Code review | `/code-review` (default effort) | bugs, reuse, simplification, efficiency in the diff |
| Security audit | `@security-audit` agent | secrets, leaks, injection, auth/authz (HARD gate — reads project CLAUDE.md for scope) |
| Docs status | `@docs-review` agent | README + `docs/` drift vs the code changes; auto-fixes committed locally |
| Wiki health | `/wiki-lint` | orphans, broken cites, missing cross-refs in `knowledge/wiki/` |

(`@distill` is opt-in via `/worktree-done` or manual invocation — not run
per-PR. It's compounding-value-when-present, not essential-per-PR.)

**Why a mix of `/skill` and `@agent`?** Forced by what exists in the harness:
`/wiki-lint` has no agent form; `@docs-review` has no skill form. For
`code-review` and `security` (both available as either), the skill form is
used when interactive findings benefit from the user reviewing inline; the
agent form is used when parallel speed and a harder gate matter (security).

Aggregate the findings into one block grouped by source. Two outcomes:

- **No blocking issues / user accepts as-is** → continue to step 4.
- **Issues to fix** → ask the user to address (with you or manually).
  After fixes are committed, return to step 2.

Severity bar for "blocking":
- Code review: any CONFIRMED bug or unhandled correctness finding.
- Security: any leaked secret, auth bypass, or injection sink (HARD block — never push).
- Wiki: broken cites or orphans that touch a page this PR modifies (otherwise informational).
- Docs: any stale claim that contradicts the merged behavior (e.g., command renamed but README still shows old form).

User can override informational findings; never override security.

### 4. Push the branch

```bash
git -C "$REPO" push -u origin "$BRANCH"
```

If push is rejected (non-fast-forward), abort and surface — never
`--force` from this skill.

### 5. Open the PR

Extract `PR_TITLE` and `PR_BODY` from `mb/active/<slug>.md` (between the
`<!-- PR_TITLE -->` and `<!-- PR_BODY -->` markers). If either is empty,
abort: "Missing PR_TITLE or PR_BODY in tracking file."

If a PR already exists for this branch (re-open or update flow):

```bash
PR_NUM=$(gh pr view --json number -q .number 2>/dev/null)
```

- **No existing PR** → `gh pr create --title "<PR_TITLE>" --body "<PR_BODY>"`.
  Parse `PR_NUM` from the URL `gh` prints.
- **Existing PR** → skip creation; just continue.

### 6. Tick matching roadmap items with (#N)

Read `docs/roadmap.md`. Identify which `- [ ]` items this PR closes —
this is a judgment call:

1. List every `- [ ]` line in `docs/roadmap.md`'s Todo section.
2. Read the PR body's Summary bullets.
3. Suggest matches: "PR #N closes roadmap items 1, 5 — confirm? [y/n/edit]"
4. On `y`: rewrite the matched `- [ ] **Item**` → `- [x] (#N) **Item**`.
   Preserve the rest of the line verbatim.
5. On `edit`: ask which items to tick.

If no items match (skill PR, refactor, infrastructure), skip silently.

### 7. Commit + push the roadmap edit

If step 6 made any changes:

```bash
git -C "$REPO" add docs/roadmap.md
git -C "$REPO" commit -m "docs(roadmap): tick item(s) closed by #$PR_NUM"
git -C "$REPO" push origin "$BRANCH"
```

### 8. Report

Print:

```
PR opened: <URL>
Branch:    <branch>
Checks:    pre-commit ✓ pytest ✓ mypy ✓
Reviews:   code ✓ security ✓ docs ✓ wiki ✓
Roadmap:   ticked items <N, M> with (#<PR_NUM>) (or "none — non-roadmap PR")

Next: review in GitHub, then Squash-merge in the UI.
      After merge, run /pr-merge to archive + clean up.
```

## What this skill does NOT do

- **Does not call `gh pr merge`.** Human gate is mandatory.
- **Does not modify `main`.** Only edits the feature branch.
- **Does not `--force` push.** A rejected push is surfaced, not bypassed.
- **Does not skip checks.** No `--no-verify` shortcut.
- **Does not write to `mb/active/`.** The tracking file is owned by `/goal` / `/act` / `/revise`.

## Pause heuristics

Stop and surface to the user when:
- Tracking file is missing or has unfinished goals.
- Any check (pre-commit / pytest / mypy) fails.
- Any quality review (code / security / wiki / docs) surfaces a blocking
  finding per the severity bar above. Security findings are HARD blocks
  and cannot be overridden.
- `git push` is rejected.
- The roadmap-match step is ambiguous (no clear correspondence between PR
  summary and any roadmap item — ask, don't guess).
- `gh pr create` returns an error (auth, base-branch missing, etc.).
