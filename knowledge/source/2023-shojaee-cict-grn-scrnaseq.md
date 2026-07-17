---
source_url: https://doi.org/10.1093/bib/bbad370
source_type: papers
title: "Robust discovery of gene regulatory networks from single-cell gene expression data by Causal Inference Using Composition of Transactions"
author: Shojaee & Huang
retrieved: 2026-07-16
doi: 10.1093/bib/bbad370
---

# Robust discovery of gene regulatory networks from single-cell gene expression data by Causal Inference Using Composition of Transactions

**Authors:** Abbas Shojaee, Shao-shan Carol Huang
**Year:** 2023
**Venue:** Briefings in Bioinformatics (Oxford), research article

## Abstract
This paper applies Causal Inference Using Composition of Transactions (CICT) to
infer gene regulatory networks (GRNs) from single-cell RNA-seq (scRNA-seq) data.
The core premise: if all gene expression were random, a genuine regulatory gene
would induce its targets at levels that deviate from the background random
process, leaving a distinctive statistical fingerprint in the full relevance
network of gene–gene associations. CICT engineers novel network features from
that relevance network so any supervised machine-learning model can directly
classify each candidate edge as causal-regulatory versus random. Benchmarked on
simulated and experimental scRNA-seq data via the BEELINE pipeline, CICT
outperformed diverse existing inference methods by 10 to >100-fold in accuracy,
and remained robust to sparsity, ground-truth type, association measure, and
model complexity.

## Key contributions
- Reframes GRN inference as **direct supervised prediction of causality** on edges, rather than correlation ranking or unsupervised modeling.
- Introduces a three-level feature construction (F0/F1/F2) from `conf`/`contrib` distribution "zones" around each edge's source and target nodes, encoding local and global network structure.
- Shows a small labeled set (as few as 250 true edges) plus a simple random forest (20 trees, depth 10) suffices — accuracy is decoupled from model complexity.

## Methods
CICT converts an expression matrix into a gene–gene association network, then for
each candidate edge computes confidence (`conf`) and contribution (`contrib`)
values and defines distribution zones around the source and target nodes. F0
features are Z-scores of the edge within each zone; F1 features summarize the
surrounding empirical distributions (moments, L-moments, skewness, etc.); F2
features re-Z-score F0/F1 across all edges to capture global position. Labels come
from prior GRNs, ChIP-seq, or knockout/overexpression (lof/gof) data, and may be
directed or undirected. A random forest trained on ~1–20% of true edges plus 4×
random edges predicts all remaining edges. Benchmarking used SERGIO simulations
(DS9–DS12; 100 genes, dropouts up to 87% zeros) and experimental human/mouse
datasets at three complexity levels (L0/L1/L2), evaluated with rpAUPR and rEPR
(ratios of partial-AUPR and early-precision to a random classifier).

## Key results
- On simulated data, CICT reached median rpAUPR **38.88** vs 8.55 for other methods, comparable to Inferelator-Prior (37.03); on cell-type-specific ChIP-seq ground truth CICT hit median rpAUPR **63.31** while most methods stayed at random.
- Under extreme dropout (q=80, ~87% zeros) CICT held **~75% accuracy** while most methods collapsed to random-classifier performance.
- Adding TF-outgoing-edge information gave a random forest **20× higher rpAUPR** (106 vs 5) on L2_lofgof; TF-info feature importance was ~400× the top non-TF feature.
- Top 5 predictors were all CICT F1 features; the leading one (L-kurtosis of source contrib.) separated regulatory vs random edges by mean log2 difference of 12, letting even a single decision stump discriminate edge direction.

## Why it matters for our work
For the BioReasoning Challenge, CICT is a concrete, data-efficient recipe for
turning noisy scRNA-seq into a **directed** regulatory graph — directly relevant
to justifying up/down/none predictions (Tracks A/B) from a TF perturbation. Its
central lesson, that *predicting causality directly beats ranking correlation*,
and its demonstrated robustness to dropout and tiny labeled sets, argue for using
inferred CICT-style edge features or priors rather than co-expression alone. The
finding that TF-identity is a dominant feature reinforces feeding known-TF
information into any directional-effect model.

## Limitations / open questions
- Supervised — still requires labeled ground-truth edges (ChIP-seq/lof-gof), which are incomplete and noisy.
- Benchmark scope capped at ~100–1500 genes; signed edges, unsupervised mode, and million-entity scaling were envisioned but not evaluated here.
- No integration of cell-type, lineage, temporal, or multi-omics (epigenomic/proteomic) information; post-inference pruning untested.
