# Development

How we set up, work, and ship on this repo. If you're just landing here,
read this once end-to-end before opening a PR.

## Setup

Python is managed with [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync                 # install deps from pyproject.toml + uv.lock
cp .env.example .env    # fill in API keys (Together AI / Fireworks for
                        # GPT-OSS-120B; Kaggle for data download)
uv run pytest           # smoke-test that the env works
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
4. **PR for review.** Open the PR against `main`. **In the same PR,
   check the box in `roadmap.md`** for the item you landed — the plan must
   not lag merged work. Tag a teammate for review on anything non-trivial.
5. **Merge into main.** Squash or merge per your preference; either is
   fine. Delete the branch.

For agent-driven work, the same loop is wrapped by the
[`/goal` → `/act` → `/commit`](.claude/skills/) skills — same shape, the
agent just handles the mechanics.

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

- Open against `main`.
- At least one teammate review for non-trivial changes.
- The PR body should explain the **why** — the diff shows the what.
- If the PR lands a roadmap item, check the box in `roadmap.md` in the
  **same PR**.
- If the PR changes workflow, API, file layout, data schema, or commands,
  update the relevant docs in the **same PR**. Stale docs are worse than
  missing docs.

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
