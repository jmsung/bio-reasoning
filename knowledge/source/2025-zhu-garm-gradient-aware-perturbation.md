---
source_url: https://doi.org/10.1101/2025.10.03.680360
source_type: papers
title: "Gradient-aware modeling advances AI-driven prediction of genetic perturbation effects"
author: Zhu & Jerby (Jerby Lab, Stanford)
retrieved: 2026-07-16
doi: 10.1101/2025.10.03.680360
---

# Gradient-aware modeling advances AI-driven prediction of genetic perturbation effects

**Authors:** Dixian Zhu, Livnat Jerby
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
Predicting the transcriptional effects of genetic perturbations across contexts
is a central challenge in functional genomics, and exhaustively profiling every
perturbation with Perturb-seq is infeasible. The authors present **GARM**
(Gradient Aligned Regression with Multi-decoder), an ML framework that uses
gradient-aware (pairwise) supervision to capture both absolute and relative
perturbational effects. Across multiple large-scale CRISPRi Perturb-seq datasets,
GARM consistently outperforms GEARS, scGPT, GenePert, and a coexpression linear
baseline for predicting responses to unseen perturbations within and across
cellular contexts. The paper also shows that widely used metrics (MSE, gene-ranking
correlation) overestimate performance — letting trivial models look predictive —
and introduces **perturbation-ranking (PrtR)** criteria that better reflect utility
for experimental design, plus an analysis of which genes are systematically easier
or harder to predict.

## Key contributions
- **Pairwise/gradient-aligned loss**: training on differences f(xi)−f(xj) vs.
  yi−yj is equivalent to learning the gradient of the target function and to
  optimizing Pearson correlation; a linearization drops cost from O(GP²) to O(GP).
- **Multi-decoder architecture (GARM)**: five decoders optimize different aspects
  (MAE mean, PrtR variance/trend per-gene, GenR variance/trend per-perturbation),
  then are reconciled into one prediction — no method-specific hyperparameter tuning.
- **PrtR evaluation criterion**: ranks, per gene, which perturbations most up- or
  down-regulate it — a more stringent, forward-genetics-relevant benchmark than GenR.
- **Exposes metric inflation**: a "PertMean" model predicting the training-average
  response for every perturbation can win on GenR, revealing GenR/MSE don't isolate
  perturbation-specific signal.

## Methods
Perturbation response y_p is defined at pseudo-bulk level as the mean log1p-TPM of
targeting cells minus the mean of all perturbed cells (control-referenced). GARM
uses FFNN encoders/decoders (4-layer, 1024-unit hidden, ELU) trained with Adam. It
was benchmarked against GEARS, scGPT, GenePert, and Coexpress, each tuned and run
over 5 seeds, on four CRISPRi genome-scale Perturb-seq datasets — HepG2, Jurkat,
K562, RPE1 (2,042–2,373 perturbations each), plus curated K562/RPE1. Two evaluation
settings: within-dataset (75/25 split) unseen-perturbation prediction, and
cross-dataset prediction into an unseen cellular context (12 splits, 6,641 shared
genes). Metrics: MSE, GenR (gene-ranking correlation), and PrtR (Pearson/Spearman),
plus AUROC/AUPRC for recovering the top-20% up/down perturbations per gene.

## Key results
- **Within-dataset PrtR**: GARM beats all methods on average PrtR-Pearson in all 6
  datasets, and per-gene it wins on 84.5%/87.0%/90.6%/89.9%/86.5%/72.5% of genes
  (Pearson) across HepG2/Jurkat/K562/RPE1/curated-K562/curated-RPE1.
- **Cross-context PrtR**: GARM significantly best in 3/4 datasets, winning on
  88.2%/92.0%/94.8%/92.0% of genes (Pearson) for HepG2/Jurkat/K562/RPE1.
- GARM was best under **AUROC and AUPRC in all 24** within-dataset PrtR evaluations
  and consistently best cross-dataset.
- PrtR is a harder task: avg Pearson 0.084–0.386 vs. GenR 0.168–0.639; the trivial
  PertMean model can top GenR, confirming metric inflation.
- **Gene predictability** is consistent across models: high-PrtR genes enrich for
  cell cycle, apoptosis, metabolism, antigen presentation; low-PrtR genes enrich
  for transcription factors, chromatin modifiers, and epigenetic regulators. Genes
  with larger expression variance across perturbations are easier to predict.

## Why it matters for our work
This paper is directly on-point for **Track A/B up/down/none perturbation-effect
prediction**. Its central warning — that gene-ranking correlation and MSE inflate
apparent skill and let a mean-predictor look competitive — mirrors our own
Track B lesson (over-abstention + a misleading small-CV score). PrtR reframes the
task as *ranking which perturbations move a target gene up or down*, which is
essentially our directional up/down/none call, and its AUROC/AUPRC top-20% framing
is a cleaner offline proxy than raw correlation. The pairwise/gradient-aligned loss
is a concrete, cheap (linear-cost) training trick we could layer onto a regression
head, and GARM's win over scGPT/GenePert is a useful data point for the Track C
foundation-model-vs-supervised debate.

## Limitations / open questions
- Preprint (bioRxiv, not peer-reviewed); operates at pseudo-bulk, not single-cell
  distributions.
- GARM is **not orthogonal** to other methods — genes hard for GEARS/scGPT stay
  hard for GARM, suggesting shared priors (coexpression, GO, text embeddings) are
  the bottleneck for a class of genes (TFs, chromatin/epigenetic regulators).
- Even GARM struggles to push low-variance / subtle-effect genes past PrtR ≈ 0.4;
  authors suggest better priors, protocols, and preprocessing are needed.
- All benchmarks are CRISPRi knockdown in cell lines; generalization to activation,
  combinatorial, or in vivo perturbations is untested here.
