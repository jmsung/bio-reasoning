---
title: PR-only workflow with squash-merge
date: 2026-06-06
status: accepted
cites:
  - ../../../docs/development.md
  - ../../../docs/roadmap.md
---

# 0001 — PR-only workflow with squash-merge

**Status:** accepted, partially enforced (see "Caveat" below).

## Decision

All changes to `main` land via Pull Request. The only allowed merge type
is **squash-merge**, performed manually in the GitHub UI. Branch
deletion is automatic on merge.

Three layered gates enforce quality before code reaches `main`:

| Gate | When | What runs |
|---|---|---|
| **Pre-commit hook** | every `git commit` | black, ruff (lint), mypy on `src/`, hygiene checks (trailing-whitespace, EOF, large files, etc.) — config in `.pre-commit-config.yaml` |
| **`/pr-open` skill** | branch → PR | full lint + typecheck + tests + `/code-review`, then push + `gh pr create` + tick matching roadmap items with `(#N)` |
| **Human squash-merge** | PR → main | reviewer clicks "Squash and merge" in GitHub UI (the only enabled merge type) |

Three skills support the flow:

- `/dev-setup` — one-time onboarding after `git clone`: `uv sync`, `uv run
  pre-commit install`, verify `gh` + `kaggle` auth, check `.env`.
- `/pr-open` — runs the PR-time gate above.
- `/pr-merge` — after the human squash-merges in GitHub: verify, archive
  the `mb/active/<slug>.md` tracking file, prune the worktree, delete
  the local branch.

## Why

We are 3 people on a low-stakes challenge repo, but we want:

- **A linear, roadmap-aligned history on `main`.** One PR ⇒ one
  squashed commit ⇒ one roadmap box ticked. `git log main` reads as the
  roadmap's audit log.
- **A pause point before mutation of `main`.** The GitHub UI's "Squash
  and merge" button is the human gate. Skills do not auto-merge.
- **No mandatory approvals.** Requiring review for a 3-person team
  where one member is usually solo would add wait time without
  proportional value. Discipline + PR review when teammates are
  available is enough.

## How (the actual commands)

Squash-only is enforced at the repo level via GitHub repo settings:

```bash
gh api -X PATCH /repos/jmsung/bio-reasoning \
  -f  allow_squash_merge=true \
  -F  allow_merge_commit=false \
  -F  allow_rebase_merge=false \
  -F  delete_branch_on_merge=true
```

Verify:

```bash
gh api /repos/jmsung/bio-reasoning \
  -q '{allow_squash_merge, allow_merge_commit, allow_rebase_merge, delete_branch_on_merge}'
```

Expected output:

```json
{
  "allow_squash_merge": true,
  "allow_merge_commit": false,
  "allow_rebase_merge": false,
  "delete_branch_on_merge": true
}
```

## Caveat — branch protection deferred

We would also like to enforce **"no direct push to `main`"** via branch
protection rules (`PUT /repos/.../branches/main/protection`) or via the
newer Rulesets endpoint (`POST /repos/.../rulesets`).

Both are **gated to GitHub Pro on private repositories**. Our repo is
private (`gh api /repos/jmsung/bio-reasoning -q .visibility` → `private`),
and we don't have Pro. The classic endpoint returns:

```
HTTP 403: Upgrade to GitHub Pro or make this repository public to
enable this feature.
```

Until either (a) we make the repo public, or (b) someone upgrades to
Pro, **no-direct-push is enforced by team discipline** — through this
document, `docs/development.md`, and the team's habit of always going
through `/pr-open`.

Making the repo public is a real trade-off — competitors on the
BioReasoning Challenge can see our methodology. We are not making that
trade now; we revisit after the challenge.

## Consequences

- `git log main` is linear; bisect granularity is per-PR, not per-WIP-commit.
- Intra-branch commits ("goal 1 / goal 2 / …") stay on the branch and
  are squashed away on merge. The branch's `mb/active/<slug>.md` file
  preserves the per-goal narrative for retrospectives.
- `/worktree-done` is superseded by `/pr-open` + manual squash + `/pr-merge`.
  We keep `/worktree-done` available for non-PR-flow projects.
- The same-PR-ticks-the-box rule is now mechanical (`/pr-open` does it),
  not human discipline.
- Teammates need to run `/dev-setup` exactly once after `git clone` to
  install hooks. Without it, pre-commit doesn't fire and trivia leaks
  into PRs — annoying but caught by `/pr-open`, so not a quality risk.
