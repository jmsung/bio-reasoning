# Development

How we set up, work, and ship on this repo. If you're just landing here,
read this once end-to-end before opening a PR.

## Setup

Python is managed with [`uv`](https://docs.astral.sh/uv/). The fast path is
**`/dev-setup`** in Claude Code — one skill that does everything below.

```bash
/dev-setup              # in Claude Code — does uv sync, pre-commit install,
                        # and verifies gh + kaggle auth + .env
```

Or manually:

```bash
uv sync                       # install deps from pyproject.toml + uv.lock
uv run pre-commit install     # wire the pre-commit hook (one-time)
cp .env.example .env          # then fill in API keys (Together AI /
                              # Fireworks for GPT-OSS-120B; Kaggle for data)
uv run pytest                 # smoke-test that the env works
```

Run any command in the project env with `uv run <cmd>`. Don't `pip install`
into the system Python.

Data and large artifacts are **not** in the repo. See
[`where-things-live.md`](where-things-live.md) for the repo / Drive / Kaggle
map.

## R&D workflow

We work in 5 small steps. The point is to keep the plan, the work, and the
merged history in sync.

1. **Brainstorm + discuss.** Open question or loose idea. Talk it through
   with the team (sync or async — a draft PR description is fine). The goal
   is alignment on *what* and *roughly how*, not a finished design.
2. **Update [`roadmap.md`](roadmap.md).** Add or sharpen the item, in
   priority order. If the idea displaces existing items, re-rank them in the
   same edit. The roadmap is the single living plan.
3. **Branch + implement.** Use `/worktree-start <type>/<slug>` to get an
   isolated worktree and a branch tracking file. Iterate in small commits.
   TDD where it applies (new pure functions; data transforms with clear I/O).
   Every `git commit` runs the **pre-commit hook** (`.pre-commit-config.yaml`)
   — black, ruff lint, mypy on `src/`, plus hygiene checks. Fix what it
   flags; don't bypass with `--no-verify`.
4. **Open the PR.** Run **`/pr-open`** in Claude Code. It runs the full
   pre-PR gate (pre-commit sweep, pytest, mypy, then 4 parallel reviewer
   agents: `@code-review`, `@security-audit`, `@docs-review`,
   `@wiki-lint`), pushes the branch, opens the PR, and **ticks the
   matching `roadmap.md` item with `(#N)`**. No manual box-checking
   required.
5. **Squash-merge in GitHub.** Squash is the only merge type allowed
   (enforced in repo settings). Review in the UI, then click "Squash and
   merge". The remote branch auto-deletes. Then run **`/pr-merge`** to
   archive the tracking file, delete the local branch, and prune the
   worktree.

For agent-driven work, the same loop is wrapped by the
`/goal` → `/act` → `/commit` harness skills — same shape, the agent just
handles the mechanics. Background and rationale for the PR-only flow:
[`knowledge/wiki/decisions/0001-pr-workflow.md`](../knowledge/wiki/decisions/0001-pr-workflow.md).

## Conventions

### Commits

Conventional commits: `type(scope): description`.

Types we use: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`.

Each commit is one cohesive unit. The message body explains the **why**,
not the **what** — the diff already shows what.

Example:

```
docs(roadmap): seed from current Todo

Establish a single living plan so the roadmap doesn't drift from PRs.
```

### Branches

`type/description` in kebab-case. Examples: `docs/team-scaffold`,
`feat/gpt-oss-inference`, `fix/data-loader-shuffle`.

Never force-push to `main`. Don't skip hooks (`--no-verify`).

### PRs

- Open against `main` via `/pr-open` (runs checks + creates the PR).
- At least one teammate review for non-trivial changes.
- The PR body should explain the **why** — the diff shows the what.
- If the PR lands a roadmap item, `/pr-open` ticks the box automatically
  in the form `- [x] (#N) Item`. No manual edit needed.
- If the PR changes workflow, API, file layout, data schema, or commands,
  update the relevant docs in the **same PR**. Stale docs are worse than
  missing docs.
- Only **squash-merge** is enabled in repo settings. The remote branch is
  deleted automatically on merge.

### Code

- Clean, readable, production-quality. Simplicity over cleverness.
- Minimal diffs — every changed line should trace to the task.
- Default to no comments. Add one only when the **why** is non-obvious.
- Follow the in-repo rule from [`where-things-live.md`](where-things-live.md):
  importable code → `src/bio_reasoning/`, entry points → `scripts/`.
- Don't introduce hypothetical-future abstractions.

### Tests

- `tests/` mirrors `src/bio_reasoning/`.
- `uv run pytest` should pass before opening a PR.
- New pure functions or data transforms: write the test first.
