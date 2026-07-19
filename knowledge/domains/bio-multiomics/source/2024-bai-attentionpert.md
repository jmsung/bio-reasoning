---
source_url: https://doi.org/10.1093/bioinformatics/btae244
source_type: papers
title: "AttentionPert: accurately modeling multiplexed genetic perturbations with multi-scale effects"
author: Ding Bai et al.
retrieved: 2026-07-16
doi: 10.1093/bioinformatics/btae244
---

# AttentionPert: accurately modeling multiplexed genetic perturbations with multi-scale effects

**Authors:** Ding Bai, Caleb N. Ellington, Shentong Mo, Le Song, Eric P. Xing
**Year:** 2024
**Venue:** Bioinformatics (Vol. 40, ISMB 2024 proceedings)

## Abstract
AttentionPert is an attention-based neural network that predicts single-cell gene expression under single- and multi-gene genetic perturbations, including perturbations never seen in training. It models perturbation effects at two scales: a global, nonuniform system-wide impact (PertWeight) and a localized disturbance propagated through a gene–gene similarity network (PertLocal). Following GEARS, it predicts an expression *shift* added to a sampled control cell. Across three CRISPRi/a datasets it beats the prior SOTA (GEARS) on differential-expression accuracy, most notably in the hardest out-of-distribution (OOD) case where none of the co-perturbed genes appear in training.

## Key contributions
- Two-encoder multi-scale design: **PertWeight** (multi-head attention over Gene2Vec-initialized gene embeddings, capturing uneven global effects) + **PertLocal** (t-hop SGConv over an augmented Gene Ontology graph, capturing local effects).
- A **nonadditive (NA)-bias** module in PertLocal that learns nonlinear co-effects of multiplexed perturbations, replacing GEARS's cross-gene layer (which is dropped).
- Uses pretrained **Gene2Vec** embeddings (size 200) rather than GEARS's random initialization; prunes the GO graph to only genes actually present in each dataset.

## Methods
Inherits GEARS's preprocessing (pair each control cell with a post-perturbation cell), shift-prediction formulation, and combined auto-focus + direction-aware loss. The novel part is the shift predictor g_θ: PertWeight and PertLocal encodings are summed and passed to a simplified linear (gene-specific) decoder with no cross-gene layer. The augmented GO graph adds minimum-weight virtual edges between disconnected gene pairs so the network is fully connected. Trained 20 epochs, batch 128, Adam lr 1e-3; 5 random inits over 5 splits of each dataset.

## Key results
- Evaluated by **MSE on top-20 DE genes**, rel-MSE (vs Ctrl baseline), and Pearson ρ_Δ of predicted vs true expression shift across all genes. Baselines: Ctrl, CPA, GEARS.
- **Norman** (131 two-gene perturbations): outperforms all baselines in seen 2/2, seen 1/2, and seen 0/2 scenarios; wins on **all 9 seen-0/2 (fully OOD) perturbations** and on **~80% (63/79) of tested two-gene perturbations** in Split 1 vs GEARS.
- **RPE1** (1543 perturbations) and **K562** (1092 perturbations), each >160k cells: beats all baselines on all metrics, robust across all 5 splits.
- Makes fewer direction and magnitude errors on top-20 DE genes; NA-bias improves prediction on nonadditive genes. Ablations show each of the three GEARS-differences and each encoder contributes.

## Why it matters for our work
Directly relevant to Track A/B up/down/none prediction: AttentionPert predicts the *direction and magnitude* of perturbation-induced expression shifts and reports OOD (unseen-gene) performance, exactly the generalization regime the challenge tests. It is a strong GEARS-successor baseline and a source of transferable design ideas — Gene2Vec-initialized gene embeddings, GO-graph message passing, and explicit modeling of nonadditive multi-gene co-effects — for our perturbation-response models.

## Limitations / open questions
- Evaluated only on three GEARS-preprocessed screens; no cross-dataset/cross-cell-type transfer test.
- Relies on GEARS preprocessing and GO priors, so it inherits their coverage limits; genes absent from the GO graph are hard to place.
- Predicts mean per-condition expression, not full single-cell distributions or cell-state heterogeneity.
- Two-gene perturbations only (no 3+); Norman OOD set is small (9 seen-0/2 cases), limiting statistical power on the headline OOD claim.
