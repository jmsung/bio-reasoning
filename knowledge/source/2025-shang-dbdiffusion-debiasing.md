---
source_url: https://doi.org/10.1101/2025.09.12.675662
source_type: papers
title: "Predicting the unseen: a diffusion-based debiasing framework for transcriptional response prediction at single-cell resolution"
author: Ergan Shang et al.
retrieved: 2026-07-16
doi: 10.1101/2025.09.12.675662
---

# Predicting the unseen: a diffusion-based debiasing framework for transcriptional response prediction at single-cell resolution

**Authors:** Ergan Shang, Yuting Wei, Kathryn Roeder (Carnegie Mellon University; The Wharton School, University of Pennsylvania)
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
dbDiffusion (debiased diffusion) is a generative framework for predicting single-cell transcriptional responses to *unseen* genetic perturbations from related Perturb-seq data. It couples a latent diffusion model (operating in VAE latent space) with classifier-free guidance conditioned on perturbation embeddings, and adds a debiasing step that corrects the systematic bias of generative predictions. Deliberately avoiding LLM/foundation-model embeddings — which the authors find yield unsatisfactory results — it derives embeddings for unmeasured perturbations from data-driven clustering of effect sizes and gene-expression correlations. Benchmarked on Perturb-seq datasets, dbDiffusion matches or beats state-of-the-art methods, and its integration of prediction-powered inference yields statistically rigorous confidence intervals and differential-expression calls.

## Key contributions
- A latent diffusion + classifier-free guidance generative model that estimates the *mean* effect (per gene) of an unseen perturbation, plus an uncertainty quantification via confidence intervals — not just realistic per-cell samples.
- A data-driven embedding for unmeasured perturbations built from two signals: per-gene effect-size clustering and the gene-expression correlation matrix (Leiden clustering on a smoothed, eigenvector-reduced correlation), explicitly avoiding LLM/GO/foundation-model embeddings.
- A debiasing step based on the conjecture that estimation bias is shared across perturbations within a cluster: subtract the observed bias of other perturbations in the assigned cluster from the predicted mean.
- Integration of prediction-powered inference (PPI) to correct generative bias and enable valid statistical downstream tasks (DE gene identification).

## Methods
Gene expression is modeled in VAE latent space where a diffusion model, guided by the perturbation embedding via classifier-free guidance, denoises Gaussian noise into predicted expression. For an unseen perturbation, the model finds its effect-size cluster by examining the gene-expression correlation matrix, then debiases the predicted mean using the average realized bias of that cluster's members. Evaluation used Pearson correlation coefficient (PCC) between predicted and observed mean expression change, and the overlap of confidence intervals with truth, on the Yao (2024) and Replogle (2022) Perturb-seq datasets, against GEARS, scLAMBDA, scGPT, and a one-hot cfDiffusion baseline.

## Key results
- On Yao's dataset (14 largest-effect perturbations), dbDiffusion outperformed the other three methods, reaching an average PCC of ~0.5, considerably higher than the next competitor.
- On Replogle's dataset (20 largest-effect perturbations), it was slightly below scLAMBDA but much better than GEARS and scGPT; matched cfDiffusion on Yao but was much better on Replogle, showing the informative embedding beats one-hot encoding even for trained perturbations.
- dbDiffusion had the highest confidence-interval overlap with truth (scLAMBDA second); GEARS cannot support interval estimation.
- Applying the cluster-based debiasing to cfDiffusion, scLAMBDA, and scGPT improved each considerably — the debiasing idea transfers across methods.
- Success is governed by clustering alignment: when predicting achieved PCC, distance-to-optimal-cluster correlated strongly negatively (r = -0.69); when predicting that distance, the Rand-Index-like gene-clustering measure RI correlated r = -0.44. Weaker Yao effect sizes explain lower overall performance there.

## Why it matters for our work
Directly on-topic for the BioReasoning perturbation-prediction tracks (Track A/B up/down/none direction prediction). Its headline claim — that simple, data-driven embeddings from effect-size and expression-correlation clustering beat LLM/foundation-model embeddings (scGPT, scLAMBDA) for unseen perturbations — is a caution for our Track C foundation-model choice and gene-embedding-direction work, reinforcing the linear-baseline skepticism already in our wiki (Ahlmann-Eltze, Csendes). The debiasing step (shared within-cluster bias) and confidence-interval / PPI machinery are reusable patterns for producing statistically calibrated direction calls rather than point predictions.

## Limitations / open questions
- Preprint (not peer-reviewed); benchmarked on only two Perturb-seq datasets (Yao, Replogle), single-gene perturbations, small test sets (14 and 20 top-effect perturbations).
- Performance collapses when effect-size clusters and gene-expression clusters misalign (low RI) — poor clustering yields a poor embedding and poor prediction.
- Debiasing gains for competing methods relied on dbDiffusion's own clustering, so they are not clean head-to-head comparisons.
- Authors note AI/LLM embeddings occasionally add complementary value when biological clustering is weak, suggesting hybrid/adaptive embedding strategies are unexplored future work.
