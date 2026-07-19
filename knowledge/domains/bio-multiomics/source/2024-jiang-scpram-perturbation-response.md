---
source_url: https://doi.org/10.1093/bioinformatics/btae265
source_type: papers
title: "scPRAM accurately predicts single-cell gene expression perturbation response based on attention mechanism"
author: Qun Jiang et al.
retrieved: 2026-07-16
doi: 10.1093/bioinformatics/btae265
---

# scPRAM accurately predicts single-cell gene expression perturbation response based on attention mechanism

**Authors:** Qun Jiang, Shengquan Chen, Xiaoyang Chen, Rui Jiang
**Year:** 2024
**Venue:** Bioinformatics (Oxford)

## Abstract
scPRAM predicts single-cell gene-expression responses to external perturbations (drug treatment, bacterial/LPS infection, cytokine stimulation) for cell types not seen during training. Prior methods (scGen, scVIDR, trVAE, scPreGAN, CellOT) mostly model the *average* response of a cell type, ignoring single-cell heterogeneity and the full response distribution. scPRAM combines a variational autoencoder, optimal transport, and an attention mechanism to align pre- and post-perturbation cell states and transfer the perturbation direction to unseen cells at single-cell resolution. Across multiple real datasets it beats existing methods on cross-cell-type, cross-species, and cross-individual prediction, and is robust to noise and sample-size variation.

## Key contributions
- An attention-based perturbation-transfer scheme that predicts per-cell (not just per-cell-type-average) responses, capturing single-cell heterogeneity and the whole response distribution.
- Use of optimal transport to pair unpaired control/perturbed cells in VAE latent space (cells are destroyed by sequencing, so pre/post are not one-to-one), yielding a coupling matrix used to build the perturbation direction.
- A method that generalizes the learned perturbation direction to *unseen* cell types via attention over similarities to seen cells, avoiding the averaging bias of scGen and the small-sample linear-regression weakness of scVIDR.

## Methods
Control and perturbed cells are encoded into a shared VAE latent space. Because samples are unpaired, optimal transport computes a coupling matrix M between latent control (Z_ctr) and perturbed (Z_ptb) cells; each control cell is matched to its argmax-row perturbed counterpart to form an adjusted Z_ptb'. For a query (unseen) cell, an attention mechanism weights the perturbation vectors of matched training cells by latent-space similarity, producing a cell-specific latent shift that is decoded back to gene-expression space. Evaluation holds out one cell type / species / individual at a time and compares predicted vs. true responses using linear regression of gene-expression mean and variance, Wasserstein distance, and number of common differentially expressed genes (DEGs, Wilcoxon rank-sum in Scanpy).

## Key results
- On out-of-sample prediction, scPRAM matches competitors on expression *mean* regression but achieves a marked breakthrough on *variance* regression, reflecting better capture of single-cell heterogeneity (Fig. 2B); UMAP of predicted CD8T responses aligns closely with truth while other four methods show clear bias.
- Identifies substantially more common DEGs than five baselines — nearly 50+ on PBMC and Hpoly.Day10 — and predicts top-100-DEG mean/variance more accurately; top-100 scPRAM DEGs enriched for the interferon-signaling pathway, matching the IFN-β stimulus.
- Cross-species (macrophages from mouse/rat/rabbit/pig, 6 h LPS): baselines' variance R² fall below 0.4, while scPRAM raises variance R² above 0.6 and better captures species-specific marker-DEG heterogeneity.
- Robust to downsampling and to 10–50% dropout noise, consistently outperforming other methods as noise rises; also stable under class imbalance.

## Why it matters for our work
scPRAM is a directly relevant perturbation-response method for the BioReasoning Challenge's up/down/none prediction framing (Tracks A/B): it predicts direction and magnitude of gene-expression change under perturbation, with an explicit focus on DEG identification — the exact signal our classifier must recover. Its OT+attention transfer of a perturbation "direction" to unseen cell types/species/individuals is a candidate strategy for generalizing across the held-out conditions in the challenge, and its emphasis on modeling the response *distribution* (not just the mean) is a useful contrast to foundation-model-only Track C approaches.

## Limitations / open questions
- Requires observed perturbed cells for related cell types to learn a transferable direction; it does not predict responses to entirely novel perturbations (unlike GEARS-style perturbation-graph methods).
- Handles single, categorical perturbations per experiment; combinatorial perturbations and dose-response are not addressed here.
- Relies on a good shared VAE latent alignment and OT matching; performance under strong batch effects or very distant target domains is untested beyond the reported datasets.
