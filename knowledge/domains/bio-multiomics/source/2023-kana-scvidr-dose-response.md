---
source_url: https://doi.org/10.1016/j.patter.2023.100817
source_type: papers
title: "Generative modeling of single-cell gene expression for dose-dependent chemical perturbations"
author: Kana, Nault, Filipovic, et al.
retrieved: 2026-07-16
doi: 10.1016/j.patter.2023.100817
---

# Generative modeling of single-cell gene expression for dose-dependent chemical perturbations

**Authors:** Omar Kana, Rance Nault, David Filipovic, Daniel Marri, Tim Zacharewski, Sudin Bhattacharya
**Year:** 2023
**Venue:** Patterns 4(8):100817

## Abstract

Single-cell sequencing exposes the heterogeneity of cellular response to chemical
perturbations, but exhaustively testing every cell type × chemical × dose combination is
infeasible. The paper introduces **scVIDR** (single-cell variational inference of
dose-response), a variational-autoencoder (VAE) model that predicts both single-dose and
multi-dose single-cell gene expression responses better than prior methods. scVIDR
generalizes across mouse hepatocytes, human blood cells, and cancer cell lines, exposes an
interpretable latent space via a regression model, and assigns each cell a continuous
"pseudo-dose" ordering cells by chemical sensitivity — aiming to cut repeated animal
testing across tissues, chemicals, and doses.

## Key contributions

- **scVIDR**: extends scGen-style latent-space vector arithmetic on a VAE to predict
  *cell-type-specific* differential expression and to extrapolate *high doses from less data*.
- A **linear/regression model over latent deltas** (δ) that both predicts the perturbation
  shift for held-out cell types and makes the latent space interpretable at the gene level.
- **Pseudo-dose**: a per-cell continuous score ordering cells by perturbation sensitivity.
- Demonstrated across three biological regimes: in vivo mouse liver (TCDD), IFN-β PBMCs,
  and the sci-Plex 188-drug multiplexed cancer-cell-line screen.

## Methods

scVIDR trains a VAE on control and treated cells, computes the difference between control
and treated latent centroids (δ) for observed cell types, and fits a linear regression to
predict δ for an unseen cell type; the decoder maps the predicted latent shift back to
expression. For multi-dose prediction it **log-linearly interpolates along δ** between
control and the highest dose. Performance is quantified as R² of mean per-gene expression
(via scipy `linregress`) over the top 5,000 highly variable genes (HVGs) and top 100 DEGs
(Scanpy `rank_genes_groups`), with cell-resampling (80%, 100×) and a one-sided Mann-Whitney
U test versus scGen, scPreGAN, and CellOT.

## Key results

- Held-out TCDD-treated mouse portal hepatocytes: scVIDR reached **R² = 0.92 on HVGs** and
  **R² = 0.81 on DEGs**, and significantly beat scGen/scPreGAN/CellOT across all liver cell
  types (p < 0.001).
- IFN-β PBMCs: scVIDR led on HVGs (**R² = 0.97** vs 0.92/0.77/0.66) and DEGs (0.96 vs
  0.86/0.80/0.84 for scGen/scPreGAN/CellOT).
- Cross-species LPS6 prediction in rat from pig/rabbit/mouse: scVIDR **R² = 0.92** (HVGs) vs
  scGen 0.91, scPreGAN 0.63, CellOT 0.23.
- 8-dose TCDD liver response: scVIDR significantly outperformed scGen on DEGs for doses
  > 0.3 μg/kg and recovered dose-dependent induction of the AhR-target gene *Ahrr*.
- sci-Plex: over 37 held-out drugs in A549, scVIDR beat scGen on DEG expression at the 3
  highest doses (100 / 1,000 / 10,000 nM).
- Pseudo-dose correlated with administered dose (**R² = 0.76**) and was higher in central
  vs portal hepatocytes, matching known TCDD liver-zonation biology.

## Why it matters for our work

scVIDR is a directly relevant baseline for perturbation-response prediction — the core of
the BioReasoning Challenge's up/down/none directional tasks (Track A/B). Its δ-arithmetic +
linear-regression recipe shows a **simple, interpretable model can beat heavier generative
autoencoders** for predicting cell-type-specific differential expression, echoing our own
finding that linear baselines are strong. The dose-interpolation and pseudo-dose ideas
offer a continuous framing of perturbation magnitude that could inform how we rank or
threshold predicted regulation direction, and the DEG-focused R² evaluation is a useful
reference protocol.

## Limitations / open questions

- Accuracy degrades for cell types that respond weakly to treatment (small control
  populations, low HVG expression) — the VAE underestimates DEGs there.
- Multi-dose prediction assumes a **log-linear** trajectory along δ; nonlinear or
  non-monotonic dose-response may break this.
- Standard VAE latent space is not natively interpretable; interpretability requires the
  bolted-on sparse-regression step, trading against reconstruction accuracy.
- Validation centers on a few well-characterized systems (TCDD liver, IFN-β, sci-Plex);
  generalization to novel chemicals/mechanisms with no analog in training is untested.
