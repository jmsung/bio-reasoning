# bio-reasoning-2026

BioReasoning Challenge 2026 — MLGenX Workshop @ ICLR 2026.

Testing whether LLMs and agentic systems can serve as useful computational engines for predicting cellular behavior.

## Challenge

Predict perturbation outcomes in macrophages using LLMs / agentic systems.
Three tracks (prompt-only, agentic tool-use, fine-tuning). Canonical
summary, per-track detail, and entry decision live in
[`docs/challenge.md`](docs/challenge.md).

Overview: https://genentech.github.io/BioReasoningChallenge/

Likely entering A and/or B.

## Setup

```bash
uv sync
```

## Layout

- `src/bio_reasoning/` — library code
  - `data/` — loaders, transforms
  - `features/` — feature engineering
  - `models/` — model definitions
  - `training/` — train loop, callbacks
  - `eval/` — metrics, validation
  - `utils/` — seed, logging, io
- `scripts/` — entry points: `prepare_data.py`, `train.py`, `predict.py`, `make_submission.py`
- `configs/` — experiment configs (YAML per experiment)
- `notebooks/` — exploration (numbered: `01-eda.ipynb`, …)
- `tests/` — pytest
- `docs/` — team-facing docs (architecture, design notes, decisions)
- `data/` — `raw/`, `processed/`, `external/`, `interim/` (gitignored except READMEs/.gitkeep)
- `models/` — checkpoints (gitignored except README)
- `outputs/` — run artifacts: logs, preds, figures (gitignored except README)
- `submissions/` — Kaggle submission files (gitignored except README)

## Source of truth

`README.md` and `docs/` are the authoritative reference for this repo.
Any code change that affects workflow, API, file layout, data schema, or
commands **must** update the relevant docs in the same commit or PR.
Stale docs are worse than missing docs.
