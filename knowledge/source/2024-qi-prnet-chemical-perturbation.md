---
source_url: https://doi.org/10.1038/s41467-024-53457-1
source_type: papers
title: "Predicting transcriptional responses to novel chemical perturbations using deep generative model for drug discovery"
author: Xiaoning Qi et al.
retrieved: 2026-07-16
doi: 10.1038/s41467-024-53457-1
---

# Predicting transcriptional responses to novel chemical perturbations using deep generative model for drug discovery

**Authors:** Xiaoning Qi, Lianhe Zhao, Chenyu Tian, Yueyue Li, Zhen-Lin Chen, Peipei Huo, Runsheng Chen, Xiaodong Liu, Baoping Wan, Shengyong Yang, Yi Zhao
**Year:** 2024
**Venue:** Nature Communications

## Abstract
PRnet is a perturbation-conditioned deep generative model that predicts bulk and single-cell transcriptional responses to chemical perturbations the model has never seen experimentally. It generalizes across novel compounds, pathways, and cell lines, enables gene-level interpretation and in-silico drug screening from disease gene signatures, and was used to build a large virtual atlas of perturbation profiles spanning 88 cell lines and 52 tissues. The authors experimentally validate novel compound candidates against small cell lung cancer and colorectal cancer, and recommend drug candidates for 233 diseases.

## Key contributions
- A scalable encoder-decoder generative model (PRnet) that predicts post-perturbation transcriptomes conditioned on compound structure (SMILES) and dose, generalizing to *unseen* chemicals — not just unseen cell types.
- Three-module design: Perturb-adapter (encodes any compound via SMILES/RDKit), Perturb-encoder, Perturb-decoder (VAE-style), making novel-compound screening tractable.
- An end-to-end reverse-signature drug-recommendation workflow producing a large-scale virtual perturbation atlas plus experimentally validated hits.

## Methods
PRnet formulates transcriptional-response prediction as a distribution-generation problem conditioned on a perturbation P = (structure s, dose d, cell context c). Compounds are converted to fixed-size embeddings through the Perturb-adapter using SMILES + RDKit Morgan fingerprints, so any unseen molecule can be encoded. A VAE-inspired Perturb-encoder/decoder estimates a per-gene Gaussian (mean, variance) and is trained by minimizing a Gaussian negative log-likelihood loss. Training used a bulk L1000 HTS library (>883k profiles, 175,549 compounds; 978 landmark genes, later expanded to 12,328 via L1000 linear transformation) and the sci-Plex3 single-cell assay (290,888 profiles, 188 compounds, A549/K562/MCF7 at four doses). Data were split strictly by perturbation attribute (random / compound / cell_line / pathway splits, 6:2:2, 5-fold CV) to simulate novel perturbations and prevent leakage. Screening ranks compounds by their ability to reverse disease up/down gene signatures using a Kolmogorov-Smirnov enrichment score (CMap-style connectivity).

## Key results
- Outperformed baselines (including CPA-family and linear models) across all three OOD splits on "Pearson of log(FC)" and "R2" metrics; strongest on unseen-compound prediction with an average PCC ≈ 0.8.
- On unseen cell lines, PCC improved by over 0.3 vs. alternatives; R2 in the compound reached ~0.97.
- Experimentally validated hits via MTT assays: SEL120-34A HCl and (+)-Fangchinoline against SCLC; 7-Methoxyrosmanol and Mulberrofuran Q against CRC.
- Generated a virtual atlas over 88 cell lines / 52 tissues and recommended candidate drugs for 233 diseases (NASH, IBD, PCOS cases literature-validated).

## Why it matters for our work
PRnet is a directional up/down/none-relevant reference for the BioReasoning Challenge Track A/B perturbation-response prediction: it predicts per-gene log fold-change and evaluates on "Pearson of log(FC)" and R2 under strict attribute-held-out splits — exactly the OOD generalization our challenge demands. Its SMILES-conditioned adapter is a concrete recipe for encoding *novel* perturbations (vs. genetic-only models like GEARS), and its VAE per-gene distribution head plus CMap-style reverse-signature scoring offer a baseline architecture and a directional-signature evaluation frame we can borrow or beat.

## Limitations / open questions
- SMILES/Morgan fingerprints may not fully capture 3D structure or stereochemistry; richer molecular encoders could help.
- Restricted to L1000 landmark genes at training (978 → linearly expanded), inheriting L1000 biases.
- The reverse-signature (CMap) paradigm does not hold for all diseases — transcriptional reversal ≠ drug sensitivity in some cases.
- Screening focuses on gene-level effects, ignoring phenotypic readouts (IC50, AUC) from dose-response curves.
