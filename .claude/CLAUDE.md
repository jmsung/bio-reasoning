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
- GitHub: https://github.com/jmsung/bio-reasoning

## Team
- Jongmin Sung — https://www.linkedin.com/in/jongmin-sung/
- Bing Hu — https://www.linkedin.com/in/bingxuhu/
- Joo Lee — https://www.linkedin.com/in/joo-lee-b0a9b9161/

## Tech stack
- Python 3.x, managed with `uv`
- Install: `uv sync`
- Run: `uv run <cmd>`

## Repo layout
- `src/bio_reasoning/` — importable package code (`data/`, `features/`, `models/`, `training/`, `eval/`, `utils/`)
- `scripts/` — entry points: `prepare_data.py`, `train.py`, `predict.py`, `make_submission.py`
- `configs/` — experiment configs (one YAML per experiment)
- `notebooks/` — exploration (numbered: `01-eda.ipynb`, …)
- `tests/` — pytest
- `docs/` — design notes, data schemas, decisions
- `data/` — `raw/` / `processed/` / `external/` / `interim/` — gitignored except READMEs/.gitkeep
- `models/`, `outputs/`, `submissions/` — gitignored except READMEs

Rule: if it would be `import`ed from a notebook or another script, it lives
in `src/`. Otherwise `scripts/`. Never duplicate functions across scripts.

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
- Google Drive (papers, materials): *(link TBD)*
- Kaggle competitions: see Track A / Track B URLs above
