---
name: pr-open
description: Run all pre-PR checks, push the branch, open the PR, and tick matching roadmap items with (#N). Stops at human squash-merge.

disable-model-invocation: true
---

Runs the full PR-time gate before main: rebase → checks → 4 parallel
reviews → propose a report-worthy addition (if the project keeps
`reports/progress-report.md`) → push → `gh pr create` → update
`docs/roadmap.md` with `(#N)`. **Does not auto-merge** — the human clicks
"Squash and merge" in the GitHub UI.

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

Verify working tree is clean:

```bash
[ -z "$(git -C "$REPO" status --porcelain)" ] || {
  git -C "$REPO" status --short
  echo "Uncommitted changes — commit or stash before /pr-open." >&2
  exit 1
}
```

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

### 4. Quality gate — 4 agents in parallel

Spawn all four as parallel subagents in a single message (the Agent tool
runs them concurrently). Each returns one structured report.

| Agent | Role | Gate |
|---|---|---|
| `@code-review` | bugs, reuse, simplification, efficiency in the diff | soft (review-only) |
| `@security-audit` | secrets, leaks, injection, auth/authz; reads project CLAUDE.md for scope | **HARD** (any finding blocks push) |
| `@docs-review` | README + `docs/` drift vs the code changes; auto-fixes committed locally | soft (fixes itself) |
| `@wiki-lint` | orphans, broken cites, body-link gaps in `knowledge/wiki/` | soft (review-only) |

`@distill` is opt-in (run separately when the branch warrants it) — not
included in the per-PR gate.

**Why all agents, no skills?** Per
[`0002-skill-vs-agent-convention.md`](../../../knowledge/wiki/decisions/0002-skill-vs-agent-convention.md):
quality-gate orchestrators spawn parallel reviewer agents. Agents give
~3× faster wall-clock (true parallelism), isolated context (no
pollution back into your conversation), and a uniform report shape for
bulk review.

Aggregate the findings into one block grouped by source. Two outcomes:

- **No blocking issues / user accepts as-is** → continue to step 5.
- **Issues to fix** → ask the user to address (with you or manually).
  After fixes are committed, return to step 3.

Severity bar for "blocking":
- Code review: any CONFIRMED bug or unhandled correctness finding.
- Security: any leaked secret, auth bypass, or injection sink (HARD block — never push).
- Wiki: broken cites or orphans that touch a page this PR modifies (otherwise informational).
- Docs: any stale claim that contradicts the merged behavior (e.g., command renamed but README still shows old form).

User can override informational findings; never override security.

### 5. Report-worthy addition to progress report (conditional, user-gated)

If the project keeps a committed narrative report (`reports/progress-report.md`),
assess whether this branch produced something worth adding, and let the user approve.
This runs **pre-push** so an approved addition **rides this PR** and is reviewed with
the code (the report's own header declares additions are proposed "per PR").

1. **Skip silently** if `reports/progress-report.md` does not exist (most projects
   won't have one).
2. Launch a subagent with the branch diff (`git -C "$REPO" diff origin/main...HEAD`),
   the PR body Summary, and the current `reports/progress-report.md`. Task: judge whether
   the branch produced a result a collaborator reading the report would want — a **new
   empirical/scientific result, a methods change, or a significant finding** (NOT routine
   refactors, chores, fixes, infra, or skill/tooling edits). If yes, draft the addition (a
   section or paragraph matching the report's structure, with the key numbers) and name
   which section it slots into. If not report-worthy, return `NONE`.
3. If the subagent returns a draft, present it and **ask via `AskUserQuestion`** (approve /
   edit / skip), showing the drafted text verbatim. Nothing is written without an explicit
   approve.
4. On approval: insert into `reports/progress-report.md` at the named location, bump the
   `*Last updated:*` line to today, and commit on the branch:
   ```bash
   git -C "$REPO" add reports/progress-report.md
   git -C "$REPO" commit -m "docs(reports): add <result> to progress report"
   ```
   It ships in this PR. The working tree must be clean again before push (step 6).

**Recommend-only and user-gated:** the subagent *proposes*; the user disposes. A `NONE`
verdict or a skip writes nothing and never blocks the PR. Keep additions tight — the report
is publishable, so prefer a crisp result paragraph over a dump.

### 6. Push the branch

```bash
git -C "$REPO" push -u origin "$BRANCH"
```

If push is rejected (non-fast-forward), abort and surface — never
`--force` from this skill.

### 7. Open the PR

Extract `PR_TITLE` and `PR_BODY` from `mb/active/<slug>.md` (between the
`<!-- PR_TITLE -->` and `<!-- PR_BODY -->` markers). If either is empty,
abort: "Missing PR_TITLE or PR_BODY in tracking file."

If a PR already exists for this branch (re-open or update flow):

```bash
PR_NUM=$(gh pr view --json number -q .number 2>/dev/null)
```

- **No existing PR** → `gh pr create --title "<PR_TITLE>" --body-file <(printf '%s' "$PR_BODY")`.
  Then `PR_NUM=$(gh pr view --json number -q .number)`. If `PR_NUM`
  is empty after creation, abort: "PR created but number not
  resolvable — check `gh pr list` manually."
- **Existing PR** → skip creation; just continue.

### 8. Tick matching roadmap items with (#N)

Read `docs/roadmap.md`. Identify which `- [ ]` items this PR closes —
this is a judgment call:

1. List every `- [ ]` line in `docs/roadmap.md`'s Todo section.
2. Read the PR body's Summary bullets.
3. Suggest matches: "PR #N closes roadmap items 1, 5 — confirm? [y/n/edit]"
4. On `y`: rewrite the matched `- [ ] **Item**` → `- [x] (#N) **Item**`.
   Preserve the rest of the line verbatim.
5. On `edit`: ask which items to tick.

If no items match (skill PR, refactor, infrastructure), skip silently.

### 9. Commit + push the roadmap edit

If step 8 made any changes:

```bash
git -C "$REPO" add docs/roadmap.md
git -C "$REPO" commit -m "docs(roadmap): tick item(s) closed by #$PR_NUM"
git -C "$REPO" push origin "$BRANCH"
```

### 10. Report

Print:

```
PR opened: <URL>
Branch:    <branch>
Checks:    pre-commit ✓ pytest ✓ mypy ✓
Reviews:   code ✓ security ✓ docs ✓ wiki ✓
Report:    added "<result>" to progress-report.md (or "none — not report-worthy / no report")
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
