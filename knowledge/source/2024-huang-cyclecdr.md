---
source_url: https://doi.org/10.1093/bioinformatics/btae248
source_type: papers
title: "Predicting single-cell cellular responses to perturbations using cycle consistency learning"
author: Wei Huang et al.
retrieved: 2026-07-16
doi: 10.1093/bioinformatics/btae248
---

# Predicting single-cell cellular responses to perturbations using cycle consistency learning

**Authors:** Wei Huang, Hui Liu
**Year:** 2024
**Venue:** Bioinformatics (Oxford)

## Abstract
cycleCDR is a deep-learning framework that predicts how cells respond at the molecular level to external perturbations (drugs or genetic manipulations). An autoencoder maps unperturbed cellular states into a latent space where perturbation effects are assumed to be a **linear additive** shift. A **cycle-consistency** constraint (borrowed from cycleGAN, for unpaired data) requires that adding a perturbation vector to an unperturbed latent state decodes to the true perturbed state, and — conversely — subtracting it from a perturbed state restores the unperturbed state. This bidirectional constraint plus latent linearity yields transferable perturbation representations, so the model generalizes to drugs unseen at training time. The authors validate on four dataset types: bulk transcriptional, bulk proteomic, single-cell transcriptional drug responses, and single-cell genetic-perturbation responses, reporting consistent state-of-the-art performance.

## Key contributions
- Applies **cycle consistency** to unpaired single-cell perturbation data, sidestepping the fact that RNA-seq is destructive so the same cell cannot be profiled before and after perturbation (no paired samples).
- Combines cycle-consistency loss with a **linear-additive latent model** of perturbation effects, enabling drug "exposure" (add vector) and "withdrawal" (subtract vector) to be simulated bidirectionally and drug representations to transfer to **unseen drugs**.
- A **dual-autoencoder** architecture (separate encoders/decoders for unperturbed and perturbed states) that empirically beats a single shared autoencoder.

## Methods
Unperturbed state x_i is encoded to latent z_i; the effect of drug j is a learned vector d_j added in latent space, and a decoder G reconstructs the perturbed response. A second encoder maps the actual perturbed response y_ij to the same latent space, where subtracting d_j should recover x_i via a second decoder. Paired data (bulk) use an MSE loss on both forward and reverse directions plus a reconstruction loss; unpaired single-cell data rely on the cycle-consistency constraints. Drug perturbations are represented from molecular structure so unseen compounds can be encoded. Evaluation uses mean/median r² and explained variance (EV) over all genes and over differentially expressed genes (DEGs), against a naive baseline, chemCPA (drug response), and GEARS (genetic perturbation).

## Key results
- **Bulk L1000** (6424 drugs, 42 cell lines, 978 landmark genes; train n=73,222): highest mean r² and EV among all methods over both all genes and DEGs; per-drug boxplots show >0.75 mean r² across all genes and 0.4–0.6 across DEGs.
- **Single-cell drug response** (sci-Plex): outperforms chemCPA with and without L1000 pretraining, reaching ~0.5 or higher r² across MCF7, K562, and A549 cell lines; confirmed on the newer sci-Plex4 dataset.
- **Single-cell genetic perturbation**: beats the baseline and **GEARS** on mean r²/EV across all genes and DEGs, with the largest margin on highly variable genes; predicted vs. actual post-perturbation expression significantly correlated (P<0.01) for top DEGs.
- Ablation: dual autoencoders and the cycle-consistency + reconstruction losses each contribute measurable gains.

## Why it matters for our work
The BioReasoning Challenge (Tracks A/B) asks whether a perturbation drives a gene up, down, or unchanged. cycleCDR is a directly relevant baseline: it models the **directional latent shift** of a perturbation and, via linear additivity, produces a signed per-gene response that could be thresholded into up/down/none calls. Its cycle-consistency trick for unpaired control/perturbed cells addresses the same missing-paired-data problem our single-cell prediction faces, and its generalization to unseen drugs speaks to held-out-perturbation evaluation. It is a useful point of comparison alongside GEARS, chemCPA, CPA, and scPRAM already in our wiki.

## Limitations / open questions
- Linear-additive latent assumption may under-model nonlinear or combinatorial (drug×dose, gene×gene) effects.
- Reported metrics for competing methods were taken from their papers without confidence intervals, so head-to-head significance is uncertain.
- Cell lines with weak drug response were filtered out on L1000, which may inflate apparent accuracy; performance is best for drugs whose pharmacology resembles the training set.
- r²/EV are continuous-expression metrics — not a direct up/down/none classification score, so mapping to the Challenge's discrete labels is unvalidated here.
