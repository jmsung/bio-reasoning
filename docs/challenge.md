# BioReasoning Challenge 2026

Canonical team summary of the BioReasoning Challenge 2026, organized by
Genentech's BRAID team and held at the **MLGenX Workshop @ ICLR 2026**.

This document is the source of truth for what the challenge is, which
track(s) we enter, and how submissions work. Track-level detail (data,
scoring, format) is filled in by subsequent goals on this branch.

## Motivation

The challenge asks whether LLMs and agentic systems can do more than talk
about biology — whether they can serve as useful computational engines for
predicting cellular behavior. Concretely, participants predict
**perturbation outcomes in macrophages**, combining biological knowledge
with structured reasoning to anticipate intervention effects.

## Tracks

Three tracks, each fixing a different axis of the LLM-engineering design
space so contributions are comparable.

- **Track A — Prompt-only (no tools, single call).** Optimize prompting
  with a fixed LLM. No fine-tuning, no tool use, single forward call.
- **Track B — (Multi-)agentic tool-use.** Design tools and multi-agent
  architectures around a fixed LLM. No fine-tuning of the base model.
- **Track C — Fine-tuning (reasoning, no tools).** Fine-tune an open model
  under 10B parameters using any fine-tuning technique. No tool use.

Deeper per-track sections (data, evaluation, constraints) are appended in
later goals on the `docs/scope-tracks` branch.

## Track A — prompt-only

[Kaggle](https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a) · Community competition · $2,000 USD prize.

### Task

3-class classification: given a **perturbation** (a perturbed gene) and a
**target gene**, predict the direction of expression change for that target
under the perturbation. Classes: `up` / `down` / `none`.

### Data

| File | Rows | Columns |
|---|---|---|
| `train.csv` | 7,705 | `id, pert, gene, label` |
| `test.csv` | 1,813 | `id, pert, gene` |

`id` is `<pert>_<gene>`. **Track A and Track B share the same data files
byte-for-byte** — the tracks differ only in modeling constraints, not the
prediction task or split.

### Label distribution (train)

| Class | Count | Share |
|---|---|---|
| `none` | 4,260 | 55.3% |
| `up` | 2,359 | 30.6% |
| `down` | 1,086 | 14.1% |

Majority-class baseline ≈ **0.553**.

### Out-of-distribution split

| Dimension | Train unique | Test unique | Overlap |
|---|---|---|---|
| Perturbations | 386 | 96 | **0** |
| Target genes | 1,570 | 636 | **0** |

Zero overlap on both axes — every test pair is a new perturbation
**and** a new target gene. The task is designed to penalize memorization
and reward biological reasoning that generalizes across both axes.

### Evaluation

Metric not visible in the bundled files. Public-leaderboard top score
≈ **0.65** (vs majority-class baseline 0.553), consistent with accuracy
or a similar [0, 1] classification metric. Confirm from the Kaggle
evaluation tab before relying on this for tuning.

### Submission format

No `sample_submission.csv` is bundled. From the column layout the expected
shape is almost certainly:

```csv
id,label
Slc35b1_Pdia6,none
Rprd2_9930111J21Rik2,down
...
```

Confirm column names and label spelling against the Kaggle submission page
before first submit.

### Constraints (from challenge overview)

- **Fixed base model:** GPT-OSS-120B.
- **No tools, single forward call.**
- Token budgets and sample-per-question limits per overview page; exact
  numbers to confirm from the Kaggle rules tab.

### Leaderboard snapshot (2026-06-06)

| Rank | Team | Score |
|---|---|---|
| 1 | Misha Shikhov | 0.651 |
| 2 | João Victor | 0.640 |
| 3 | Alex Li | 0.632 |
| 4 | Jeki Wan Taufik | 0.628 |
| 5 | Álvaro | 0.615 |

23 entries total. Headroom over baseline (~0.10) suggests prompting
alone gets meaningful signal — the question is how much.

## Timeline

- **Final submission deadline:** 2026-07-22 07:00:00 UTC (all three tracks).
- Workshop: ICLR 2026 (date TBD from MLGenX schedule).

## Eligibility

The overview page states the challenge "will follow a good-faith policy
regarding cheating" but does not specify team size limits or participant
restrictions. Track-specific constraints (base model, parameter limits,
token budgets) live in the per-track sections. General eligibility to be
confirmed from Kaggle and updated here.

## Organizers

Organized by **Genentech (BRAID team)**. Listed organizers include Carl
Edwards, Ehsan Hajiramezanali, Sara Mostafavi, and Aviv Regev, among
others.

## References

- Challenge overview: https://genentech.github.io/BioReasoningChallenge/
- Track A (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a
- Track B (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b
- Workshop: MLGenX @ ICLR 2026

_Overview fetched 2026-06-06. Re-check before any decision that depends on
timeline or eligibility._
