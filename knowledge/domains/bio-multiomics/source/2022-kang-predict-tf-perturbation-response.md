---
source_url: https://doi.org/10.1093/g3journal/jkac144
source_type: papers
title: "Predicting which genes will respond to transcription factor perturbations"
author: Yiming Kang et al.
retrieved: 2026-07-16
doi: 10.1093/g3journal/jkac144
---

# Predicting which genes will respond to transcription factor perturbations

**Authors:** Yiming Kang, Wooseok J Jung, Michael R Brent
**Year:** 2022
**Venue:** G3: Genes|Genomes|Genetics

## Abstract
The authors train ML models to predict, for a given transcription factor (TF), which genes will respond to perturbing that TF — without using any data from the perturbed cells, so predictive features cannot be consequences of the perturbation. Models are trained on perturbation-response data for a subset of TFs and tested on held-out TFs. In human cells, existing TF binding location data (ChIP-seq) has almost no detectable utility for predicting responsiveness; instead, features of the gene itself — its preperturbation expression level and expression variation — are highly predictive across all TFs. This shows some genes are intrinsically poised to respond and others are resistant, explaining why binding locations predict responses so poorly. Certain histone marks (H3K4me1, H3K4me3) carry modest predictive power, mainly downstream of the TSS, but far less than expression features.

## Key contributions
- Reframes the task as predicting *responsiveness to perturbation* (up/down/no response) from unperturbed-cell features, cross-validated across TFs so a TF's outcome can be predicted before any experiment on it.
- Uses SHAP values to attribute each prediction to individual features, quantifying what drives responsiveness.
- Establishes that in human cells, gene-intrinsic expression features — not TF binding maps — carry nearly all the signal.

## Methods
Features are aggregated over 100 bp subregions of each gene's regulatory DNA: TF binding location (yeast: calling cards + ChIP-exo; human: ENCODE ChIP-seq), histone marks, chromatin accessibility, dinucleotide frequency, plus gene expression level and (level-adjusted) expression variation. XGBoost gradient-boosted trees are trained with 10-fold cross-validation *by TF*, so predictions for each TF come from models that never saw its binding or response data (folds: ≥77,000 instances yeast, ≥392,000 human). Class imbalance is severe (median 2–7% of genes respond), so accuracy is AUPRC, benchmarked against random expectation (the responsive fraction) and against label-permuted null models.

## Key results
- On human K562, actual AUPRC was at least 2× random expectation for every TF, and >10× for several; 143/145 human TFs beat permuted-label null at P < 10⁻³.
- In human, a model *without* TF binding locations was as accurate as the full model, and a GEX-only model was almost as accurate; a binding-only model performed dramatically worse (no TF exceeded 2× random).
- Dropping enhancer + upstream-promoter features left accuracy essentially unchanged (mean AUPRC actually rose 0.005 and 0.001); GEX-only lowered mean AUPRC by only 0.033 (~12%).
- In yeast the opposite held: TF binding (calling cards / ChIP-exo) was the single most influential feature; binding signal mattered mainly within 500 bp upstream of the TSS.
- Histone marks were most influential downstream of the TSS but shifted predicted response probability by ≤0.02; a no-GEX model had low accuracy (median AUPRC 0.11).
- Even the best models were far from accurate predictors — high relative to chance but low in absolute terms.

## Why it matters for our work
Directly relevant to Track A/B, where we predict whether a gene responds (up/down/none) to a TF/gene perturbation. This paper's central lesson: gene-intrinsic features — baseline expression level and expression variation — are the dominant, TF-agnostic signal for responsiveness, while ChIP-seq binding maps add little in human cells. That argues for strong non-network baselines (a gene's own expression statistics) before investing in binding- or network-derived features, and it reframes "which genes respond" partly as an intrinsic poised-vs-resistant property. It also warns that response prediction has a low absolute accuracy ceiling with current data.

## Limitations / open questions
- Human ChIP-seq's low utility may partly reflect incomplete enhancer–gene maps and long perturbation-to-readout intervals, not a true absence of binding signal.
- Absolute accuracy stays low even with binding + epigenetic features; no model predicts responders with high precision.
- Proposed but untested fix: feed binding locations of *other* TFs (via network inference — NetProphet 2, Inferelator — or PPI maps) to capture indirect network effects.
