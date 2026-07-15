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

The metric is **`mean(AUROC_de, AUROC_dir)`**, *not accuracy* — confirmed
from the vendored official scorer
[`src/bio_reasoning/eval/kaggle_metric_track_a.py`](../src/bio_reasoning/eval/kaggle_metric_track_a.py):

- **AUROC_de** ranks none-vs-DE by `prediction_up + prediction_down`.
- **AUROC_dir** ranks up-vs-down by `prediction_up / (prediction_up + prediction_down)`
  over DE-positive rows only.

Consequences: predictions must be **graded** (`prediction_up`,
`prediction_down` floats), not hard labels; a constant "predict none" scores
≈ **0.5**, not 0.553 — the 0.553 majority-class figure is an *accuracy*
reference and does **not** apply to this metric. Submissions also carry
per-seed predictions, reasoning traces, and token counts, and Track A caps
**prompt tokens at 4,096**. Public-leaderboard top ≈ 0.65 is on this AUROC
scale. Our leak-free evidence-prior floor is ≈ 0.53 (direction carries the
signal; DE-vs-none is flat) — see the Track A prior baseline.

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

23 leaderboard entries (of 26 joined teams). Headroom over baseline
(~0.10) suggests prompting alone gets meaningful signal — the question
is how much.

## Track B — (multi-)agentic tool-use

[Kaggle](https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b) · Community competition · $2,000 USD prize.

### Task and data

**Identical to Track A.** Same 3-class problem (`up` / `down` / `none`),
same `train.csv` and `test.csv` byte-for-byte, same dual-OOD split. The
prediction target is the same; only the modeling rules differ.

### Constraints (from challenge overview)

- **Fixed base model:** GPT-OSS-120B.
- **Tool use allowed:** design and use tools / multi-agent architectures
  around the fixed base.
- **Limits:** ≤ 100 tools, ≤ 250 calls per test row, 16,384 prompt tokens.
- **Traces required:** submissions must include traces of tool calls for
  reproducibility / audit.
- Exact limits to confirm from the Kaggle rules tab.

### Evaluation and submission

Same `mean(AUROC_de, AUROC_dir)` metric and graded-prediction submission
shape as Track A (see Track A Evaluation above).

### Leaderboard snapshot (2026-06-06)

| Rank | Team | Score |
|---|---|---|
| 1 | shijingzhao | 0.652 |
| 2 | Alex Li | 0.632 |
| 3 | Misha Shikhov | 0.620 |
| 4 | Álvaro | 0.612 |
| 5 | Tian Luyi | 0.606 |

12 leaderboard entries (of 12 joined teams). Top score is essentially tied with Track A's top —
suggests that, at the current state of the leaderboard, agentic tool-use
is not yet pulling ahead of careful prompting. Headroom for whichever
approach lands the right tools.

## Track comparison

| Dimension | Track A (prompt-only) | Track B (agentic tool-use) | Track C (fine-tuning) |
|---|---|---|---|
| Task | 3-class direction (`up`/`down`/`none`) | identical | identical |
| Data | `train.csv` 7,705 rows + `test.csv` 1,813 rows | byte-identical to A | byte-identical to A |
| Base model | GPT-OSS-120B (fixed) | GPT-OSS-120B (fixed) | any open model < 10B (you train it) |
| Modeling moves | prompt engineering only | tool design + agent architecture | fine-tuning technique |
| Inference cost | 1 call × 3 samples per row | up to 250 tool calls per row | depends on chosen model |
| Compute required | inference only | inference only | GPU training |
| Top leaderboard (2026-06-06) | 0.651 | 0.652 | 0.611 |
| Headroom over baseline (0.553) | +0.10 | +0.10 | +0.06 |
| Submission cadence | Kaggle daily limit | Kaggle daily limit | Kaggle daily limit |
| Reward | $2,000 USD | $2,000 USD | $2,000 USD |
| Fit with project philosophy | Strong baseline; high signal per effort | Direct fit — "agentic engineering sandbox" | Off-pattern (we'd be fine-tuning, not orchestrating agents) |
| Effort to enter | Low — prompt + submit | Medium — tool design + traces | High — GPU, FT pipeline |
| Teams joined to date | 26 | 12 | 14 |

Notes:
- Tracks A and B compete on the **same task with the same data** — the
  only thing being optimized is the design of the LLM-engineering layer
  around a fixed base. Code, evaluation harness, and data loaders are
  shared.
- Top scores on A and B are essentially tied — at the current leaderboard
  state, agentic tool-use has not yet beaten careful prompting. This is
  upside for whoever lands the right tools.
- Track C's lower top score is consistent with the harder problem of
  beating a 120B base with a < 10B fine-tune.

## Entry decision

**Primary focus: Track B (agentic tool-use).**
**Active baseline: Track A (prompt-only).**
**Optional / opportunistic: Track C (fine-tuning).**

All three tracks share the same data byte-for-byte (confirmed
2026-06-06), so the entry barrier is low — the team has joined all
three Kaggle competitions to preserve optionality.

Rationale:

- **Track B is the project's purpose.** From `.claude/CLAUDE.md`: "This
  project is a sandbox for **agentic engineering**." Track B is
  literally that — design tools, design agents, watch them reason.
- **Track A is the unavoidable baseline.** If our agent (B) can't beat
  careful prompting (A), the agent isn't earning its complexity. A is
  the control we measure B against — necessary regardless of the
  leaderboard.
- **A + B share everything except the modeling layer.** One data
  pipeline, one eval harness, two submissions. Marginal cost of doing
  both ≈ the tool / agent design work itself, which is exactly the
  practice we want.
- **Track C is opt-in, not committed.** Fine-tuning a < 10B model is a
  different exercise (supervised learning, GPU bookkeeping, HF training
  stack). Top leaderboard 0.611 vs 0.65 on A/B suggests less near-term
  headroom. We've joined to keep the option open; we'll only spend
  effort here if (a) someone on the team has bandwidth, (b) we have a
  specific hypothesis a small FT could test, and (c) A and B work is
  stable. Not the default path.

Pending confirmation from Bing and Joo before this is final.

## Timeline

- **Final submission deadline:** 2026-07-22 07:00:00 UTC (all three tracks).
- Workshop: ICLR 2026 (date TBD from MLGenX schedule).

## Rules and logistics

### Eligibility

Overview page: "will follow a good-faith policy regarding cheating." No
explicit team-size limit found yet; Kaggle's per-competition default
applies — confirm from each Track's rules tab before merging teams.

### Per-track constraints

| | Track A (prompt-only) | Track B (agentic) | Track C (fine-tuning) |
|---|---|---|---|
| Base model | GPT-OSS-120B (fixed) | GPT-OSS-120B (fixed) | any open model, **≤ 10B total params** |
| Tools | none — single LLM call | ≤ 100 tools, ≤ 250 calls per row | none |
| Prompt tokens | ≤ 4,096 | ≤ 16,384 | n/a |
| Samples per question | 3 | n/a | n/a |
| Traces | not required | **required** (audit) | n/a |
| Fine-tuning | forbidden | forbidden | any technique |

Sources: challenge overview, Track A Kaggle forum (organizer reply,
2026-05-11), Track C Kaggle forum (organizer reply, 2026-05-27).

### Rule clarifications (from organizer forum replies)

- **Track A "prompt-only" scope.** "Generally speaking, there are not
  constraints placed on how the prompt is constructed" except the
  4,096-token cap and the rule that "the prompt cannot directly include
  the expected outputs." Using external scripts / automated methods for
  prompt optimization is allowed and *encouraged* to be shared. What is
  **not** allowed: running another model on the test rows and stuffing
  its predictions into the prompt.
- **Track C 10B limit is TOTAL params, not effective.** Gemma E4B (4B
  effective, 8B total) is allowed. Params dedicated to non-text
  modalities (e.g. audio in E4B) can be removed and excluded from the
  count.
- **GPT-OSS-120B access:** organizers confirm querying it through an API
  (Together AI, Fireworks, etc.) is fine — no need to run locally —
  "as long as you use the correct model and sampling parameters."
- **No traditional-ML-only submissions.** Track A is for LLM-prompted
  predictions; non-LLM pipelines (TF-IDF / SVD / boosting) violate the
  rules. Organizers will audit top solutions for compliance.

### Reference implementation

Genentech publishes a reference repo with example submissions and the
scripts to generate them:

- https://github.com/genentech/bioreasoningchallenge

Treat this as the canonical "how submissions are produced" guide. Read
before writing our own pipeline.

## Data

All three tracks ship the **same** `train.csv` + `test.csv`. The task is
3-class direction prediction (`up` / `down` / `none`) for a `(perturbation,
target gene)` pair in macrophages.

### Files

| File | Rows | Schema | Where it lives locally |
|---|---|---|---|
| `train.csv` | 7,705 | `id, pert, gene, label` | `data/raw/<track>/` (gitignored) |
| `test.csv` | 1,813 | `id, pert, gene` | `data/raw/<track>/` (gitignored) |

`id = "<pert>_<gene>"`.

### Splits (train vs test)

| Dimension | Train unique | Test unique | Overlap |
|---|---|---|---|
| Perturbations | 386 | 96 | **0** |
| Target genes | 1,570 | 636 | **0** |

Dual-OOD: every test row pairs an unseen perturbation with an unseen
target gene. Memorization cannot help.

### Label distribution (train)

| Class | Count | Share |
|---|---|---|
| `none` | 4,260 | 55.3% |
| `up` | 2,359 | 30.6% |
| `down` | 1,086 | 14.1% |

Majority-class baseline ≈ 0.553. Current leaderboard tops ≈ 0.65.

### Provenance and license

- **Curated by Genentech (BRAID team)** for the challenge.
- Underlying biology: macrophage perturbation experiments. Specific assay
  / cell line not stated on Kaggle's data tab as of 2026-06-06 — confirm
  from the data tab or the Genentech GitHub repo before publication.
- **License:** not bundled with the CSVs; subject to each Kaggle
  competition's rules — confirm before redistribution.

### Access

- Kaggle competition page (per track) → accept rules → `kaggle
  competitions download -c <slug>`.
- All three tracks must be joined separately for data access (the user
  has joined all three as of 2026-06-06).
- Raw CSVs live under `data/raw/<track>/` and are gitignored. We
  never commit competition data.

## Submission format

### File shape

Inferred from `test.csv` columns and the convention of Kaggle community
competitions:

```csv
id,label
Slc35b1_Pdia6,none
Rprd2_9930111J21Rik2,down
...
```

One row per test `id`, label ∈ `{up, down, none}`. Confirm the exact
header and any required dtypes against each Track's Kaggle submission
page before the first submit — Kaggle's evaluator rejects header
mismatches silently into "format error" leaderboard entries.

No `sample_submission.csv` is bundled in the competition zip; the
reference implementation at
[genentech/bioreasoningchallenge](https://github.com/genentech/bioreasoningchallenge)
should be the source of truth for the canonical format.

### Submission cadence

- Submissions are **generated locally** (Kaggle notebooks are not the
  expected workflow per organizer reply, 2026-05-15).
- Kaggle's daily-submission cap applies per track. The exact number isn't
  exposed via the CLI — check each competition's submission page.
- Use the Kaggle CLI:
  ```bash
  kaggle competitions submit -c <track-slug> -f submission.csv -m "<message>"
  ```

### Final-submission selection

Kaggle community competitions typically let teams pick which of their
submissions count for the private leaderboard. Verify the count and the
selection deadline (usually same as the final-submission deadline,
2026-07-22 07:00:00 UTC) from each Track's rules tab.

### Track B traces

Track B requires submission of **traces** of tool calls alongside the
prediction CSV. Format and upload mechanism not yet inspected — confirm
from Track B's rules tab and the reference repo before our first Track B
submission.

## Organizers

Organized by **Genentech (BRAID team)**. Listed organizers include Carl
Edwards, Ehsan Hajiramezanali, Sara Mostafavi, and Aviv Regev, among
others.

## References

- Challenge overview: https://genentech.github.io/BioReasoningChallenge/
- Reference implementation: https://github.com/genentech/bioreasoningchallenge
- Track A (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-a
- Track B (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-b
- Track C (Kaggle): https://www.kaggle.com/competitions/ml-gen-x-bioreasoning-challenge-track-c
- Workshop: MLGenX @ ICLR 2026

_Overview + data fetched 2026-06-06. Re-check before any decision that
depends on timeline, eligibility, or rule details — organizer replies on
Kaggle forums supersede the static overview page._
