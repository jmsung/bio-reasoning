---
source_url: https://doi.org/10.15252/msb.202211517
source_type: papers
title: "Predicting cellular responses to complex perturbations in high-throughput screens"
author: Mohammad Lotfollahi et al.
retrieved: 2026-07-16
doi: 10.15252/msb.202211517
---

# Predicting cellular responses to complex perturbations in high-throughput screens

**Authors:** Mohammad Lotfollahi, Anna Klimovskaia Susmelj, Carlo De Donno, Leon Hetzel, Yuge Ji, Ignacio L Ibarra, Sanjay R Srivatsan, Mohsen Naghipourfar, Riza M Daza, Beth Martin, Jay Shendure, Jose L McFaline-Figueroa, Pierre Boyeau, F Alexander Wolf, Nafissa Yakubova, Stephan Günnemann, Cole Trapnell, David Lopez-Paz, Fabian J Theis
**Year:** 2023
**Venue:** Molecular Systems Biology

## Abstract
High-throughput single-cell screens measure transcriptional responses to thousands of drug and genetic perturbations, but the combinatorial space is too large to sample exhaustively. This paper introduces the **compositional perturbation autoencoder (CPA)**, which combines the interpretability of linear models with the flexibility of deep learning to predict single-cell perturbation responses in silico. CPA generalizes to unseen dosages, cell types, time points, and species, predicts unseen drug combinations while outperforming baselines, and — via a chemistry-aware extension (chemCPA) — predicts responses to completely unseen drugs. Applied to a genetic Perturb-seq screen, CPA imputes 5,329 missing gene-pair combinations (97.6% of all possibilities).

## Key contributions
- CPA: an autoencoder that disentangles gene expression into a perturbation-free "basal state" plus additively composable perturbation and covariate embeddings, enabling counterfactual "what if treated differently" prediction.
- Adversarial discriminators strip perturbation/covariate signal from the latent basal state; learned embedding dictionaries give interpretable dose-response curves and perturbation similarity maps.
- chemCPA extension replaces the perturbation dictionary with a molecule encoder (RDKit fingerprints) → generalizes to compounds never seen in training.
- A new drug-combination dataset (combosciplex, n=63,378 cells, 32 perturbations/combos in A549) for validation.

## Methods
CPA encodes each cell's expression into a low-dimensional latent space, uses discriminators to remove perturbation and covariate signal (the basal state), then re-composes basal + perturbation + covariate embeddings with nonlinear dose/time scalers before decoding back to expression. All weights and embedding dictionaries are learned jointly via backpropagation on reconstruction + discriminator losses. At evaluation, swapping a perturbation embedding produces counterfactual predictions for unseen conditions. Distance from an unseen embedding to the nearest observed embedding serves as an uncertainty proxy. Performance is scored via R2 (scikit-learn) between predicted and real means/variances, over all genes and over the top ~50 differentially expressed genes (DEGs), against a random-subset baseline and a linear model.

## Key results
- On sci-Plex3 (188 drugs, 290,889 cells across A549/K562/MCF7), CPA extrapolates to held-out highest doses; vs. scGen it improved variance prediction by 35.85% and mean prediction by 1.54%, capturing whole-distribution shifts scGen misses.
- Predicted a fully held-out Panobinostat + Alvespimycin combination with R2 = 0.81; beat random and linear baselines on highly variable genes and top-50 DEGs.
- chemCPA outperformed CPA on unseen-drug and combination settings; DEG R2 dropped from 0.85 to 0.38 when the single-drug Panobinostat observation was also withheld, showing single-drug data is crucial for combinations.
- On genetic Perturb-seq (281 single/double perturbations, 108,497 cells), CPA imputed all 5,329 missing gene-pair combinations; accuracy improved with more combinations seen (failed on DEGs when <71 combinations trained). Notably, a simple baseline matched CPA/linear on mean prediction here, indicating limited whole-transcriptome nonlinearity in that dataset.

## Why it matters for our work
CPA is a foundational perturbation-prediction method directly relevant to the BioReasoning Challenge's up/down/none directional prediction (Tracks A/B): its counterfactual, additive-embedding framing is exactly the "predict how a cell's expression shifts under a perturbation" task we face. The uncertainty proxy (distance to nearest observed embedding) is a reusable signal for calibrating abstention — relevant given our Track B over-abstention failure. Critically, the Perturb-seq finding that a random/linear baseline matched CPA on mean prediction reinforces our own lesson (linear baselines are strong; don't trust small CV) and warns that whole-transcriptome mean metrics can hide the real challenge, which lies in variance and DEG-level distribution shifts.

## Limitations / open questions
- Additive composition of perturbation embeddings struggles with strong distribution shifts / synergy (Alvespimycin combos capped at ~0.3 R2 on DEGs for both CPA and chemCPA).
- Predictions degrade with scarce samples (n<100 cells) or when only single-perturbation data exists for a combination.
- On some genetic screens a linear/random baseline is competitive, so gains are dataset-dependent and mean-R2 can overstate model value.
- In silico imputed combinations distant from measured data (e.g. KLF1 pairs) flag potential novelty but require experimental validation.
