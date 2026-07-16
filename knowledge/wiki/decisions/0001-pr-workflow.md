---
title: PR-only workflow with squash-merge
date: 2026-06-06
status: accepted
---

<!-- Body links to docs/development.md and docs/roadmap.md (outside the
     wiki tree). Wiki `cites:` are wiki-root-relative per @wiki-lint;
     extra-wiki references stay in the body. -->


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
| **`/pr-open` skill** | branch → PR | full lint + typecheck + tests; then a 4-agent quality gate run in parallel (`@code-review`, `@security-audit`, `@docs-review`, `@wiki-lint`); then (if the project keeps `reports/progress-report.md`) a user-gated proposal to add a report-worthy result that rides this PR; then push + `gh pr create` + tick matching roadmap items with `(#N)`. Security findings are HARD blocks; other findings are surfaced for review. |
| **Human squash-merge** | PR → main | reviewer clicks "Squash and merge" in GitHub UI (the only enabled merge type) |

Three skills support the flow:

- `/dev-setup` — one-time onboarding after `git clone`: `uv sync`, `uv run
  pre-commit install`, verify `gh` + `kaggle` auth, check `.env`.
- `/pr-open` — runs the PR-time gate above.
- `/pr-merge` — after the human squash-merges in GitHub: verify, sync
  `main`, verify progress-report freshness (read-only — writes nothing to
  `main`), archive the `mb/active/<slug>.md` tracking file, prune the
  worktree, delete the local branch. Layout-aware — in a plain `git clone`
  (no umbrella / no worktree) the archive + worktree-prune steps are
  skipped and `main` is checked out in place.

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

## No-direct-push enforcement — free-tier "Path B"

We would prefer to enforce **"no direct push to `main`"** via GitHub
branch protection (`PUT /repos/.../branches/main/protection`) or the
newer Rulesets endpoint. Both are **gated to GitHub Pro on private
repos**, and ours is private + free. The classic endpoint returns
`HTTP 403: Upgrade to GitHub Pro or make this repository public`.

We don't want to make the repo public during the challenge (competitors
would see our methodology) and don't want to pay for Pro. So we use
**Path B** — client-side block + server-side loud-fail:

### Client-side: pre-push hook (refuses the push)

`.pre-commit-config.yaml` declares a pre-push hook that runs on every
`git push`. For pushes targeting `main`, it inspects each commit being
pushed and refuses if any commit subject doesn't end with `(#NNN)` —
the GitHub squash-merge marker.

Script: `scripts/git-hooks/no-direct-push-to-main.sh`.

Installed by `/dev-setup` (via `uv run pre-commit install`, which picks
up `default_install_hook_types: [pre-commit, pre-push]` in the config
and installs both hook types). Every teammate's clone gets it.

Bypass exists (`git push --no-verify`) but is documented as "don't,
except true emergencies". Lightweight discipline + visible-bypass-trail.

### Server-side: GitHub Actions guard (fails the workflow)

`.github/workflows/guard-main.yml` runs on every push to `main`. It
checks the HEAD commit's subject; if it doesn't end with `(#NNN)`, the
workflow fails with a loud red ❌ on the commit and a notification
email.

Free private repos can't reject pushes server-side (only paid plans
can), so this is informational — but a failing CI on `main` is hard to
ignore and creates a paper trail.

### Why "(#NNN)" as the marker

GitHub's squash-merge automatically formats the merged commit subject as
`<PR title> (#<PR number>)`. Both the pre-push hook and the Actions
guard look for this suffix as proof "this commit came from a merged PR,
not a direct push".

If the team adopts a different merge format later, both checks need to
update — they're hard-coded to this regex.

### When this gets replaced

Two upgrade paths replace Path B with a real server-side block:

1. **Make the repo public** when the challenge ends and we write up
   results. Classic branch protection becomes free.
2. **Upgrade to GitHub Pro** ($4/mo) if we want enforcement before going
   public.

Either unlocks: `gh api -X PUT /repos/jmsung/bio-reasoning/branches/main/protection` with PR-required + no-force-push + no-deletion. At that point Path B can stay (belt-and-suspenders) or be removed.

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
