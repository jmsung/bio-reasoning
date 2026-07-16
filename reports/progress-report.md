# BioReasoning Challenge 2026 — Progress Report

*Updated as branches land — the merge workflow proposes report-worthy additions per PR.*
*Last updated: 2026-07-15.*

## Goal

Predict how a genetic perturbation reshapes a target gene's expression in macrophages —
a 3-class call (`up` / `down` / `none`) for each `(perturbation, target-gene)` pair — and
test whether LLMs and agentic systems can serve as computational engines for it. The test
split is **dual-OOD**: perturbations *and* target genes are both disjoint from train, so
memorization is worthless and only transferable biological reasoning generalizes.

**Metric:** `mean(AUROC_de, AUROC_dir)` — predictions are graded (`prediction_up`,
`prediction_down`). `AUROC_de` ranks none-vs-DE by `up + down`; `AUROC_dir` ranks up-vs-down
by `up / (up + down)` over DE-positive rows. Accuracy does **not** apply.

## Where we stand

| Approach | Method | Score | Notes |
|---|---|---|---|
| Majority class | predict `none` (55.3%) | ≈ 0.553 | reference only (metric is AUROC, not accuracy) |
| **Track A — evidence prior** | functional-category direction prior (no LLM) | **0.529** (Kaggle LB; CV 0.534) | our real floor; ~0 CV↔LB gap; **direction carries the signal, DE-vs-none is nearly flat** |
| **Track B — agent harness (v1)** | multi-agent tool-use (direction-prior + GO-evidence tools) on `gpt-oss-120b` | local CV **0.675** → LB **0.488** | **did not transfer** — the agent abstained on ~72% of rows, submitting `0/0`; ties collapse the rank metric to ~random. Local CV was inflated ~0.19 over LB. |
| Public leaderboard (top) | — | ≈ 0.65 | on the same AUROC scale |

**Two findings drive the plan:**
1. **The direction axis carries the signal; DE-vs-none is nearly flat** — split optimization
   effort across the two sub-metrics, don't chase the aggregate.
2. **Local CV badly over-states leaderboard performance** (Track B: 0.675 CV → 0.488 LB). The
   agent's over-abstention (emitting `0/0`) deletes the prior's signal and creates rank ties.
   The fix is twofold: **never emit `0/0`** (fall back to the direction prior on every would-be
   abstention, guaranteeing ≥ the 0.529 floor), and **score, don't label** (emit a continuous
   DE-likelihood — only order matters for AUROC). And measurement must move onto a **dual-OOD
   validation split** that reproduces the real train/test disjointness, so CV stops lying.

## Approach

1. **Honest fitness signal first** — a dual-OOD validation split (perturbations + genes
   disjoint from the train portion) with a single `evaluate() → {auroc_de, auroc_dir, mean}`
   entry point. Every baseline (including the agent harness's 0.675) is re-scored here; a naive
   CV inflates.
2. **A self-improving trial loop** — a single-problem loop that proposes a candidate
   (a Track A prompt, then a Track B agent config), scores it on the OOD split, keeps per-trial
   execution traces, reflects on stagnation, and compounds an archive of what works. Fixed model
   throughout: `gpt-oss-120b` via a hosted OpenAI-compatible endpoint (leaderboard-legal — it is
   the competition's fixed model).
3. **Two tracks off one loop** — Track A optimizes the prompt of the fixed LLM; Track B
   optimizes tools + orchestration around it. Track B must beat the Track A result to justify
   its cost.
4. **Submission discipline** — spend the daily Kaggle budget only on candidates that beat the
   best-on-validation; track the public-LB − validation gap; select finals before the deadline.

## Plan (to 2026-07-22)

- **Now:** build the dual-OOD validation split (the loop's fitness signal); it exists to close
  the CV↔LB gap that inflated Track B by ~0.19.
- **First Track B fix (cheapest, highest value):** never emit `0/0` — fall back to the direction
  prior on every would-be abstention. This alone should recover ≥ 0.529 (the bar is "stop
  deleting the prior"). Then blend `α·agent + (1−α)·prior` (never-worse-than-prior by
  construction, α tuned on the OOD split).
- **Then:** stand up the trial loop against the OOD split; optimize Track A prompts, and evolve
  Track B toward **scoring, not labeling** (continuous DE-likelihood, killing the tie-mass
  failure at the root).
- **Close:** submission discipline → final selection.

## Risks & mitigations

- **Model access** → mitigated: the fixed `gpt-oss-120b` is reachable now via a hosted
  OpenAI-compatible endpoint; a local GPU box is a scale/backup path.
- **Validation ≠ leaderboard** → *realized* on Track B (0.675 CV → 0.488 LB). Mitigated going
  forward by the dual-OOD split that mirrors the real test structure; we track the LB−val gap on
  every submission and never trust CV alone.
- **Agent over-abstention** → *realized* (72% of rows `0/0` collapsed the LB to ~random).
  Addressed by a hard "never emit `0/0`, fall back to the prior" rule, a prior-blend floor, and a
  scoring-not-labeling reframe — validated on the OOD split.
