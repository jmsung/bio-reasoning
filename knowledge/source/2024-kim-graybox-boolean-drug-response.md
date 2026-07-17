---
source_url: https://doi.org/10.1016/j.crmeth.2024.100773
source_type: papers
title: "A gray box framework that optimizes a white box logical model using a black box optimizer for simulating cellular responses to perturbations"
author: Kim, Han, Hopper et al.
retrieved: 2026-07-16
doi: 10.1016/j.crmeth.2024.100773
---

# A gray box framework that optimizes a white box logical model using a black box optimizer for simulating cellular responses to perturbations

**Authors:** Yunseong Kim, Younghyun Han, Corbin Hopper, Jonghoon Lee, Jae Il Joo, Jeong-Ryeol Gong, Chun-Kyung Lee, Seong-Hoon Jang, Junsoo Kang, Taeyoung Kim, Kwang-Hyun Cho (KAIST)
**Year:** 2024
**Venue:** Cell Reports Methods (2024), doi:10.1016/j.crmeth.2024.100773

## Abstract

Predicting cellular perturbation responses needs both accuracy and interpretable
insight into molecular regulatory dynamics. ML models are accurate but black-box;
Boolean/logical network models are interpretable but hard to fit because their
edge-weight search space is high-dimensional and discontinuous. The authors present
a "gray box" framework: a **white box** Boolean network supplies interpretable
topology, and a **black box** derivative-free optimizer — GREY, trained by
meta-reinforcement learning — fits the network's edge weights. GREY-optimized
logical models predict anti-cancer drug responses of cancer cell lines while
exposing the underlying regulatory mechanisms.

## Key contributions

- **Gray box framework** combining an interpretable Boolean network (white box) with a
  learned optimizer (black box), keeping interpretability while scaling to large networks.
- **GREY** (gradient-free optimizer trained by meta-RL to yield edge weights): a
  learning-to-optimize (L2O) optimizer specialized for Boolean-network edge weights.
- Multi-agent meta-RL architecture — GNNs produce node/edge/global features, one
  LSTM "agent" per edge (shared weights, independent hidden states), trained with DPPO.
- Drug-response core networks (DRCNs) auto-extracted from a pan-cancer core network
  built from Omnipath signed/directed edges + CancerGeneNet phenotype nodes.

## Methods

GREY was pre-trained (supervised) then RL-trained on **100,000 synthetic environments**
(random weighted-sum Boolean networks, 20–40 nodes); fitness = Pearson correlation
between simulated and ground-truth node fold changes; reward = fitness improvement.
For biology, DRCNs were built for three NCI-MATCH targeted drugs — afatinib (57 nodes),
trametinib (66), palbociclib (192 nodes / 655 edge weights). Cell-line mutation profiles
(COSMIC) set invariant node states; drug responses (GDSC2 viability AUC) are the ground
truth. Drug response = change in phenotype-node (proliferation/apoptosis) activity between
attractors before and after fixing drug-target nodes to −1.

## Key results

- GREY beat CMA-ES (SOTA derivative-free optimizer) in **sample efficiency**, with
  statistically significant higher fitness across all network scales (20–200 links).
- Trametinib DRCN: GREY reached fitness 0.3 in ~403 evaluations vs ~1,102 for CMA-ES
  (~3× more sample-efficient); scaled to the 655-edge palbociclib network.
- On 21 drugs (F1 vs SRMF, DeepCDR, LOBICO): GREY-optimized DRCNs scored **below** ML
  models SRMF/DeepCDR but **above** the logical model LOBICO — trading raw accuracy for
  mechanistic interpretability.
- In-house RNA-seq validation: for BT-474, 14 GREY-simulated node fold changes matched
  experiment vs only 5/42 for a random agent; for BT-20, 7 vs 1. Inferred biomarkers
  matched NCI-MATCH basket-trial marker genes.

## Why it matters for our work

This is a hybrid "prior-knowledge network + learned optimizer" recipe for the exact
prediction our challenge poses. The phenotype-node activity change gives a **signed**
response (decrease/increase/no-change) — directly analogous to the Track A/B up/down/none
direction call — and, unlike a pure ML predictor, the optimized Boolean model yields a
mechanistic trace of *why*, the kind of reasoning an LLM/agentic system is meant to
produce. It also demonstrates the interpretability-vs-accuracy trade-off (beats logical
LOBICO, trails ML DeepCDR) our track designs must weigh, and shows curated signed
networks (Omnipath, CancerGeneNet) as usable priors for grounding perturbation reasoning.

## Limitations / open questions

- Raw predictive accuracy trails black-box ML (SRMF, DeepCDR); the win is interpretability,
  not leaderboard score.
- Requires a hand-curated signed/directed prior network; DRCNs are deliberately kept small
  to keep Boolean attractor simulation tractable.
- Coarse readout — mutation profiles collapse to a few nodes (716 cell lines mapped to 57),
  and response is a phenotype-node activity change, not full transcriptome.
- Validated on three drugs / a handful of cell lines with in-house RNA-seq; broad
  cross-drug, cross-cell-line generalization is untested.
