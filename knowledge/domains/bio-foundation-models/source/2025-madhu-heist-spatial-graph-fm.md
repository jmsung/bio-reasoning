---
source_url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12486056/
source_type: papers
title: "HEIST: A Graph Foundation Model for Spatial Transcriptomics and Proteomics Data"
author: Hiren Madhu et al.
retrieved: 2026-07-16
doi:
---

# HEIST: A Graph Foundation Model for Spatial Transcriptomics and Proteomics Data

**Authors:** Hiren Madhu, João Felipe Rocha, Tinglin Huang, Siddharth Viswanath, Smita Krishnaswamy, Rex Ying (Yale University)
**Year:** 2025
**Venue:** arXiv preprint (PMC12486056 / PMID 41040798)

## Abstract
HEIST is a hierarchical graph-transformer foundation model for spatial transcriptomics and proteomics. It models a tissue as a two-level hierarchical graph: a top-level spatial cell graph (cells connected by physical proximity) where each cell node is itself expanded into a lower-level gene co-expression network graph. Unlike prior single-cell FMs that either discard spatial context or use fixed gene vocabularies, HEIST computes gene embeddings dynamically from co-expression structure and cellular context, enabling generalization to unseen genes and to spatial proteomics without retraining. It is pretrained on 22.3M cells from 124 tissues across 15 organs using spatially-aware contrastive and masked-autoencoding objectives, and reaches state-of-the-art performance on clinical outcome prediction, cell-type annotation, and gene imputation.

## Key contributions
- Hierarchical tissue graph coupling a spatial cell graph with per-cell gene co-expression networks, unifying molecular and spatial information.
- Intra-level and cross-level message passing so cell context refines gene embeddings and vice versa.
- Vocabulary-free gene embeddings (rank-based + sinusoidal positional encodings, updated via co-expression message passing) that generalize to novel genes and to proteomics markers.
- Spatially-aware contrastive + masked-autoencoding pretraining on 22.3M cells (13.3M 10x Genomics, 8.7M Vizgen, 360K Seattle Alzheimer's Brain Atlas), mostly MERFISH/Xenium.

## Methods
Each cell is a node in a spatial proximity graph; within each cell, genes form a co-expression graph with an adaptive threshold τ. The model alternates intra-level message passing (within each graph) and cross-level message passing (integrating cell↔gene signals). Pretraining combines a contrastive objective over gene expression and cell locations with a masked-autoencoding loss that reconstructs masked gene expression and spatial coordinates (MSE), teaching robustness to dropout and noise. Downstream tasks use frozen embeddings with a lightweight MLP head (or fine-tuned decoder for imputation).

## Key results
- State-of-the-art across seven organs; 8× faster than scGPT(-spatial) and 48× faster than scFoundation on a 19,826-cell tissue.
- Clinical outcome prediction (AUC-ROC): best in 6/7 scenarios; on UPMC, surpasses scGPT-spatial by 25.4% and CellPLM by 30%.
- Cell-type annotation (F1): best in 4/5 datasets; +28.7% (UPMC) and +17.9% (DFCI) neck datasets.
- Gene imputation (Pearson, fine-tuned): beats all baselines by 2.5% (placenta) and 9% (skin).
- Linear probe for ligand-receptor interaction prediction: AUC-ROC 0.995 ± 0.002, best of all baselines.
- Ablations: hierarchical modeling and spatial information are the most critical components; MAE most important for imputation.

## Why it matters for our work
HEIST is a Track C foundation-model candidate that stakes out the spatial-omics niche the mainstream scFMs (scGPT, scFoundation, CellPLM) handle poorly. Its two ideas are directly transferable to our gene-regulation strategy: (1) vocabulary-free gene embeddings built from co-expression + context, which sidesteps the fixed-gene-vocabulary limitation that hampers cross-dataset transfer in Track A/B; and (2) explicit modeling of how microenvironment shapes intracellular regulation — relevant when reasoning about up/down/none expression shifts driven by context rather than the perturbed gene alone. The strong ligand-receptor probe result suggests the embeddings encode real regulatory signaling structure worth probing for our prediction tasks.

## Limitations / open questions
- Zero-shot gene imputation is weak; strong results require fine-tuning the decoder per dataset.
- Pretraining is spatial-omics-only (MERFISH/Xenium/CODEX/MIBI) — unclear transfer to non-spatial single-cell or bulk perturbation settings (our Track A/B data).
- One HEISTLayer is slower than CellPLM; the speed wins are relative to scGPT/scFoundation, not universally.
- No public weights/DOI confirmed in the retrieved text; reproducibility for our stack unverified.
