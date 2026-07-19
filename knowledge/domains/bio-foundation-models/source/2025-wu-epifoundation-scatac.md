---
source_url: https://doi.org/10.1101/2025.02.05.636688
source_type: papers
title: "EpiFoundation: A Foundation Model for Single-Cell ATAC-seq via Peak-to-Gene Alignment"
author: Juncheng Wu et al.
retrieved: 2026-07-16
doi: 10.1101/2025.02.05.636688
---

# EpiFoundation: A Foundation Model for Single-Cell ATAC-seq via Peak-to-Gene Alignment

**Authors:** Juncheng Wu, Changxin Wan, Zhicheng Ji, Yuyin Zhou, Wenpin Hou
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
EpiFoundation is a foundation model for single-cell ATAC-seq (scATAC-seq), the epigenetic modality that measures chromatin accessibility per cell. Existing single-cell foundation models target scRNA-seq and cannot transfer to scATAC-seq, whose peak space is huge (10^5–10^6 accessible regions) and extremely sparse (only two DNA copies per chromosome). EpiFoundation sidesteps intractable peak-to-peak correlation modeling with a cross-modality pre-training procedure: it processes only the non-zero peak set of each cell and uses paired dense gene expression as a supervisory signal, aligning peak-to-gene correlations. It supports cell-type annotation, batch correction, and gene expression prediction, and reports state-of-the-art results across multiple tissues.

## Key contributions
- A foundation model purpose-built for sparse, high-dimensional scATAC-seq — a modality prior single-cell FMs (Geneformer, scGPT, scBERT, scFoundation) did not cover.
- Two design innovations: (1) encode only the non-zero peak set to densify cell-specific signal and cut compute; (2) supervise pre-training with paired gene expression via peak-to-gene alignment rather than peak-to-peak masking.
- MiniAtlas: a curated 10X Multiome dataset of 100,000+ cells with paired scRNA-seq + scATAC-seq spanning 19 tissues and 56 cell types, plus diverse held-out test sets.

## Methods
Input is a binarized peak-cell accessibility matrix A ∈ {0,1}. For each cell only the non-zero peaks, embedded together with their chromosome identity, are fed to transformer blocks to produce a cell representation z_c. The pre-training objective predicts the paired binary gene expression B_binary (gene expressed vs not) of the same cell — the peak-to-gene alignment. Data was built from GEO/ENCODE 10X Multiome FASTQs processed with Cell Ranger ARC (GRCh38), peaks called with MACS2, matrices from Signac, multimodal clustering with Seurat, and cell-type labels assigned via Spearman correlation to DISCO reference profiles. For downstream tasks the frozen z_c feeds task-specific decoders fine-tuned for cell-type labels or fine-grained per-gene expression; z_c also serves directly as an unbiased embedding for batch correction.

## Key results
- Cell-type annotation: fine-tuned EpiFoundation gives favorable Accuracy, Macro/Micro F1, and ROC-AUC across four tissue datasets, distinguishing even cell types with similar transcription profiles.
- Batch correction: EpiFoundation embeddings beat scANVI, Harmony, LIGER, and peak-PCA on most datasets/metrics (scIB bio-conservation + batch metrics: ISO, NMI, cASW, cLISI, GC, bASW), achieving the highest NMI to ground-truth cell types and best graph connectivity.
- Gene expression prediction: fine-tuned on PBMC, BMMC, Kidney, and multi-tissue (ALLTissue), EpiFoundation significantly outperforms the Gene Activity baseline (Signac) across MSE, Spearman (SRCC), and Pearson (PRCC) on all datasets — indicating better peak-to-gene alignment.
- Ablations (kidney): removing batch-label conditioning or chromosome information each degrades NMI/bASW, confirming both strategies aid representation quality.

## Why it matters for our work
Track C foundation-model selection is RNA-centric, but EpiFoundation shows a credible route to bring the epigenetic (chromatin-accessibility) modality into a single-cell FM by aligning peaks to genes. The peak-to-gene alignment objective — predicting whether a gene is expressed from accessible regulatory regions — is directly a gene-regulation prior and is conceptually close to the up/down/none expression-direction prediction of Tracks A/B. The non-zero-set encoding trick (drop zeros, densify signal) is a reusable efficiency pattern for any sparse single-cell input, and MiniAtlas is a candidate paired multiome resource if we ever fuse ATAC with RNA features.

## Limitations / open questions
- Preprint (bioRxiv); no peer review, and reported gains reference tables/figures rather than headline effect sizes in prose.
- Human-only (GRCh38), 19 tissues / 56 cell types — generalization to other species or rarer cell types is untested.
- Cell-type labels are computationally assigned via DISCO correlation, so annotation ground truth is itself model-derived.
- Pre-training requires paired scRNA+scATAC (10X Multiome); applicability to ATAC-only data without paired RNA supervision is unclear.
- Future work targets a unified multi-modal FM (RNA + ATAC + sequence) — not yet realized here.
