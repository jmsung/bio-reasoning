---
source_url: https://doi.org/10.1038/s41467-025-63478-z
source_type: papers
title: "Prediction of cellular morphology changes under perturbations with a transcriptome-guided diffusion model"
author: Wang et al. (BioMap Research / CUHK)
retrieved: 2026-07-16
doi: 10.1038/s41467-025-63478-z
---

# Prediction of cellular morphology changes under perturbations with a transcriptome-guided diffusion model

**Authors:** Xuesong Wang, Yimin Fan, Yucheng Guo, Chenghao Fu, Kinhei Lee, Khachatur Dallakyan, Yaxuan Li, Qijin Yin, Yu Li, Le Song
**Year:** 2025
**Venue:** Nature Communications

## Abstract
MorphDiff is a transcriptome-guided latent diffusion model that simulates
high-fidelity cell *morphology* images (5-channel Cell Painting) in response to
genetic and chemical perturbations, conditioned on the perturbed L1000 gene
expression profile. Predicting cell-image responses across the vast perturbation
space is infeasible experimentally, so an in-silico simulator can accelerate
phenotypic drug discovery — mechanism-of-action (MOA) prediction, compound
bioactivity, and repurposing. Benchmarked on three large datasets covering
thousands of perturbations, MorphDiff accurately predicts morphological changes
for *unseen* perturbations and, critically, its generated morphologies drive MOA
retrieval at accuracy comparable to ground-truth images while outperforming
baselines by 16.9% and 8.0%.

## Key contributions
- First transcriptome-conditioned diffusion model that generates full multi-channel
  cell-morphology *images* (not just tabular features) for unseen perturbations.
- Two inference modes: G2I (gene-expression → image, de novo) and I2I
  (control image + gene expression → perturbed image).
- Demonstrates that transcriptome (L1000) is a strong conditioning signal for
  morphology, exploiting shared information between the two modalities.
- An MOA-retrieval pipeline showing computationally-inferred morphology carries
  MOA signal complementary to drug structure and transcriptomics.

## Methods
Architecture couples a Morphology VAE (MVAE) that compresses 5-channel Cell
Painting images (DNA, ER, RNA, AGP, Mito) into a latent space, with a Latent
Diffusion Model that denoises those latents conditioned on the perturbed L1000
gene-expression vector. Trained/evaluated on three datasets: 1028 drug
perturbations (CDRP), 130 genetic perturbations (JUMP, U2OS), and 61 drug
perturbations (LINCS, A549), split into training, in-distribution (ID), and
out-of-distribution (OOD) sets. Evaluation combines image-generation metrics
(FID, Inception Score, CMMD, density, coverage) with biological-relevance metrics
using interpretable CellProfiler and DeepProfiler features. Baselines: MorphNet,
IMPA, DMIT, DRIT++, StarGANv1, VQGAN, MDTv2 (most conditioned on Gene2vec/RDKit
embeddings, following IMPA).

## Key results
- On JUMP OOD (genetic) and CDRP OOD (drug), both MorphDiff modes substantially
  outperform baselines on most image-generation metrics (FID, CMMD in particular).
- Generated CellProfiler-feature vectors align with ground truth (high R2 on
  significantly-changed features); MorphDiff(G2I) beats IMPA on per-feature recovery.
- DeepProfiler-embedding SVM pairwise classification: MorphDiff(G2I) achieves the
  highest perturbation-discrimination accuracy among tested methods.
- MOA retrieval on the CDRP Target_MOA set (69 drugs, 10 targets, 35 MOAs):
  MorphDiff-generated morphology reaches accuracy comparable to ground-truth
  morphology and outperforms baselines by 16.9% and 8.0% (per abstract);
  MorphDiff consistently beats baselines on fold-of-enrichment and mAP matching.

## Why it matters for our work
MorphDiff is a concrete data point that perturbed transcriptome carries enough
signal to reconstruct a *different* cellular readout (morphology) for unseen
perturbations — the same generalization-to-unseen-perturbations problem behind
Tracks A/B (predicting up/down/none expression responses). Its two-mode design
(de novo vs. control-anchored, I2I) mirrors our baseline-vs-delta framing, and
its finding that structurally dissimilar drugs share MOA-relevant phenotypes
reinforces why perturbation *effect* (expression/phenotype) beats structural
similarity as a conditioning signal — relevant to how we encode perturbations for
prediction rather than relying on chemical/gene-embedding nearest-neighbors.

## Limitations / open questions
- Requires a measured perturbed L1000 profile as input, so it cannot be applied
  to perturbations with no transcriptomic measurement — limiting true zero-shot use.
- Morphology data is noisy (batch, well-position effects); modality gap between
  transcriptome and image means shared information is only partial.
- Evaluation is on a handful of cell lines (U2OS, A549) and curated MOA subsets;
  generalization across cell types and to prospective wet-lab validation is untested.
