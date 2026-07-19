---
source_url: https://doi.org/10.1038/s41467-025-67481-2
source_type: papers
title: "scDrugMap: benchmarking large foundation models for drug response prediction"
author: Qing Wang et al.
retrieved: 2026-07-16
doi: 10.1038/s41467-025-67481-2
---

# scDrugMap: benchmarking large foundation models for drug response prediction

**Authors:** Qing Wang, Yining Pan, Minghao Zhou, Zijia Tang, Yanfei Wang, Guangyu Wang, Qianqian Song
**Year:** 2025
**Venue:** Nature Communications

## Abstract
scDrugMap is a unified framework (Python toolkit + interactive web server, scdrugmap.com) for benchmarking and predicting single-cell drug responses with foundation models. It evaluates ten models — eight single-cell foundation models (scFMs) and two general-purpose LLMs — across 495,237 cells from 60 datasets spanning diverse tissues, drugs, cancer types, and treatment regimens. It is the first systematic benchmark of foundation models for single-cell drug-response prediction, framed as binary sensitive-vs-resistant classification per cell.

## Key contributions
- First systematic benchmark of foundation models for single-cell drug response prediction (drug-sensitive vs drug-resistant classification).
- Curated 495,237 cells: a primary collection (326,751 cells / 36 datasets / 23 studies) plus an external validation collection (168,486 cells / 24 datasets / 6 studies).
- Two evaluation strategies — pooled-data (train/test within pooled category) and cross-data (train on one dataset, test on another, closer to clinical reality).
- Model-selection guidance + web server for prediction, biomarker discovery, and resistance-mechanism analysis.

## Methods
The eight scFMs benchmarked: scFoundation, scGPT, scBERT, Geneformer, CellLM, CellPLM, UCE, and tGPT; the two LLMs are LLaMa3 and GPT4o-mini. Each scFM was assessed under two training regimes — layer-freezing (frozen embeddings + classifier) and full fine-tuning — with 10-fold cross-validation. Metrics: F1 (primary, robust to class imbalance), AUROC, accuracy, precision, recall (plus AUPRC in supplement). GPT4o-mini was run zero/few-shot: prompts fed the top-10 (or top-100) highest-expressed genes per cell plus the data source, with a chain-of-thought variant tested; mini-batches of 10 cells limited hallucination from long inputs.

## Key results
- Pooled-data, fine-tuned: scFoundation was best overall, highest mean F1 across all tissue categories (PBMC 0.940, tumor 0.990, bone marrow 0.962, cell line 0.947); scBERT consistently worst. Fine-tuning beat layer-freezing overall.
- scGPT beat scFoundation on melanoma (F1 0.992 vs 0.978) and vemurafenib (1.000 vs 0.990).
- Cross-data (harder, clinically realistic): most models fell below F1 0.8. Under fine-tuning, UCE was strongest (e.g. tumor tissue F1 0.774); under layer-freezing, scGPT led in tumor tissue (0.858). scFoundation lost its edge, generalizing poorly.
- Validation collection (layer-freezing): scFoundation best across all tissue/drug/cancer categories (e.g. NSCLC F1 0.997), confirmed by AUROC.
- GPT4o-mini performed at or below baseline (best: liver cancer F1 0.690; immunotherapy only 0.391), showing general LLMs lack precision for this task without domain adaptation.

## Why it matters for our work
Directly relevant to Track C (open-weights foundation models) and to the broader up/down/none prediction framing. It gives an evidence-based ranking of single-cell FMs — scFoundation for pooled/in-distribution, UCE/scGPT for cross-dataset generalization — and a stark warning that a general LLM prompted with top-expressed gene names barely beats baseline (F1 ~0.39–0.69). This argues for domain-specific embeddings or fine-tuning over naive LLM prompting, and shows chain-of-thought prompting gives only marginal lift. The pooled-vs-cross-data gap mirrors our own CV-vs-LB generalization concerns.

## Limitations / open questions
- Cross-data F1 largely below 0.8 and AUPRC below 0.7 — current FMs are not yet clinically reliable on independent datasets.
- Severe class imbalance (e.g. small prostate/pancreatic sets, ~11–21% sensitive cells) likely inflates some near-perfect F1 scores; reviewers flagged over-interpretation of marginal cross-data wins.
- Downside-error cost: a fine-tuned scGPT case study (F1 0.2645) missed key biology (COL1A2/SEZ6L2, p53 pathway) that ground-truth labels revealed.
- 10 folds are technical replicates, not independent biological replicates; no Pearson/Spearman correlation reported alongside F1/AUROC.
