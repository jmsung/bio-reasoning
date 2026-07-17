---
source_url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12383350/
source_type: papers
title: "scOTM: A Deep Learning Framework for Predicting Single-Cell Perturbation Responses with Large Language Models"
author: Yuchen Wang et al.
retrieved: 2026-07-16
doi: 10.3390/bioengineering12080884
---

# scOTM: A Deep Learning Framework for Predicting Single-Cell Perturbation Responses with Large Language Models

**Authors:** Yuchen Wang, Tianchi Lu, Xingjian Chen, Zhongyu Yao, Ka-Chun Wong
**Year:** 2025
**Venue:** Bioengineering (MDPI)

## Abstract
scOTM predicts single-cell perturbation responses from *unpaired* control/perturbed data, targeting generalization to unseen cell types. It injects prior biological knowledge — perturbation and cell-state embeddings from domain LLMs (scGPT for single-cell profiles, ChemBERTa/ESM2 for perturbations) — into a variational autoencoder regularized by maximum mean discrepancy (MMD) instead of the usual KL-to-standard-normal constraint, which the authors argue yields more expressive, biologically informative latents. Optimal transport then maps control to perturbed distributions in latent space. scOTM outperforms prior methods on whole-transcriptome response prediction and top-DEG recovery, and is robust in data-limited settings.

## Key contributions
- Replaces the VAE's KL-to-N(0,I) constraint with an **MMD-VAE** (kernel-based, non-parametric) for more flexible latent modeling.
- Uses **optimal transport (Earth Mover's Distance)** to learn a soft coupling between control and stimulated cells, giving an interpretable control→perturbed mapping.
- Integrates **LLM-derived embeddings** of both cell state (scGPT) and perturbation (ChemBERTa/ESM2), element-wise added to the gene-expression input.
- Handles **unpaired data** and generalizes to **held-out (unseen) cell types**.

## Methods
Datasets: Kang et al. human PBMC (IFN-β stimulation, 6998 HVGs after scGen-style preprocessing) and the Kaggle Open Problems single-cell perturbation dataset (belinostat vs. DMSO; 8562 control / 8101 perturbed cells). Evaluation holds out all stimulated cells of one cell type as the test set; the model predicts their stimulated profiles from control cells. The MMD-VAE encodes `D + D_embed + P_embed` into latent `z`; loss = reconstruction (L2) + α·MMD(z, N(0,I)) with an RBF kernel. In latent space, an OT plan γ (uniform marginals, squared-Euclidean cost) defines per-cell perturbation deltas; for a test control cell, the predicted shift is a cosine-similarity-weighted aggregate of training deltas, added to the cell's latent and decoded back to gene space.

## Key results
- Gene-mean regression R² = 0.976 on the representative CD4T held-out experiment; predicted ISG15/ISG20 distributions match stimulated.
- Best of all methods on **7/7** PBMC out-of-sample cell types, average mean-expression R² = **94.05%** (range 86.8% for FCGR3A+ Mono to 97.4%), beating scPRAM, scGen, scVIDR, trVAE, CellOT.
- DEG recovery: e.g. recovers 74/100 (dendritic) and 83/100 (CD14+ monocytes) top DEGs, higher than all baselines; Reactome enrichment recovers interferon/antiviral pathways consistent with IFN-β.
- Ablations: MMD vs. KL raised mean R² 0.9145→0.9416, variance R² 0.7502→0.7682, common top-100 DEGs 60.43→64.71; adding LLM embeddings further improved mean/variance R² and DEG overlap, most on heterogeneous cell types.
- Robust down to 10% training data (mean R² often ≥0.85); ~8–12 min/experiment on a single RTX 3080.

## Why it matters for our work
scOTM is directly relevant to perturbation-response prediction (the up/down/none direction task in Tracks A/B): its OT-plus-similarity delta mechanism produces per-gene expression shifts whose sign and magnitude map onto up/down/none calls, and its DEG-recovery focus mirrors our need to rank the most-changed genes. It is also a concrete case of using foundation-model embeddings (scGPT, ESM2, ChemBERTa — Track C candidates) as *frozen priors injected into a lightweight downstream model* rather than fine-tuning them, a cheap integration pattern worth considering. The MMD-over-KL choice and the unpaired/unseen-cell-type evaluation protocol are useful reference points for our own CV design.

## Limitations / open questions
- Evaluated only on PBMC (IFN-β) and a single-drug (belinostat) slice; breadth across many perturbations/compounds is untested.
- Gene-level *mean/variance* regression on unpaired data — no single-cell-resolved paired accuracy; high R² on means can mask cell-level error.
- Some baselines were not reproducible and were cited from the scPRAM paper rather than re-run, weakening head-to-head fairness.
- FCGR3A+ Mono showed non-monotonic performance with more data (condition imbalance), and LLM-embedding gains required extra training epochs.
