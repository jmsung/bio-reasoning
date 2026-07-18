# bio-reasoning-2026 — team instructions for Claude Code

Shared Claude Code conventions for the BioReasoning Challenge 2026 team.
Applies to anyone working in this repo.

## Project

BioReasoning Challenge 2026 (MLGenX Workshop @ ICLR 2026). Testing whether
LLMs and agentic systems can serve as computational engines for predicting
cellular behavior.

- Challenge overview: https://genentech.github.io/BioReasoningChallenge/
- Track A (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a
- Track B (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b
- Track C (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-c
- GitHub: https://github.com/jmsung/bio-reasoning

## Philosophy

This project is a sandbox for **agentic engineering**, not our day job. We
use it to practice building with agents on a biologically meaningful problem
(gene regulation and prediction) in a safe, low-stakes environment.

- **Agents do the work, we manage.** The point is not for the developer to
  write the code — it's to define the goal, shape the plan, review, and give
  feedback. The agent executes under our direction and approval.
- **Agents must ask.** When intent is unclear or a decision is ambiguous,
  the agent stops and asks rather than guessing. Alignment beats velocity.
- **System thinking over micro-management.** Prefer cutting-edge harness,
  agentic workflows, and meta-learning over hand-tuning. If we find
  ourselves fine-tuning by hand, we're doing it wrong — step back and let
  the system do it.
- **Learn by doing.** Try, fail, iterate. Shipping a rough thing and
  learning from it beats planning a perfect thing.

## Team
- Jongmin Sung — https://www.linkedin.com/in/jongmin-sung/
- Bing Hu — https://www.linkedin.com/in/bingxuhu/
- Joo Lee — https://www.linkedin.com/in/joo-lee-b0a9b9161/

## Tech stack
- Python 3.x, managed with `uv`
- Install: `uv sync`
- Run: `uv run <cmd>`

## Repo layout

Full map (repo + Drive + Kaggle) lives in [`docs/where-things-live.md`](../docs/where-things-live.md) — single source of truth.

In-repo rule: if it would be `import`ed from a notebook or another script,
it lives in `src/bio_reasoning/`. Otherwise `scripts/`. Never duplicate
functions across scripts.

## Canonical docs

| File | Owns |
|---|---|
| [`README.md`](../README.md) | Project entry point, team, philosophy, getting started |
| [`docs/challenge.md`](../docs/challenge.md) | Challenge summary, per-track detail, entry decision |
| [`docs/roadmap.md`](../docs/roadmap.md) | Single living plan — priority-ordered Todo + completed milestones |
| [`docs/development.md`](../docs/development.md) | Setup, R&D workflow (brainstorm → roadmap → branch → PR → merge), conventions |
| [`docs/architecture.md`](../docs/architecture.md) | System design — data flow, components, per-track architectural notes |
| [`docs/foundation-models.md`](../docs/foundation-models.md) | Track C open-weights candidates + comparisons + pick |
| [`docs/kaggle-rules.md`](../docs/kaggle-rules.md) | Per-track submission format, limits, gotchas |
| [`docs/where-things-live.md`](../docs/where-things-live.md) | Repo / Drive / Kaggle map |
| [`knowledge/wiki/`](../knowledge/wiki/) | Distilled team knowledge — see [README](../knowledge/wiki/README.md) |

When the user asks "where does X live / how does Y work", check these first
and quote them. Don't duplicate their content here.

**Roadmap convention:** when a PR lands work that completes a `docs/roadmap.md`
item, the **same PR** must check the box. The roadmap should never lag merged
work. **Team R&D flow:** see [`docs/development.md`](../docs/development.md) —
brainstorm → roadmap → branch → PR → merge.

## Team skills (available in `.claude/skills/`)

Dev pipeline (run in this order across a branch's life):

- `/dev-setup` — one-time after `git clone`: `uv sync`, install pre-commit hooks, verify `gh` + `kaggle` auth, check `.env`.
- `/commit` — local commit: runs checks, reads the `gcm` block from the tracking file (or prompts), stages, commits. Never pushes.
- `/pr-open` — gated push + PR creation: rebase → pre-commit / pytest / mypy → 4 parallel reviewer agents (`@code-review`, `@security-audit`, `@docs-review`, `@wiki-lint`) → propose a report-worthy addition to `reports/progress-report.md` (user-gated, rides the PR) → push → `gh pr create` → tick matching `roadmap.md` items with `(#N)`. Stops at human squash-merge.
- `/pr-merge` — post-merge cleanup: verify PR merged (or `gh pr merge --squash` on confirm if still open), sync main, verify progress-report freshness (read-only — writes nothing to main), archive `mb/active/<slug>.md`, prune worktree, delete branch. Works in both layouts — universal (umbrella + linked worktree) and plain `git clone` (mb-archive + worktree-prune are skipped automatically).

See [`knowledge/wiki/decisions/0001-pr-workflow.md`](../knowledge/wiki/decisions/0001-pr-workflow.md) for the 3-gate model (pre-commit → `/pr-open` → squash UI).

Other:

- `/git-sync` — safe-sync this repo (commit → fetch → rebase → push). Never `--force` on shared branches.
- `/wiki-query` — search the team wiki, synthesize a cited answer.
- `/wiki-ingest` — ingest a paper / web page / talk into `knowledge/source/` as a distilled page.
- `/wiki-learn` — distill a conversation insight into a new wiki page.
- `/wiki-lint` — wiki health checks (orphans, stale claims, missing cites).

## Reliability order — wiki > web > model knowledge

This project's wiki is a living, hybrid (human + agent) knowledge base.
When answering a question, rank sources in this order:

1. **The wiki first** — `knowledge/source/` (per-artifact distillations) and
   `knowledge/wiki/` (hand-curated synthesis). Treat these as ground truth
   for this project; cite the specific page.
2. **Web second** — WebFetch / WebSearch only when the wiki is silent
   or insufficient. Cite the URL inline. If the source is durably
   useful, run `/wiki-ingest <url>` so the next query hits step 1.
3. **Model training knowledge last** — only when both the wiki and a
   web fetch fail. Mark the answer as "from model knowledge, not from
   wiki/web" so the reader knows it's lower-confidence.

The wiki compounds — bypassing it makes it stale. When you learn
something durable from the web or from a teammate conversation, file
it back via `/wiki-ingest` or `/wiki-learn` so future agents and
teammates land at step 1.

For full layout + flow: [`knowledge/wiki/README.md`](../knowledge/wiki/README.md).

### Consult the KB first — the exploration/strategy gate

Reliability order is not aspirational. **Before proposing any exploration,
experiment, or strategy** (a new approach, a roadmap item, "what should we try
for Track X"), the agent MUST first retrieve from the KB and ground its proposal
in what we already know:

```bash
qmd query "<your question>" -c bio-reasoning -n 10 --files
```

The `bio-reasoning` collection indexes all of `cb/` — so this surfaces not just
papers (`knowledge/source/`, `knowledge/domains/**`) but the **synthesized wisdom**
in `knowledge/wiki/findings/` and `knowledge/wiki/methods/` (e.g. what already failed,
which levers moved the score, competitor landscape) *and* the strategy docs
(`docs/roadmap.md`, `docs/foundation-models.md`). Read the top hits, then:

- **Cite** the specific `findings/` / `methods/` / `source/` pages that inform the plan.
- **Don't re-propose** something a `findings/` page already tried and ruled out —
  say so and build on it instead.
- **Learn back:** when exploration produces a durable insight, file it via
  `/wiki-learn` (→ `findings/`) and re-embed (`qmd embed -c bio-reasoning`) so the
  next agent starts from it. The KB only compounds if you write back.

If `qmd` is unavailable, fall back to `/wiki-query` (grep over `knowledge/`). Skipping
this gate — reasoning from model priors when the KB has a relevant page — is a defect,
not a shortcut.

## Documentation is the source of truth
- `README.md` and `docs/` are authoritative. Always keep them current.
- Any code change affecting workflow, API, file layout, data schema, or
  commands MUST update the relevant docs in the same commit or PR.
- When answering "where does X live / how does Y work" questions, check
  README/docs first and quote them. Stale docs are worse than missing docs —
  fix them on sight.

## Coding conventions
- Clean, readable, production-quality. Simplicity over cleverness.
- Minimal diffs — every changed line should trace to the task.
- Default to no comments. Add one only when WHY is non-obvious.
- Follow existing structure. Keep changes localized.
- Don't introduce hypothetical-future abstractions.

## Commits and branches
- Conventional commits: `type(scope): description`
- Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`
- Each commit = one cohesive unit. Explain *why*, not *what*.
- Branch naming: `type/description` (kebab-case)
- Never force-push to main. Don't skip hooks (`--no-verify`).
- Open PRs against `main`. At least one teammate review before merge.

## Workflow with Claude Code
- Plan before coding for non-trivial tasks.
- Work in small iterative chunks — one sub-task at a time.
- For new code: TDD (test → signature → implementation).
- Don't guess silently. If context is missing, read the repo, ask
  teammates, or ask the user before assuming.
- Be terse in responses. The diff speaks for itself.

## Shared resources
- GitHub (code + PRs + issues): https://github.com/jmsung/bio-reasoning
- Google Drive (papers, materials): private — shared with the team
- Kaggle competitions: Track A / B / C URLs in the Project section above
