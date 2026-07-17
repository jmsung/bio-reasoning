---
source_url: https://doi.org/10.1101/2024.11.16.623974
source_type: papers
title: "Squidiff: Predicting cellular development and responses to perturbations using a diffusion model"
author: Siyu He et al.
retrieved: 2026-07-16
doi: 10.1101/2024.11.16.623974
---

# Squidiff: Predicting cellular development and responses to perturbations using a diffusion model

**Authors:** Siyu He, Yuefei Zhu, Daniel Naveed Tavakol, Haotian Ye, Yeh-Hsing Lao, Zixian Zhu, Cong Xu, Sharadha Chauhan, Guy Garty, Raju Tomer, Gordana Vunjak-Novakovic, James Zou, Elham Azizi, Kam W. Leong
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
Squidiff is a diffusion-model-based generative framework that predicts single-cell transcriptomic changes across diverse cell types in response to environmental changes — cell differentiation, gene perturbation, and drug response. Through continuous denoising and semantic feature integration it learns transient cell states and predicts high-resolution transcriptomic landscapes over time and conditions. The authors apply it to iPSC differentiation, gene/drug perturbation benchmarks, blood vessel organoid (BVO) development, and cellular responses to neutron irradiation and a growth-factor drug (G-CSF), positioning it as an in-silico screening tool for precision medicine.

## Key contributions
- Adapts a **diffusion autoencoder** (conditional DDIM + semantic encoder) to single-cell gene expression: biology (cell type, stimulus, disease state) is captured in a semantic latent variable `z_sem`, while stochasticity lives in the diffusion noise variable `x_T`.
- Predicts perturbation responses by **vector arithmetic in semantic space** — a stimulus is a direction `Δz_sem`; two-gene perturbations are modeled as the sum of two learned `z_sem` vectors, requiring **no gene-gene graph prior** (unlike GEARS).
- Adds a **drug-compound adapter** (rFCFP fingerprints from PRNet) so the model can generalize to entirely unseen drugs, not just unseen cell types.
- Generates cell-type-specific responses from **single-timepoint** data, inferring dynamic trajectories without costly multi-timepoint sequencing.

## Methods
A forward Gaussian diffusion process progressively noises the gene-expression vector `x_0`; a denoiser network `ε_θ(x_t, t, z_sem)`, conditioned on the semantic latent variable, learns the deterministic DDIM reverse process to reconstruct `x_0`. The semantic encoder produces `z_sem` per condition; differences and sums of these vectors define stimulus directions and combined perturbations. For unseen drugs, the semantic variable is updated to `z_sem' = Enc(x_0, rFCFP)`, incorporating drug structural/functional properties. Predictions are validated with differential expression, pseudotime (Scorpius, PAGA, Monocle), and Pearson/R² correlation against held-out ground truth.

## Key results
- **Differentiation (iPSC → definitive endoderm):** trained only on day 0 and day 3, Squidiff accurately interpolates days 1–2; recovers known marker dynamics (NANOG down, GATA6 up, T enriched early). Outperforms scGen on both Pearson correlation and R² across days (t-test P as low as 1.97×10⁻³⁵).
- **Gene perturbation (K562, non-additive ZBTB25+PTPN12):** beats both GEARS and scGen on R² without any graph prior, with fewer genes predicted in the wrong direction.
- **Drug response:** on glioblastoma data, trained on limited cell/drug combinations, it predicts all six drugs' effects on tumor cells and oligodendrocytes and correctly flags panobinostat as the most potent on tumor cells. With the rFCFP adapter, it matches or beats PRNet on sci-plex3 unseen-compound and random splits.
- **BVO development + neutron irradiation:** reconstructs endothelial/mural/fibroblast trajectories, captures transient states scGen misses, and (trained on endothelial cells only) predicts irradiation and G-CSF responses in held-out cell types; recovers a p53/DNA-damage signature (CDKN1A, MDM2, GDF15 up).

## Why it matters for our work
Squidiff is a strong data point for the BioReasoning perturbation-prediction task (Track A/B up/down/none): it predicts the direction and magnitude of expression change under gene and drug perturbations, and its semantic-vector arithmetic is a concrete graph-free alternative to GEARS/CODEX-style priors for generalizing to unseen combinations. The single-timepoint-to-trajectory inference and the rFCFP unseen-drug adapter are reusable ideas for building generalizable perturbation predictors, and its diffusion framing complements the VAE (scGen, CPA) and counterfactual (CODEX) approaches already in our wiki.

## Limitations / open questions
- Diffusion training injects Gaussian noise and is compute-heavy — longer training and more resources than VAEs/GANs; authors flag scaling as future work.
- The **linearity assumption** on semantic variables gives only approximate predictions in highly complex scenarios.
- Unseen-drug prediction is limited without the fingerprint adapter; combination effects assume implicit additive/synergistic latent capture.
- Drug-combination validation used the 4i dataset (~50 morphological features, not transcriptomics), and all results are single-timepoint in-vitro organoids — no in-vivo validation yet.
