---
title: Track B — the agent underperformed its own prior (rank-metric abstention)
cites:
  - findings/track-a-eda.md
  - methods/pbio-agent-for-tracks.md
  - domains/ai-reasoning/source/2026-bioreasoning-challenge-overview.md
---

# Track B — the agent underperformed its own prior

**Result (2026-07-16):** the agentic Track B harness (DSPy ReAct, gpt-oss-120b
via OpenRouter, tools = `direction_prior` + train-data lookups + gene/STRING
lookups, graded `submit_graded` output) scored **Kaggle public LB 0.488** —
*below* the 0.529 Track A prior floor ([[track-a-eda]]) and far below its own
60-row leak-free CV of **0.675**. A negative result, and an instructive one.

## Root cause: over-abstention in a rank metric

The metric is `mean(AUROC_de, AUROC_dir)` — **rank-based**. The agent submitted
`prediction_up = prediction_down = 0` on **72% of the 1,813 rows** (1,307).
Those are ties at zero: they carry no rank information, so a 72% block of ties
drags AUROC to ≈0.5 (0.488). Only 506 rows carried any DE signal.

We *gave* the agent the `direction_prior` tool — the exact no-LLM signal that
scores the 0.529 floor — and it **threw the prior away** by abstaining. A dumb
baseline that emitted the prior's graded scores for every row would have beaten
our agent. The LLM's reasoning was net-negative: it degraded a floor-clearing
prior into a near-random submission.

This is the counterpoint to [[pbio-agent-for-tracks]], which argued the `none`
majority is "the whole game" and an abstain policy is the key lever. True — but
the policy overshot. Abstaining is only safe in an *accuracy* metric; in a
**rank** metric a tie is worse than a weak guess.

## Two durable lessons

1. **In a rank metric, never emit `0/0` — floor every prediction to the prior.**
   A tie carries no rank signal, so abstention is destructive, not cautious.
   When the agent has no opinion, fall back to the evidence prior's graded score
   (extend the parse-fail fallback to *all* would-be abstentions), or blend
   `α·agent + (1−α)·prior` so the output is never worse than the prior.
2. **A 60-row leak-free CV is untrustworthy for AUROC.** The CV→LB gap was 0.19
   and it *flipped the conclusion* (0.675 "beats floor" → 0.488 "below floor").
   Rank stability needs hundreds of rows with real class balance. Do not trust
   an offline number until the validation set is sized to the real test — this
   is exactly what the OOD-faithful val split is for.

## What was *not* the problem

Engineering was sound: 1% tool-fallback rate, the runaway-row guard held
(max-iters cap + prior fallback), full 1,813-row run cost **$2.90** (~10× under
the initial $20–40 guess). The failure was entirely modeling/policy — a useful
separation, because it says *don't polish the harness, fix the output policy.*

## Fix direction — outcomes (2026-07-16)

The plan was: OOD val split → floor-to-prior → blend → scoring-not-labeling.
Three are now measured:

- **Dual-OOD val split** — built (`holdout_split`, perts+genes disjoint; PR #14).
  Baselines on it: no-signal 0.500, evidence prior **0.533**. It reproduces the
  leaderboard (the eventual fix's LB↔OOD-val gap was **0.004**), so it is the
  trusted offline fitness gate — a 60-row CV is not.
- **floor-to-prior / never-`0/0`** — ✅ **works** (first Track B above the floor; the
  base every later direction lever builds on).
  Flooring every `(0,0)` tie to the pert's graded prior: **Kaggle LB 0.568**
  (PR #16, first Track B above the 0.529 floor), confirmed on OOD-val at **0.564**
  (PR #20). The full ladder: hard A/B/C 0.507 → graded-but-over-abstaining 0.488
  → floor-to-prior 0.568. The agent's ~28% signal rows add real lift *on top of*
  the recovered prior — reasoning helps once it can't delete the prior.
- **blend `α·agent + (1−α)·prior`** — ❌ **no gain; that lever exhausted** (PR #21).
  OOD-val α-sweep: best α=0.9 → 0.5654 vs floor-to-prior 0.5647 (+0.0007, noise).
  The agent's signal rows are already well-calibrated, so shrinking them toward
  the prior doesn't help; and a *raw* blend can't beat floor-to-prior by
  construction — it gives `(0,0)` ties only `(1−α)·prior` vs the full prior.
- **blend a learned model's *direction*** — ✅ **works: Kaggle LB 0.578**
  (2026-07-16, two-stage-de-dir). A *different* lever than the α-blend above: keep
  floor-to-prior's DE magnitude untouched but rank-average the **two-stage GO-term
  model's** direction into `up/(up+down)`. Beats floor-to-prior for every blend
  weight in (0,1); OOD-val 0.5647 → 0.5712 (w=0.7), LB 0.568 → **0.578** (+0.010).
  The two-stage DE axis is near-chance and stays unused; only its *direction* is
  complementary. So mixing predictions is not exhausted — mixing toward the
  *coarse prior* is; mixing in an *orthogonal learned signal* still lifts.
- **fuse a neighbour-retrieval *direction*** — ✅ **new offline best: OOD-val 0.5916**
  (feat/track-b-neighbour-dir-parity). The same neighbour-direction lever that took
  Track A to LB 0.585, applied to the floored Track B base via
  `fuse_neighbour_direction`: dir 0.570→0.624 (98% coverage), **+0.028** vs the floored
  base and **+0.020** vs the two-stage dir-blend (0.5712). **Kaggle LB 0.597** (2026-07-17, +0.019 over 0.578).
  Confirms "stronger learned direction" is the live Track B lever, not a dead end.
- **scoring-not-labeling** (continuous DE-likelihood) — still open.

**Takeaway:** floor-to-prior's DE ceiling is set by **evidence quality** (the
prior + better tools) — shrinking the agent toward the prior can't beat it. But
the **direction** axis is not capped there: each stronger direction signal lifts it —
two-stage GO (LB 0.578) and now neighbour-retrieval (**LB 0.597**, OOD-val 0.5916).
Remaining levers: better knowledge tools, scoring-not-labeling, and stronger learned
direction (the one that keeps paying).
