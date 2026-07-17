---
source_url: https://doi.org/10.1101/2025.06.05.657988
source_type: papers
title: "Learning Genetic Perturbation Effects with Variational Causal Inference"
author: Emily Liu et al.
retrieved: 2026-07-16
doi: 10.1101/2025.06.05.657988
---

# Learning Genetic Perturbation Effects with Variational Causal Inference

**Authors:** Emily Liu, Jiaqi Zhang, Caroline Uhler
**Year:** 2025
**Venue:** bioRxiv (preprint; MIT EECS / LIDS + Broad Institute Schmidt Center)

## Abstract
Perturb-seq profiles transcriptomic responses to CRISPR gene perturbations at single-cell resolution. Deep-learning models interpolate observed perturbations well but overfit and generalize poorly to unseen perturbations, whereas mechanistic linear causal models extrapolate better but are too simplistic for noisy, large-scale data. The authors propose SCCVAE (Single Cell Causal Variational Autoencoder), a hybrid that embeds a learned mechanistic causal model — perturbations as additive shift interventions propagating through a learned regulatory network — inside a variational autoencoder. SCCVAE outperforms state-of-the-art baselines when extrapolating to unseen single-gene perturbations, and its latent space recovers functional perturbation modules and supports simulation of knockdowns at varying penetrance.

## Key contributions
- A hybrid causal-VAE that combines mechanistic extrapolation with deep-learning expressivity for single-cell perturbation prediction.
- Perturbations modeled as additive **shift interventions** on n=512 latent gene modules organized by a learned DAG (upper-triangular mask), decoded to full transcriptomes.
- A **shift-selection** procedure (scalar penetrance c per perturbation, grid-searched against pseudo-bulk MSE) that lets the model predict unseen perturbations of unknown guide efficiency.
- Latent U^p embeddings that cluster genes into interpretable functional modules (mediator complex, ribosomal proteins, cell-cycle, proteasome, DNA repair) even for held-out genes.

## Methods
SCCVAE has four parts: an expression encoder (control cell X → exogenous noise Z ∈ R^512), a shift encoder (perturbation label → shift vector S^p, using top-50 PCA components of the control expression matrix as the perturbation label so unseen genes are representable), a structural causal model (linear Gaussian SCM, U^p = (I−A)^−1(Z + S^p) with learned adjacency A), and an expression decoder. Trained with a variational lower bound plus a maximum-mean-discrepancy (MMD) term to match perturbed distributions. Evaluated on Replogle genome-scale Perturb-seq essential-gene data — K562 (m=8563 genes; 279 high-signal perturbations after cell-count and logistic-regression filtering) and RPE1 (m=8749) — under in-distribution splits and out-of-distribution (OOD) splits where test perturbations never appear in training (5 splits, averaged).

## Key results
- OOD: SCCVAE beats GEARS and control baselines, with the largest gains on **distributional metrics (MMD, energy distance)** over all essential genes; GEARS tends to collapse toward the control distribution while SCCVAE matches the true perturbed distribution.
- In-distribution K562: SCCVAE MSE 0.0114 vs GEARS 0.0118 vs control 0.0131 (all-genes); PearsonR ~0.982 across models (bulk-mean metrics near-saturated for all methods).
- Full unfiltered K562: SCCVAE MSE 0.00657 vs GEARS 0.00731 vs control 0.0077.
- scGPT (transformer) gets better Pearson/direction metrics but higher-than-control MMD/energy distance — it captures coarse patterns yet overfits distributional detail.
- Ablations: learned DAG and a GSP-inferred DAG both beat a conditional (non-causal) VAE and a random-graph model, confirming the mechanistic component drives OOD gains; shift selection cannot rescue a mis-specified (random) graph.
- Penetrance is tunable: sweeping c ∈ [−1,3] for gene MED7 minimizes error near c ≈ 2.0.

## Why it matters for our work
The BioReasoning Challenge's core Track A/B task is predicting perturbation direction (up/down/none) for **unseen** genes — exactly the OOD extrapolation regime this paper targets. SCCVAE reinforces two lessons already in our wiki: (1) bulk-mean metrics (MSE, Pearson) saturate and barely separate methods, so distributional/direction metrics carry the real signal — relevant to how we score and trust CV; (2) mechanistic/causal structure (a learned GRN with shift interventions) extrapolates to novel perturbations where GO-prior deep models like GEARS collapse to control. This is a candidate strategy for injecting gene-regulatory inductive bias into our up/down/none predictor rather than relying on foundation-model embeddings alone.

## Limitations / open questions
- Only single-gene knockdowns on two cell lines; combinatorial and cross-cell-type perturbations untested.
- OOD prediction **requires** a per-perturbation penetrance scalar c, selected against pseudo-bulk data — so it needs auxiliary bulk/pseudo-bulk info per novel perturbation, not a pure zero-shot label.
- On bulk-mean metrics SCCVAE is only on par with a simple linear model (Ahlmann-Eltze) — its edge is specifically distributional/single-cell fidelity.
- Gaussian output likelihood; raw counts (ZINB) and non-linear SCMs left as future work.
- Preprint, not peer-reviewed.
