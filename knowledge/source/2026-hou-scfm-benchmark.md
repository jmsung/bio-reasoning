---
source_url: https://doi.org/10.64898/2026.01.06.698060
source_type: papers
title: "A unified framework enables accessible deployment and comprehensive benchmarking of single-cell foundation models"
author: Hou et al. (senior: Xiang Zhou)
retrieved: 2026-07-16
doi: 10.64898/2026.01.06.698060
---

# A unified framework enables accessible deployment and comprehensive benchmarking of single-cell foundation models

**Authors:** Siyu Hou, Penghui Yang, Wenjing Ma, Jade Xiaoqing Wang, Xiang Zhou
**Year:** 2026
**Venue:** bioRxiv (10.64898/2026.01.06.698060)

## Abstract

A Nextflow-based, containerized framework that standardizes deployment and
evaluation of single-cell foundation models (scFMs), plus the most comprehensive
scFM benchmark to date: 13 scFMs vs. classical baselines across >50 datasets under
zero-shot, few-shot, and fine-tuning regimes. Pretrained embeddings capture
biologically meaningful structure and win in low-label / transfer settings, but a
classical HVG+PCA pipeline stays competitive or superior in many others. The work
lowers technical barriers and sets a reproducible standard for community evaluation.

## Key contributions

- Unified, model-agnostic wrapper interface (AnnData in → embeddings out), each model in its own Docker/Singularity container, orchestrated as a one-command Nextflow DAG.
- Benchmarks 13 scFMs — CELLama, CellFM, CellPLM, Geneformer, GenePT-w, LangCell, scBERT, scCello, scFoundation, scGPT, SCimilarity, scPRINT, UCE — vs. a 2,000-HVG + 50-dim PCA baseline.
- Six evaluation datasets published after Oct 2025 to control for pretraining data leakage.
- Corrects prior perturbation-benchmark implementation errors, changing the reported conclusions.

## Methods

Raw count matrices are the single standardized input; all model-specific
preprocessing (tokenization, normalization, gene-ID mapping) lives inside each
wrapper, so downstream evaluation code is uniform. Released weights/code treated as
authoritative — only minimal bug fixes, no changes to model internals. Tasks span
representation learning, trajectory inference (Slingshot), spatial transcriptomics
transfer, prototypical few-shot annotation, fine-tuning, and perturbation prediction.
Splits are stratified and identical across models. Resource profiling on H200 GPUs.

## Key results

- **Zero-shot clustering:** PCA ranks 2nd overall; only SCimilarity (a large MLP encoder, not a transformer) clearly beats it. On a stomach dataset PCA ARI=0.65 vs SCimilarity 0.68, other models ~0.57. Transformer models (scGPT, Geneformer) show no consistent edge.
- **Trajectory inference:** PCA is a strong baseline; only scFoundation slightly exceeds it. PCA best at neighborhood preservation (0.95 vs 0.72 for scFoundation).
- **Spatial transcriptomics:** No scFM beats PCA under zero-shot; scRNA-seq-pretrained models fail to transfer across modality shift (Visium/ST/MERFISH).
- **Few-shot annotation:** Baseline accuracy rises 0.54 (1-shot) → 0.88 (5-shot); pretrained embeddings help most at 1-shot. Only UCE, SCimilarity, scFoundation, scGPT, LangCell consistently beat raw expression.
- **Fine-tuning:** Most methods reach ~98% cell-type accuracy — including PCA (2nd overall). Perturbation prediction: no model beats an additive baseline, but after fixing implementation issues several match it (vs. "substantially worse" in prior reports).

## Why it matters for our work

Directly relevant to **Track C** (open-weights foundation models — see
[`docs/foundation-models.md`](../../docs/foundation-models.md)): it is a rigorous,
leakage-controlled ranking of the exact scFM candidates we'd consider, with practical
GPU/runtime profiles and a strong caution that model scale ≠ better performance. The
headline lesson for Track A/B (gene-perturbation up/down/none prediction): scFM
embeddings rarely beat a simple HVG+PCA or additive baseline, and **no model beat an
additive baseline for perturbation-effect prediction** — reinforcing our own finding
that simple baselines are hard to beat. scFMs pay off mainly in very-low-label /
transfer regimes.

## Limitations / open questions

- Perturbation eval uses Norman (double) and Replogle K562 (single) — chemical/genetic and cell-context gap from our macrophage CRISPRi task.
- "Competitive PCA" conclusions are on standard single-cell tasks, not the challenge's specific up/down/none scoring.
- Fixing others' implementation bugs is judgment-laden; some fixes may not match original authors' intent.
- Several figure references are unresolved placeholders in this preprint — some magnitudes are illustrative single-dataset examples, not aggregate.
