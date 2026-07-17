---
title: The direction ceiling is ~0.65 — equal-weight fusion can't beat the single best DIR channel
status: draft
cites:
  - findings/neighbor-retrieval-direction-lever.md
  - findings/direction-transfers-de-doesnt.md
  - findings/competitor-landscape.md
  - findings/track-a-eda.md
  - source/2026-bioreasoning-challenge-overview.md
---

# The direction ceiling is ~0.65 — equal-weight fusion can't beat the single best DIR channel

[[../home]] | [[../index]]

**Status: draft — from the `explore/dir-ceiling-probe` branch, 2026-07-17.**

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

## Caveat

This is a **lower bound**: pure-DIR-AUROC, equal-weight rank-fusion of the current channels. The
open question `direction_fusion` leaves is whether a *weighted* combiner (up-weighting neighbour-DIR)
clears 0.651 at all — re-run this probe with learned weights to close it.
