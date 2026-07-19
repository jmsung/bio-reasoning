---
source_url: https://doi.org/10.1093/nsr/nwaf255
source_type: papers
title: "Cell-GraphCompass: modeling single cells with graph structure foundation model"
author: Chen Fang et al.
retrieved: 2026-07-16
doi: 10.1093/nsr/nwaf255
---

# Cell-GraphCompass: modeling single cells with graph structure foundation model

**Authors:** Chen Fang, Wentao Cui, Zhilong Hu, Wenhao Liu, Shubai Chen, Shaole Chang, Qingqing Long, Cong Li, Yana Liu, Haiping Jiang, Pengfei Wang, Jia Pan, Guoping Hu, Guole Liu, Zhen Meng, Yuanchun Zhou, Linghui Chen, Guihai Feng, Xin Li
**Year:** 2025
**Venue:** National Science Review

## Abstract
Most single-cell foundation models (scGPT, Geneformer) impose a *sequential* token order on the genes within a cell, discarding intrinsic biology and unused prior knowledge. Cell-GraphCompass (CGCompass) instead models each cell as a **graph**: nodes are genes, edges encode gene–gene relationships. A GNN + transformer architecture jointly learns gene and cell embeddings via message passing plus self-attention. Pre-trained on ~50M human cells (scCompass-h50M) and fine-tuned to batch integration, cell type annotation, single-cell perturbation, and bulk knockout prediction, it reaches state-of-the-art on all four.

## Key contributions
- First single-cell FM to use **graph pre-training** rather than a sequential gene ordering.
- Six biological features fused into the cell graph — **node features:** gene names, gene expression values, gene text descriptions (BioBERT); **edge features:** TF–target-gene interactions (TFBSDB, TRRUST), gene co-expression (Pearson corr > 0.6), chromosomal positional adjacency.
- A **global cell node** connected to all gene nodes to explicitly represent cellular state.
- A two-step (secondary) transfer to bulk knockout: single-cell pre-train → mouse bulk pre-train → knockout fine-tune, with a two-step up/none/down classifier.

## Methods
Pre-training masks 40% of gene expression values and reconstructs them from the remaining 60% (self-supervised) on 50M human scRNA-seq cells. The modular encoder→GNN→transformer→decoder design is re-headed per downstream task; fine-tuning uses the same masked objective (integration), classification heads (annotation), or a perturbation decoder. For bulk knockout, CGCompass is re-pretrained on ~300k filtered mouse bulk profiles (ARCHS4) then fine-tuned on ~3300 mouse bulk knockouts, using focal loss to handle the severe class imbalance (only ~4% of genes are DE).

## Key results
- **Gene-level zero-shot:** beats gene2vec, BioBERT, and random embeddings on all six gene-classification datasets (MacroF1, AUC-PR, kappa) and on GGI reconstruction across eight STRING/ChIP-seq datasets (EPR, AUC-PR).
- **Batch integration & annotation:** best NMI/ARI/ASW/GraphConn vs. from-scratch models and fine-tuned FMs; >90% per-type accuracy on the MS dataset; only CGCompass gave usable linear-probe zero-shot annotation.
- **Single-cell perturbation (Norman, Adamson, Dixit):** both FMs beat GEARS; CGCompass beats scGPT on MSE / corr / corr_delta and on **direction accuracy (up/no-change/down)**; largest margin on the 20-perturbation Dixit set (few-shot).
- **Bulk knockout:** a transformer baseline collapses to "all unchanged" (95% acc, ~0 DE recall); CGCompass exceeds 90% overall accuracy while recovering the most DE genes; finer 5-class direction supervision improves it further.
- Same-data comparison (scCompass-h5M) and per-feature ablations confirm both the graph structure and each of the six features contribute.

## Why it matters for our work
The bulk-knockout head predicts each gene's post-perturbation **direction as three classes — up / no change / down** — which is exactly the Track A/B up/down/none prediction shape, and it names our core failure mode: a naive model predicts "no change" everywhere for high accuracy but near-zero DE recall (cf. our Track B over-abstention at LB 0.488). Their fixes — focal loss, a two-step change-then-direction classifier, and finer 5-class supervision — are directly portable levers for beating the no-signal-tie floor. As a Track C candidate, CGCompass is also a concrete argument that injecting TF–TG / co-expression / literature priors as graph edges outperforms sequence-token FMs.

## Limitations / open questions
- Weights/data availability and parameter count not stated in-text; open-weights status for Bing's endpoint unconfirmed.
- Bulk knockout transfer is **mouse-only**; human generalization untested.
- Echoes the Ahlmann-Eltze linear-baseline critique: when single-cell predictions are aggregated, FMs can lose to linear models — CGCompass only wins when fed pseudo-bulk profiles directly, so the framing matters.
- "Best" claims lean on supplementary tables; no absolute headline metric given in the main text.
