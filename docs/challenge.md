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

Same metric and submission shape as Track A (`id,label`). Confirm against
the Track B evaluation tab before relying.

### Leaderboard snapshot (2026-06-06)

| Rank | Team | Score |
|---|---|---|
| 1 | shijingzhao | 0.652 |
| 2 | Alex Li | 0.632 |
| 3 | Misha Shikhov | 0.620 |
| 4 | Álvaro | 0.612 |
| 5 | Tian Luyi | 0.606 |

12 entries total. Top score is essentially tied with Track A's top —
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
| Entries to date | 26 teams | 12 teams | 14 teams |

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
