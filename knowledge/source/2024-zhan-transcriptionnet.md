---
source_url: https://doi.org/10.1093/bib/bbae433
source_type: papers
title: "A genome-scale deep learning model to predict gene expression changes of genetic perturbations from multiplex biological networks"
author: Lingmin Zhan et al.
retrieved: 2026-07-16
doi: 10.1093/bib/bbae433
---

# A genome-scale deep learning model to predict gene expression changes of genetic perturbations from multiplex biological networks

**Authors:** Lingmin Zhan, Yingdong Wang, Aoyi Wang, Yuanyuan Zhang, Caiping Cheng, Jinzhong Zhao, Wuxia Zhang, Jianxin Chen, Peng Li
**Year:** 2024
**Venue:** Briefings in Bioinformatics (2024), doi:10.1093/bib/bbae433 (PMC11370636)

## Abstract

TranscriptionNet is a deep-learning model that integrates multiple biological
networks to predict the transcriptional profile (gene expression changes, GECs)
induced by three types of genetic perturbation — RNA interference (RNAi), CRISPR
knockout, and overexpression (OE) — as measured in the L1000/CMap project. It
outperforms classical regressors at predicting the 978-landmark-gene response and
extrapolates GECs from the few thousand experimentally profiled genes to all
26,945 genes present in the input networks, for each perturbation type. On three
external tasks (gene coannotation, compound–target, disease–gene) the predicted
GECs match the quality of experimentally measured ones.

## Key contributions

- Predicts genome-scale perturbation transcriptomes purely from **network-derived
  gene representations**, extending coverage from ~3.5k–5k profiled genes to
  **26,945 genes** per perturbation type (22,496 RNAi, 21,806 CRISPR, 23,427 OE new).
- Two-stage coarse-to-fine architecture: **FunDNN** encodes each gene from seven
  fused human gene networks (via BIONIC network integration) into per-type
  "pre-GECs"; **GenSAN** is a self-attention transformer that refines one type's
  pre-GECs using the true (or predicted) GECs of the other two types on the same
  gene, plus a recursive "recycling" step.
- Custom **PMSE loss** = weighted sum of Pearson-correlation loss + MSE, to match
  both shape and magnitude of the target profile.

## Methods

Trained on L1000 CMap LEVEL-5 data (978 landmark genes; 4,454 RNAi, 5,139 CRISPR,
3,538 OE unique target genes after weighted-averaging replicates), values MinMax-
normalized to [−1,1], split 7:1:2 train/val/test. FunDNN inputs seven networks
(disease, drug, protein-complex, pathway, chromosomal-location, STRING PPI, protein-
sequence-similarity; 26,945 unique genes, ~7.5M interactions) integrated by BIONIC.
Each type is trained separately. Evaluation metrics: Pearson correlation coefficient
(PCC, primary), MSE, and Kolmogorov–Smirnov statistic D.

## Key results

- Beats five classical regressors (DTR, KNR, LR, RFR, XGBoost) and the FunDNN-only
  variant on average PCC/D for all three perturbation types; baseline regressors
  already reach PCC ~0.82–0.85 (RNAi/CRISPR) and ~0.92–0.94 (OE), with the full
  model on top. Profile-wise, TranscriptionNet has higher PCC than FunDNN, DTR,
  KNR, LR, RFR, XGBoost on 54.4%, 96.1%, 91.8%, 95.2%, 53.9%, 75.6% of GECs.
- Ablations: BIONIC beats deepNF / multi-node2vec / naive-union integration;
  multi-network features ≥ any single network; GenSAN + recycling add over FunDNN.
- External generalization — predicted GECs ≈ known GECs: compound–target ROC AUC
  0.74/0.76 (RNAi), 0.80/0.82 (CRISPR), 0.68/0.68 (OE) for known/predicted; combined
  logistic model AUC 0.81/0.85. Gene coannotation (KEGG, GO-BP) and disease–gene
  (cardiomyopathy) AUROC/AUPRC also comparable between predicted and measured GECs.

## Why it matters for our work

TranscriptionNet is directly on-target for BioReasoning Track A/B: it predicts
signed gene expression changes from genetic perturbation, the same up/down/none
signal we must call. Its core recipe — represent each gene from **fused prior-
knowledge networks** (pathways, PPI, complexes, disease/drug associations) and let
that carry perturbations with **no training signal** — is exactly the regime where
our agentic Track B over-abstained. The paper is evidence that multiplex-network
gene embeddings alone can extrapolate perturbation responses genome-wide, a concrete
alternative/complement to single-cell foundation-model or LLM priors, and its L1000/
CMap grounding matches the perturbation data our tracks draw from.

## Limitations / open questions

- Predicts only the **978 landmark genes** per perturbation (not the full
  transcriptome); coverage "genome-scale" is over *perturbations*, not readout genes.
- Bulk L1000 signatures, not single-cell; no cell-type context and no multi-gene /
  combinatorial perturbations.
- External-task performance is "similar to known GECs," not clearly better, and
  drug–target MCC is low for both (imbalanced-data / perturbation-vs-drug mismatch).
- Accuracy for unprofiled genes hinges on their connectivity in the input networks;
  poorly-annotated genes are inherently limited (no held-out unseen-gene benchmark).
