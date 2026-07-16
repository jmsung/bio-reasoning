---
title: Track B — the agent underperformed its own prior (rank-metric abstention)
cites:
  - findings/track-a-eda.md
  - methods/pbio-agent-for-tracks.md
  - source/2026-bioreasoning-challenge-overview.md
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

## Fix direction (see backlog `track-b-*`)

Build the OOD val split first; then floor-to-prior / never-`0/0`; then blend
with the prior; then reframe the task as continuous scoring rather than 3-way
labeling (only order matters for AUROC).
