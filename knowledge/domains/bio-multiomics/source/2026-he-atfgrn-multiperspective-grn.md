---
source_url: https://doi.org/10.1093/bib/bbaf733
source_type: papers
title: "Revealing hidden regulatory dependencies: multi-perspective graph learning for single-cell gene regulatory network inference"
author: Wenying He et al.
retrieved: 2026-07-16
doi: 10.1093/bib/bbaf733
---

# Revealing hidden regulatory dependencies: multi-perspective graph learning for single-cell gene regulatory network inference

**Authors:** Wenying He, Rentao Zhang, Yaowei Zhu, Haolu Zhou, Yun Zuo, Yude Bai, Liang Yang, Fei Guo
**Year:** 2026
**Venue:** Briefings in Bioinformatics

## Abstract
ATFGRN is an adaptive topology-feature fusion graph neural framework for inferring gene regulatory networks (GRNs) from single-cell RNA-seq data. It fuses three complementary views of each candidate TF–target edge — local subgraph topology, expression-guided global structure, and expression-similarity — via attention-based weighting, and improves average AUROC by 5.09% over the best prior method across four network types.

## Key contributions
- A three-branch GNN that treats GRN inference as edge classification and fuses structural, expression, and similarity perspectives with learned attention weights.
- A subgraph-structure branch that extracts 2-hop local subgraphs per candidate edge (structural labeling + GCN) to capture higher-order topological dependencies — the single most important branch.
- A similarity branch built from a KNN graph + graph attention, recovering regulatory pairs that share expression patterns but lack explicit structural links.

## Methods
Each candidate edge gets three feature vectors. (1) Subgraph branch: extract the 2-hop neighborhood subgraph around the TF–target pair, apply structural labeling and GCN to encode local topology. (2) Expression-guided branch: normalize the scRNA-seq matrix into node features and run TransformerConv (multi-head dot-product graph attention) over the known GRN to capture expression–topology interactions. (3) Similarity branch: build a KNN gene-similarity graph and apply GAT, with a unidirectional LSTM skip-connection fusing outputs across GAT layers. The three branch features are combined by attention weighting and scored per edge. Benchmarks follow BEELINE preprocessing (TFs + 500 / TFs + 1000 gene sets) on seven scRNA-seq datasets (2 human, 5 mouse) against four ground-truth network types: STRING, cell-type-specific ChIP-seq, non-specific ChIP-seq, and mESC LOF/GOF. Best hyperparameters: 8 attention heads, 2 GNN layers, learning rate 0.001.

## Key results
- Average AUROC +5.09% over the second-best method (scMGATGRN) on 15 TFs+500 datasets; average AUROC >0.88 on TFs+1000 (>5% over all others); highest AUROC on all 30 datasets.
- AUPRC beats all baselines on 27/30 datasets; on the dense, imbalanced STRING network, average AUPRC 0.53 vs GATCL's 0.32.
- Ablation: removing the subgraph branch costs the most (−4.27% AUROC); removing global TransformerConv −1.61%; removing KNN similarity −1.74%.
- Only 2 GNN layers optimal — deeper layers cause over-smoothing.
- Case study: of 60 predicted hESC500 TF–target pairs, 52 were experimentally supported (hTFtarget/Cistrome DB + known networks); DeepImpute imputation helps most on sparse, cell-limited datasets (e.g. mDC AUPRC +7.11%).

## Why it matters for our work
ATFGRN is directly relevant to gene-regulation strategy for the BioReasoning Challenge. Its central lesson — that fusing structural topology, expression dynamics, and expression-similarity beats any single view for predicting TF–target regulatory edges — informs how we might engineer features or ensemble signals for Track A/B up/down/none direction prediction. The 2-hop subgraph branch dominating the ablation is a reminder that local network context, not just per-gene expression, carries the regulatory signal. Its over-smoothing finding (shallow 2-layer GNNs) and conditional-imputation result are practical guardrails if we build GNN-based baselines.

## Limitations / open questions
- Ground-truth networks (STRING/ChIP-seq/LOF-GOF) are imperfect proxies, not true GRNs.
- Negative sampling draws from a large candidate pool, risking false negatives.
- Supervised and data-hungry: weak at 10% training data, stabilizing only around 40%.
- Single-modality (scRNA-seq only); authors flag scATAC-seq / epigenomic multi-omics integration as future work.
