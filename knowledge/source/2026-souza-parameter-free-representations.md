---
source_url: https://doi.org/10.64898/2026.02.11.705358
source_type: papers
title: "Parameter-free representations outperform single-cell foundation models on downstream benchmarks"
author: Souza & Mehta
retrieved: 2026-07-16
doi: 10.64898/2026.02.11.705358
---

# Parameter-free representations outperform single-cell foundation models on downstream benchmarks

**Authors:** Huan Souza, Pankaj Mehta
**Year:** 2026
**Venue:** bioRxiv (preprint)

## Abstract
scRNA-seq data exhibit strong, reproducible statistical structure, motivating large
transformer-based foundation models (e.g. TranscriptFormer) that embed genes into a
latent space and post SOTA on cell-type classification, disease-state prediction, and
cross-species learning. The authors ask whether the same performance can be reached
without deep learning. Using simple, interpretable pipelines built on careful per-cell
normalization and linear methods, they match or beat foundation models across the
standard single-cell benchmarks — including *outperforming* them on out-of-distribution
tasks with novel cell types and organisms absent from training. They argue cell identity
in current benchmarks is largely captured by linear representations of gene expression.

## Key contributions
- Head-to-head evidence that parameter-free linear pipelines equal or beat scRNA-seq foundation models (esp. TranscriptFormer) on four downstream tasks.
- Reuses **scTOP**: per-cell rank/z-score normalization (kills batch effects), pseudo-bulk source-type basis, classify by largest non-orthogonal projection — no free parameters, no training.
- A geometric argument (PCA vs Isomap) that biologically-realized cells occupy an approximately *linear* subspace, explaining why extra model expressivity buys nothing.

## Methods
Cross-species annotation used scTOP on the 8-mammal, 7-cell-type spermatogenesis dataset
(restricting to orthologs; ~14k shared genes vs 34,168 human). For noisier human
annotation (Tabula Sapiens 2.0) they extended the pipeline with ANOVA gene selection (top
20,000), a second standardization, PCA (top 220 components fit on train only), then a
logistic-regression classifier — mirroring the FM benchmark protocol. Disease-state
(SARS-CoV-2 infected vs not) added Leiden clustering (~15 clusters) with a *local*
logistic-regression classifier per cluster. TF–gene regulation used a PMI-style enrichment
score on normalized profiles, validated against STRING PPIs.

## Key results
- **Cross-species:** scTOP beats TranscriptFormer (TF-exemplar, TF-Metazoa) macro-F1 across all 8 species, including evolutionarily distant platypus; TF transfer to non-primates was weak (F1 < 0.5).
- **Evolutionary signal:** normalized species-level expression vectors show cosine-similarity vs evolutionary-distance Spearman R = −0.876, a much stronger signal than TF embeddings.
- **Human cell-type (Tabula Sapiens 2.0):** mean macro-F1 = 0.899 vs 0.910 / 0.907 for TranscriptFormer variants (near-SOTA); macro-F1 > 0.8 in 24 of 31 tissues, >0.9 for over half of cell types.
- **Disease state (SARS-CoV-2):** local-classifier pipeline macro-F1 = 0.862, *exceeding* foundation models.
- **Geometry:** for the high-quality spermatogenesis data, Euclidean vs Isomap-geodesic distance correlation > 0.9 (vs weak for a curved Swiss-roll control) → data is near-linear.

## Why it matters for our work
Directly informs Track C foundation-model strategy: it is fresh (2026) evidence that
scRNA-seq FMs like TranscriptFormer do **not** clearly beat cheap, parameter-free linear
baselines on the standard atlas benchmarks, and are actually *worse* out-of-distribution.
It pairs with Ahlmann-Eltze (perturbation) to make the case that a strong linear/normalization
baseline should be our default reference before reaching for an open-weights FM — and that
careful per-cell normalization + feature selection may carry more signal than embedding
choice. For gene-regulation strategy it shows TF–gene links can be recovered from
conditional co-expression alone, no latent model required.

## Limitations / open questions
- Compares against *reported/benchmark-portal* FM numbers, not always re-run end-to-end; only 5 tissues had public FM benchmarks for direct comparison.
- Ortholog restriction is "inherently lossy" (drops ~20k human genes) — unclear effect on harder transfers.
- Benchmarks tested are classification/annotation; says little about generative or true perturbation-response prediction where non-linearity may matter more.
- The "cells live on a linear subspace" claim is validated mainly on high-quality, low-noise data; noisier atlases needed denoising to work.
