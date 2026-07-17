---
title: Track A error-structure — the incumbent's failure is DE, uniformly, and coverage is maxed
type: findings
status: measured
cites:
  - findings/track-a-eda.md
  - findings/direction-transfers-de-doesnt.md
  - findings/dir-ceiling-equal-weight-fusion.md
  - findings/neighbor-retrieval-direction-lever.md
  - findings/marginal-de-caps-at-degree.md
---

[[../home]] | [[../index]]

# Track A error-structure — the incumbent's failure is DE, uniformly

**Status: measured** — from `analysis/track-a-error-structure`
(`scripts/track_a_error_structure.py`, `eval/error_structure.py`).

We had run many AUROC A/B tests but never dissected *where* our best pipeline is
wrong on the data. This is the error-analysis EDA of the **incumbent** — two-stage
GO DE + neighbour-fused direction (LB 0.585, roadmap #14) — on the dual-OOD holdout
(pooled `holdout_split` seeds 0–2, 3,566 rows). It moves the axis-asymmetry claim of
[[direction-transfers-de-doesnt]] from a data prior to a **measured property of our
own predictions**, and rules a lever out.

## Reproduction (the harness is faithful)

Pooled dual-OOD mean **0.584** — DE **0.510**, DIR **0.658** — matches the documented
OOD-val ~0.588 / DIR 0.651. So the dissection below is of the real incumbent, not a
weaker stand-in.

## 1. DE is the gap, and it is at chance everywhere

- The metric is `mean(AUROC_de, AUROC_dir)`. DE sits at **0.510** (chance); DIR at
  **0.658**. DE holds **59%** of the total remaining gap — it is the dominant lever.
- **DE is at chance in every perturbation category** (housekeeping 0.495, other 0.520,
  immune 0.537). No slice of the data carries a usable DE signal for the incumbent.
  This sharpens [[marginal-de-caps-at-degree]] and [[direction-transfers-de-doesnt]]:
  the failure is not "DE is weak on average with a good sub-population" — it is
  **uniformly absent**. Subset/gating tricks won't recover it; only a fundamentally
  new DE signal will.

## 2. Direction works, and immune is the most learnable slice

Per-category DIR-AUROC (DE rows only):

| pert category | n | de_rate | up_frac_of_de | AUROC_de | AUROC_dir |
|---|---|---|---|---|---|
| housekeeping | 1869 | 0.453 | 0.732 | 0.495 | 0.612 |
| other | 1055 | 0.434 | 0.740 | 0.520 | 0.633 |
| immune | 642 | 0.441 | 0.562 | 0.537 | **0.697** |

- The EDA's **category→direction** claim holds *in predictions*: immune knockdowns
  skew targets **down** (up-fraction 0.56 vs housekeeping 0.73) and are the **most
  directionally predictable** (0.697). Housekeeping direction is the weakest (0.612).
- But DIR is already at 0.658 against the ~0.65 ceiling ([[dir-ceiling-equal-weight-fusion]]),
  so the headroom is thin. A category-conditioned direction head (extra weight on the
  immune slice) is a **small** lever (order +0.01–0.02 on the DIR half), not a crack.

## 3. Ruled out: neighbour coverage is not a lever

Neighbour-direction already covers **98.9%** of rows (only 40 uncovered). Covered DIR
0.659 vs uncovered 0.426 — covered rows are where the signal is, and we already cover
essentially all of them. **Expanding the STRING graph / retrieval coverage cannot move
the score** ([[neighbor-retrieval-direction-lever]] delivered its lift; it is spent).

## 4. Minor: confident-direction calls are poorly calibrated

39% of DE rows get a confident direction call (`P(up|DE)` outside [0.25, 0.75]); **35%
of those are wrong**, roughly uniform across category. Abstaining / shrinking confident-
but-uncertain calls is a small refinement — and [[track-b-abstention-failure]] warns
that over-abstention backfired on Track B, so treat it cautiously.

## Ranked levers (replacing blind A/B tests)

1. **Crack the DE axis (rank-1, high value / historically hard).** 59% of the gap,
   uniformly at chance. Every static/curated/self-consistency DE route has failed
   ([[marginal-de-caps-at-degree]], [[curated-edges-fail-de-axis]],
   [[llm-self-consistency-fails-de-axis]], [[contrastive-de-core-assessment]]). The new
   constraint: DE is at chance across *all* categories, so the crack must be a new
   *global* signal, not a sub-population gate.
2. **Squeeze direction on the immune slice (small).** Category-conditioned DIR head;
   ~+0.01–0.02 on the DIR half, capped by the ~0.65 ceiling.
3. **Direction calibration / selective abstention (small, risky).** 35% confident-wrong;
   mind the Track B abstention lesson.
4. **Do NOT** invest in neighbour/graph coverage expansion — already 98.9%.

## Method caveats

Categories are GO:BP keyword matches (`features/gene_function.classify`) — hypothesis-
grade, as in [[track-a-eda]]. AUROCs pooled over three dual-OOD seeds; per-category
counts (esp. immune n=642) are modest, so the 0.697 immune DIR carries seed noise
(±~0.02). Reproduce: `uv run --group eval python scripts/track_a_error_structure.py`.
