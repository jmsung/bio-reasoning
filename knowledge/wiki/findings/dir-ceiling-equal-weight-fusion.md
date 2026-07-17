---
title: The direction ceiling is ~0.65 — no fusion (equal-weight, weighted, or learned) beats the single best DIR channel
status: measured
cites:
  - findings/neighbor-retrieval-direction-lever.md
  - findings/direction-transfers-de-doesnt.md
  - findings/competitor-landscape.md
  - findings/track-a-eda.md
  - source/2026-bioreasoning-challenge-overview.md
---

# The direction ceiling is ~0.65 — no fusion (equal-weight, weighted, or learned) beats the single best DIR channel

[[../home]] | [[../index]]

**Status: measured — `explore/dir-ceiling-probe` (equal-weight) + `feat/weighted-direction-fuse`
(weighted + learned), 2026-07-17. Question closed.**

Bottom line: with DE disproven ([[direction-transfers-de-doesnt]]), rank-1 rides on
**direction**. We measured how high *fused* direction can go by rank-fusing all three
gate-passing DIR channels on the dual-OOD split — and **equal-weight fusion (0.642) is
below the single best channel, neighbour-DIR alone (0.651).** The naive direction
ceiling is ~0.65, well under the field's claimed 0.693.

## What we measured (`scripts/dir_ceiling_probe.py`, 5 seeds, 0.4/0.4 dual-OOD)

Standalone DIR-AUROC: neighbour-DIR **0.651 ± 0.047**, GO-DIR 0.595 ± 0.043,
embedding-DIR 0.574 ± 0.027.

Full subset lattice (fused DIR-AUROC, ranked):

| subset | DIR-AUROC |
|---|---|
| **neighbour** | **0.651** |
| GO + neighbour | 0.648 |
| neighbour + embedding | 0.644 |
| GO + neighbour + embedding | 0.642 |
| GO + embedding | 0.599 |
| GO | 0.595 |
| embedding | 0.574 |

Marginal contribution vs neighbour-DIR alone (equal-weight): **+GO −0.002, +embedding
−0.007, +both −0.009**. Every arm added to the strongest channel *drags the fusion down*.

## Why equal-weight fusion loses here

`fuse()` rank-normalizes each channel to (0,1) and **averages** them. Averaging a strong
channel (neighbour 0.651) with weaker ones (GO 0.595, embedding 0.574) pulls the combined
ranking toward the weak channels' noise — the mean of unequal-quality rankers sits below
the best ranker. Diversity does **not** rescue this: embedding-DIR is nearly independent of
neighbour-DIR (Spearman **corr 0.19**; [[neighbor-retrieval-direction-lever]]), yet at only
0.574 standalone it cannot convert that independence into a lift under equal weights. **Low
correlation earns a fuse *slot*, but only a channel strong enough to survive the averaging
actually lifts the fusion.**

## Implications

1. **`fuse-direction-channels` must weight, not average.** Equal-weight rank-fusion is a net
   drag; the only path to beating 0.651 is a **weighted / learned combiner that up-weights
   neighbour-DIR** heavily (cf. `feat/de-dir-weight-tuning`, where the neighbour-vs-model
   weight plateaued at w≈0.75). Even then, headroom is small — the other channels top out at
   ~0.60.
2. **Direction alone likely caps ~0.65.** With DE pinned ~0.55 and fused DIR ~0.65, the
   honest mean-AUROC ceiling of the current lane is ~0.60, below the field's unverified
   0.693 ([[competitor-landscape]]). Reaching rank-1 probably needs a *new signal source*
   (Perturb-seq expression data — Replogle/PerturbQA), not more direction channels.
3. **Decision:** push neighbour-DIR to its weighted best, **submit once, and read the real
   LB gap** before investing in the expensive data lane — exactly the strategic fork in the
   rank-1 plan.

## Independently confirmed by `feat/fuse-direction-channels` (#37)

The production fusion entry point (`bio_reasoning.models.direction_fusion.fuse_direction_channels`,
a CFA-gated N-channel fuse over `model + admitted candidates`) reached the same conclusion from
the other side: the **2-way** fusion (GO + neighbour) reproduces the +0.027 / LB-0.585 lift, but
the **3-way** (+embedding-DIR) adds **no marginal lift** — "direction saturated at 2 channels;
**CFA corr-diversity ≠ marginal lift**." Same lesson, two setups: a low-correlation channel earns
a gate slot but only lifts if it is strong enough to survive fusion. Note #37's gate is permissive
(`max_abs_corr=0.9`), so it admits all three — the *gate* does not prevent the drag; **channel
strength does.**

## Closed by `feat/weighted-direction-fuse` — weighting and a learned stacker both confirm ~0.65

The open question ("does a *weighted* or *learned* combiner clear 0.651 at all?") is now settled —
`scripts/weighted_direction_fuse.py`, same 5-seed dual-OOD split:

- **Weighted rank-fusion** (up-weight neighbour-DIR, GO/embedding at 1): a *shallow interior
  optimum* at w≈4 → **0.660**, +0.010 over neighbour-alone but **within seed σ≈0.05**. Not a
  pure asymptote — the weak channels help as tie-breakers on neighbour-DIR's ~2% uncovered rows —
  but not a robust win.
- **Learned stacker** (`models/direction_stacker.py`: logistic + pairwise interactions, evaluated
  **out-of-fold within val DE rows** so it's leak-free): **0.641 ± 0.051** — *below* neighbour-alone
  (−0.010) and weighted-best (−0.019). Non-linearity does **not** extract complementary direction
  signal; adding the weak channels via a learned model slightly hurts (noise injection).

**Verdict: ~0.65 is the hard direction ceiling.** No fusion — equal-weight (0.642), weighted
(0.660, noise), or learned (0.641) — robustly clears the single best channel, neighbour-DIR
alone (0.651). The weak channels (GO-DIR 0.595, embedding-DIR 0.574) carry no direction signal
neighbour-DIR lacks. **The direction lane is closed:** with DE pinned ~0.55, the honest
mean-AUROC ceiling is ~0.60 < the field's unverified 0.693. Next = push neighbour-DIR's weighted
best (w≈4, ~0.66), **submit once, read the real LB gap**, then decide the Perturb-seq data lane
(the `perturb-seq-data-lane-decision` backlog item) —
rank-1 by direction alone is not on the table.
