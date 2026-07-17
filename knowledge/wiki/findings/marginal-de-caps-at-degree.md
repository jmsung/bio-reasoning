---
title: Marginal DE caps at STRING degree (~0.536) — essentiality is redundant, static DE route exhausted
status: measured
cites:
  - findings/direction-transfers-de-doesnt.md
  - findings/curated-edges-fail-de-axis.md
  - findings/housekeeping-transfer-hypothesis.md
---

[[../home]] | [[../index]]

# Marginal DE caps at STRING degree (~0.536)

**Status: draft — from `feat/marginal-property-de` then `feat/richer-marginal-de`,
2026-07-16.** The *marginal* DE hypothesis (per-symbol breadth × responsiveness,
not the pairwise interaction that killed the five earlier channels) produces the
**first above-chance DE signal** — but it caps at STRING degree, and a second
marginal (gene essentiality) adds nothing because it is collinear with degree.

## The arc

The five failed DE channels were all **pair-interaction** (does *this* pert–gene
edge exist: CollecTRI, STRING 1-hop, STRING 2-hop, neighbour-retrieval, char/prefix
family — all ~chance, [[curated-edges-fail-de-axis]]). The marginal hypothesis is
orthogonal: some perts are broadly disruptive, some genes broadly responsive,
independent of the pair. The transferable proxy is per-symbol network connectivity
(STRING interaction degree), which exists for unseen val symbols too, so it survives
the dual-OOD split where a train-derived DE rate would leak.

## What we measured (dual-OOD `holdout_split`, seeds 0–4)

Logistic head on marginal features, standalone DE-AUROC; chance 0.50, CFA bar 0.55.

| Head | Features | DE-AUROC | Verdict |
|---|---|---|---|
| degree-only | `[log1p(pert_deg), log1p(gene_deg)]` | **0.536 ± 0.007** | first above-chance; below 0.55 gate |
| + essentiality | `+ [pert_ess, gene_ess]` (DepMap ternary) | **0.534 ± 0.006** (Δ −0.001) | no lift — essentiality redundant with degree |

- Degree coverage 89.4%; essentiality coverage only 15.3% (DepMap common-essential +
  nonessential controls; the continuous 450 MB gene-effect matrix was skipped).
- Fusing the degree-only marginal DE into the two-stage model lifts OOD-val mean
  **+0.008 ± 0.004** (all 5 seeds positive) — the first *DE-axis* gain of the whole
  investigation, though modest vs the +0.027 direction win. **Not submitted** (+0.008
  ≈ the +0.004 weight-tuning call; Kaggle quota preserved).

## Why essentiality adds nothing

Common-essential genes are **high-degree STRING hubs**, so gene essentiality is
collinear with the degree feature already in the head — the responsiveness signal it
was meant to carry is already captured by `degree`. A second *connectivity-correlated*
marginal cannot move a head that already has connectivity.

## Implications

1. **Marginal DE is a real but small and capped lever (~0.536, +0.008 fused).** It
   nuances "DE is dead" ([[direction-transfers-de-doesnt]]): the axis is not 100% flat
   — a faint marginal-connectivity component exists that pairwise interaction lacks —
   but it is capped at what STRING degree captures.
2. **The static/data DE route is exhausted.** Two connectivity marginals (degree,
   essentiality) both cap at 0.536; six pairwise channels are chance. Every static
   feature, curated edge, retrieval, and external annotation has now failed the DE
   axis for the same reason — consistent with [[direction-transfers-de-doesnt]].
3. **The only untried DE crack is model-based**: token-logprob self-consistency over
   {up, down, none} (renormalised answer-token probabilities), which needs a logprob
   endpoint — pursued on the separate `feat/de-logprob-self-consistency` branch, not
   more static features.
4. **The fixed 0.55 standalone CFA gate is too strict for the DE axis** when the
   incumbent DE channel is chance (~0.50): a 0.536 channel still fuses positive. Judge
   DE channels by fused Δmean, not the standalone bar.

## See also

[[direction-transfers-de-doesnt]] · [[curated-edges-fail-de-axis]] ·
[[housekeeping-transfer-hypothesis]]
