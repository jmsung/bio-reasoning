# BioReasoning Challenge 2026 — Progress Report

*Maintained per-PR via `/worktree-done` (step 5e proposes report-worthy additions on each merge).*
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
| **Track A — evidence prior** | functional-category direction prior (no LLM) | **0.529** (Kaggle LB; CV 0.534) | ~0 CV↔LB gap validates the split; **direction carries the signal, DE-vs-none is nearly flat** |
| **Track B — agent harness** | multi-agent tool-use (direction-prior + GO-evidence tools) on `gpt-oss-120b` | **CV 0.675** | clears the prior floor; to be re-scored on the honest dual-OOD split |
| Public leaderboard (top) | — | ≈ 0.65 | on the same AUROC scale |

**Key empirical finding:** the direction axis (up vs down) carries real, functionally-grounded
signal; the DE-vs-none axis is close to flat. Optimization effort should be split across the
two sub-metrics rather than chasing an aggregate.

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

- **Now:** build the dual-OOD validation split (the loop's fitness signal) and re-score the
  0.675 honestly.
- **Then:** stand up the trial loop against that split; optimize Track A prompts first.
- **Then:** extend the loop to Track B; the current highest-value lever is the agent's
  **over-abstention** (it calls ~90% `none` vs a ~55% true DE rate) — loosening the abstain
  policy should recover direction/DE signal.
- **Close:** submission discipline → final selection.

## Risks & mitigations

- **Model access** → mitigated: the fixed `gpt-oss-120b` is reachable now via a hosted
  OpenAI-compatible endpoint; a local GPU box is a scale/backup path.
- **Validation ≠ leaderboard** → mitigated by the dual-OOD split that mirrors the real test
  structure; we track the LB−val gap on every submission.
- **Agent over-abstention** → the leading Track B iteration; addressed by relaxing the abstain
  threshold and validating against the current best.
