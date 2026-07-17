---
source_url: https://doi.org/10.1186/s12859-025-06071-x
source_type: papers
title: "HGATLink: single-cell gene regulatory network inference via the fusion of heterogeneous graph attention networks and transformer"
author: Yao Sun et al.
retrieved: 2026-07-16
doi: 10.1186/s12859-025-06071-x
---

# HGATLink: single-cell gene regulatory network inference via the fusion of heterogeneous graph attention networks and transformer

**Authors:** Yao Sun, Jing Gao
**Year:** 2025
**Venue:** BMC Bioinformatics

## Abstract
HGATLink is a supervised deep-learning framework for inferring gene regulatory
networks (GRNs) from single-cell RNA-seq data. It casts GRN inference as binary
link prediction over transcription-factor (TF)–target gene pairs, fusing a
heterogeneous graph attention network (HGAT) with a simplified transformer. The
HGAT operates on a discretized gene-expression matrix, using node-degree
information as attention query/key and max-pooling aggregation to capture
heterogeneous graph structure while alleviating transitive (indirect) edges; the
transformer then models long-range dependencies between gene pairs. On 14
scRNA-seq datasets against 10 state-of-the-art baselines, HGATLink reports the
best AUROC and near-best AUPRC.

## Key contributions
- Fuses a heterogeneous graph attention network with a simplified transformer for GRN link prediction, targeting transitive-interaction removal and long-range gene dependencies.
- Uses matrix decomposition to discretize the expression matrix into k equally-spaced segments (subgraphs / edge types), learning gene features in low-dimensional space.
- Degree-aware attention (degree as query/key) with max-pooling aggregation and adaptive weight adjustment, to preserve sparse-connection signal instead of over-smoothing.
- Removes positional encoding from the transformer (the HGAT already carries positional/topological info), simplifying the model.
- Combines three-fold cross-validation with a custom numerical-interval fold-split and hard negative sampling (HNS) to handle real-world positive/negative imbalance and small samples.

## Methods
Data follow the BEELINE protocol: 7 cell types (hESC, hHEP, mDC, mESC,
mHSC-E/GM/L) expanded to 14 datasets by taking top-500 and top-1000 most-variable
genes, with cell-type-specific ChIP-seq networks as ground truth. Positives are
known TF-target edges; HNS draws negatives from genes not regulated by the
cell-type-specific TFs. The HGAT builds subgraphs from the discretized expression
matrix; gene-pair feature vectors are extracted and fed to the transformer
(positional encoding removed) for link prediction via nonlinear transforms.
Trained with Adam, cross-entropy loss, lr 1e-3 (4e-4 for mESC), weight decay
1e-6, batch 512, ≤200 epochs on a Tesla V100S GPU. Metrics: AUROC and AUPRC,
evaluated over all test folds as a whole rather than averaged.

## Key results
- Best AUROC on 14/14 datasets, with up to +4% over the second-best method.
- Best AUPRC on 13/14 datasets.
- Ablation (transformer decoder removed): AUROC drops up to 5% and AUPRC up to 6% across 6 of 7 datasets (mESC unchanged); Wilcoxon p ≈ 0.026 (AUROC) / 0.027 (AUPRC).
- Adding positional encoding back hurts: AUROC down up to 17%, AUPRC down up to 34% — confirming the HGAT already encodes position.
- Best hyperparameters: matrix-decomposition k=15 (≤3% gain over k=10), embedding dim 256 (512 gave no gain, more instability), three-fold CV (comparable to five-fold, ANOVA p>0.95).
- Robust under label imbalance: reducing positives 10–40% still keeps HGATLink above the second-best baseline (hHEP, mHSC-L).

## Why it matters for our work
HGATLink is a direct data point for the BioReasoning Challenge's regulatory-edge
framing: it predicts TF→target regulatory links, the same up/none decision
structure underlying Track A/B. Two design levers are worth borrowing. (1) Hard
negative sampling plus a custom fold-split to fight sparse positives and class
imbalance — the same over-abstention / imbalance problem that sank our Track B
submission (LB 0.488). (2) Fusing a graph structural encoder with a transformer
so topology (short-range regulatory neighborhoods) and long-range dependencies
are captured jointly — a template for combining graph priors with sequence models
on Track C. The positional-encoding ablation is a useful reminder that a graph
encoder can subsume positional information, so stacking both can hurt.

## Limitations / open questions
- Supervised and benchmark-bound: relies on cell-type-specific ChIP-seq ground truth and BEELINE datasets; generalization to unlabeled or non-benchmark data is untested.
- Predicts edge existence only; no explicit activation-vs-repression direction/sign reported.
- Gains over the second-best method are modest (up to +4% AUROC), and "optimal on 14/14" is on small, curated datasets — real-world magnitude unclear.
- Several design choices (k=15, dim 256, three-fold CV) are tuned on the same benchmark suite, raising overfitting-to-benchmark risk.
