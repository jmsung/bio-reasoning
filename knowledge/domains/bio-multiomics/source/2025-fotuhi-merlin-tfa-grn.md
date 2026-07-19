---
source_url: https://doi.org/10.1101/2025.06.09.658650
source_type: papers
title: "Uncovering Functional Gene Regulatory Networks in Bulk and Single-Cell Data through Robust Transcription Factor Activity Estimation and Model-Guided Experimental Validation"
author: Alireza Fotuhi Siahpirani et al.
retrieved: 2026-07-16
doi: 10.1101/2025.06.09.658650
---

# Uncovering Functional Gene Regulatory Networks in Bulk and Single-Cell Data through Robust Transcription Factor Activity Estimation and Model-Guided Experimental Validation

**Authors:** Alireza Fotuhi Siahpirani, Sunnie Grace McCalla, Saptarshi Pyne, Caleb Dillingham, Rupa Sridharan, Sushmita Roy
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
Reconstructing genome-scale gene regulatory networks (GRNs) is hard because expression-based inference assumes a regulator's mRNA level tracks its protein activity, which post-transcriptional/translational processes often violate. Methods that estimate hidden transcription factor activity (TFA) from a prior network of TF→target edges relax this assumption, but noise in the prior degrades both TFA and the inferred GRN. The authors present MERLIN+P+TFA, which uses prior-knowledge-guided sparsity regularization to robustly estimate TFA and downstream GRNs. On simulated and real yeast, human, and mouse data — bulk and single-cell — it improves inferred-network quality, and regularized TFA benefits many other inference algorithms. They used the inferred mouse embryonic stem cell (mESC) GRN to prioritize regulators, experimentally validating 58 regulators and the targets of several TFs.

## Key contributions
- MERLIN+P+TFA: extends MERLIN+Prior with NCA-LASSO, an L1-regularized Network Component Analysis that weights prior edges by confidence for robust TFA estimation under noisy priors.
- Two-step pipeline: (1) estimate regularized TFA via NCA-LASSO; (2) infer GRN edges + gene modules with MERLIN+P (a dependency-network PGM) under stability selection.
- Shows regularized TFA is a modular add-on that improves diverse inference methods (GENIE3, TIGRESS, Inferelator, SCENIC, mLASSO-StARS) not originally built for TFA, in both bulk and scRNA-seq.
- Model-guided experimental validation loop on the mESC pluripotency network.

## Methods
NCA-LASSO iteratively estimates TFA and a connectivity matrix, using edge confidence in an L1 regression to select reliable prior edges instead of the naive pseudo-inverse of classic NCA. Evaluation used simulated networks (10/30/50% added/removed edges, uniform vs non-uniform edge-weight schemes), a yeast natural-variation dataset with motif priors, four mammalian cell lines (mESC, hESC, LCL, MCF7) with DNase-footprint-filtered motif priors, and six scRNA-seq datasets. Metrics: AUPR vs ChIP/knockout/knockdown gold standards, "predictable TFs," and F-score.

## Key results
- In simulation, unregularized NCA TFA–true TFA correlation fell 0.79→0.57→0.44 as prior noise rose 10→30→50%; NCA-LASSO recovered higher correlation and AUPR at every noise level, most on non-uniform edge weights.
- In yeast, MERLIN+P+TFA outperformed all methods across three gold standards; regularized TFA beat unregularized in 11/16 predictable-TF cases (2 ties).
- Mammalian: regularized TFA gave the best predictable-TF counts; MERLIN+P > MERLIN, confirming prior utility.
- mESC validation: 58 prioritized regulators tested by siRNA knockdown (Nanog readout); ~18–19 decreased pluripotency per cell line. 39/81 TF-target pairs (48%) showed significant expression change; 20/39 were predicted via TFA, 19 via expression — both modalities matter.
- scRNA-seq: SCENIC+RegTFA beat SCENIC and SCENIC+NTFA; TFA-including configs dominated top rankings.

## Why it matters for our work
GRN inference underpins the up/down/none directional prediction in Tracks A/B — knowing which TFs functionally drive a target gene is the causal backbone for predicting perturbation direction. This paper's core lesson is that priors and TF activity (not mRNA) improve directional target recovery, but only when the prior's noise is handled; naive priors hurt. It also stresses context-specific gold standards, cautioning against trusting generic benchmarks — echoing our own small-CV overfitting lesson.

## Limitations / open questions
- bioRxiv preprint; no DOI-registered peer review at retrieval time.
- Benefit of regularized TFA is method- and gold-standard-dependent (some small regressions on KD/ChIP for a few methods).
- Validation is mESC-specific; authors note the need for context-specific gold standards, implying current benchmarks under-estimate true precision.
