---
source_url: https://doi.org/10.1038/s41540-025-00504-2
source_type: papers
title: "Gene regulatory network inference during cell fate decisions by perturbation strategies"
author: Qing Hu et al.
retrieved: 2026-07-16
doi: 10.1038/s41540-025-00504-2
---

# Gene regulatory network inference during cell fate decisions by perturbation strategies

**Authors:** Qing Hu, Xiaoqi Lu, Zhuozhen Xue, Ruiqi Wang
**Year:** 2025
**Venue:** NPJ Systems Biology and Applications

## Abstract
This work presents a computational framework that infers gene regulatory network
(GRN) topologies and quantifies how they differ across cell fate states, using
data collected before and after systematic perturbations. Building on Modular
Response Analysis (MRA), the authors compute a *local response matrix* for each
cell state whose entries encode both the direction and intensity of direct
regulations between molecules. Statistical resampling (confidence intervals) is
used to enforce network sparsity and remove the confounding effect of
perturbation degree, and a *differential analysis* (relative local response
matrix) then identifies which regulations are critical in each state and which
states dominate a given regulation. The epithelial-to-mesenchymal transition
(EMT) core network across epithelial (E), hybrid (H), and mesenchymal (M) states
serves as the validation example, with inferred networks largely matching the
ground-truth ODE model and experimental literature.

## Key contributions
- Extends MRA to the multi-state setting: infers a distinct network topology per cell fate rather than a single static network.
- Introduces the **redefined local response matrix** using confidence intervals over resampled perturbations to enforce sparsity and make inference robust to perturbation degree/distribution.
- Introduces the **relative local response matrix** for differential analysis — ranks which regulations are dominant in which state.
- Derives the wild-type (WT) local response matrix analytically from the governing ODEs as a ground-truth check.

## Methods
For each cell state the local response matrix is computed numerically from
steady-state expression data before/after perturbations; matrix entries reflect
regulation strength (larger magnitude = stronger regulation) and sign
(activation vs. inhibition). Because small true coefficients are sensitive to
perturbation magnitude, the method resamples across multiple perturbation types
and keeps an edge only if the 95% confidence interval of its coefficient
excludes zero — yielding the sparse "redefined" matrix. Differential analysis
normalizes each coefficient by its total across states to get the relative
matrix, from which regulations above a 1/3 threshold are called dominant. The
approach is model-independent (matrices come from data), imposes no limit on
network size, and applies to single-cell, experimental, or simulated data.

## Key results
- On the 7-node EMT network (TGF-β, snail1, SNAIL1, miR-34, zeb, ZEB, miR-200), the inferred topology closely matched the true ODE-defined network across E, H, and M states, with a single missed edge (ZEB→miR-34, L46) whose true intensity is near zero and thus absorbed into the confidence interval.
- Inferred regulations agreed with known EMT biology, e.g., double-negative loops between SNAIL1/miR-34 and ZEB1/miR-200 and miR-200 inhibition of TGF-β.
- Differential analysis recovered state-specific dominant regulations "almost exactly consistent" with the reference model: e.g., miR-200⊣TGF-β and miR-200⊣ZEB dominate E/H states; TGF-β→snail1 and ZEB⊣miR-200 are critical in the M state.
- Unlike GENIE3 (no edge strength) or PIDC/PPCOR (no directionality), this method recovers signed, weighted, directed edges.

## Why it matters for our work
The BioReasoning Challenge asks systems to predict directional regulatory effects
(Track A/B up/down/none). This paper is a perturbation-grounded, causal
alternative to the correlation- and ML-based GRN inference methods elsewhere in
our wiki: it derives *signed, directed, quantitative* edges directly from
before/after perturbation data — exactly the up/down/none distinction our tasks
require — and formalizes how perturbation magnitude and noise corrupt weak-edge
calls (relevant to our over-abstention failure mode on Track B). Its
state-specific "relative response" idea offers a principled way to reason about
context-dependent regulation, and its MRA framing is a candidate baseline or
sanity check for causal edge direction that does not depend on a foundation
model.

## Limitations / open questions
- Validated only on a small (7-node) synthetic EMT network with data simulated from a known ODE model; not demonstrated on real high-dimensional single-cell perturbation data.
- Requires *systematic* perturbations and near-steady-state measurements per state — demanding for genome-scale or real experimental settings.
- Fails on genuinely weak regulations (true coefficient ≈ 0), which get pruned by the CI test — a precision/recall tradeoff at the sparsity threshold.
- The 1/3 dominance threshold and choice of perturbation type are somewhat heuristic; scalability to hundreds/thousands of genes is asserted but not shown.
