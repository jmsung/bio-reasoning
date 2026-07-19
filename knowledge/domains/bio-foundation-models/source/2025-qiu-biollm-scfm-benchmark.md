---
source_url: https://doi.org/10.1016/j.patter.2025.101326
source_type: papers
title: "BioLLM: A standardized framework for integrating and benchmarking single-cell foundation models"
author: Ping Qiu et al.
retrieved: 2026-07-16
doi: 10.1016/j.patter.2025.101326
---

# BioLLM: A standardized framework for integrating and benchmarking single-cell foundation models

**Authors:** Ping Qiu, Qianqian Chen, Hua Qin, Shuangsang Fang, Yilin Zhang, Yanlin Zhang, Tianyi Xia, Lei Cao, Yong Zhang, Xiaodong Fang, Yuxiang Li, Luni Hu
**Year:** 2025
**Venue:** Patterns (Cell Press)

## Abstract
Single-cell foundation models (scFMs) are hard to apply and compare because each ships with a different architecture, preprocessing pipeline, and coding standard. BioLLM ("biological large language model") is a unified framework that wraps diverse scFMs behind one interface with standardized APIs, so researchers can switch models and run consistent, apples-to-apples benchmarks on scRNA-seq analysis. Using BioLLM, the authors benchmark four leading scFMs (scBERT, Geneformer, scFoundation, scGPT) across cell embedding, gene regulatory network (GRN) inference, cell-type annotation, and drug-response prediction, in both zero-shot and fine-tuning regimes.

## Key contributions
- A single unified loader/interface for scBERT, Geneformer, scFoundation, and scGPT (plus later CellPLM), removing architectural and coding inconsistencies.
- Three integrated modules: decision-tree preprocessing/QC, a "BioTask" executor (5 stages: config parse → model init → preprocess → data-loader → task exec), and an evaluation suite (silhouette scores, GRN/GO fidelity, classification metrics).
- A head-to-head benchmark across four downstream tasks with standardized metrics.

## Methods
Cell/gene embeddings are produced either zero-shot or via supervised fine-tuning. Embedding quality is measured by average silhouette width (ASW) for cell type and batch mixing (batch ASW scaled to 0–1). GRNs are built from gene-embedding similarity, clustered with Leiden (resolution 0.1–1.0), and scored by GO-pathway enrichment (adj. p < 0.01). Cell-type annotation is evaluated across 13 datasets with accuracy, precision, recall, and macro F1, benchmarked against singleR, celltypist, and scANVI. Drug response is tested by swapping DeepCDR's transcriptomic feature extractor for each scFM's embeddings and predicting IC50 (GDSC/CCLE), scored by Pearson (PCC) and Spearman (SRCC) correlation.

## Key results
- scGPT was the strongest overall: best zero-shot cell-embedding ASW, best cell-type annotation (highest accuracy/macro F1, best rare-cell-type recovery), and it beat traditional tools (singleR, celltypist, scANVI); longer input gene sequences further improved its embeddings.
- On batch correction, scGPT beat PCA but the other three scFMs performed worse than PCA; scGPT still struggled to correct cross-technology batch effects.
- Gene-level tasks favored Geneformer and scFoundation: scGPT, scFoundation, and Geneformer all enriched more GO pathways than scBERT in GRN analysis; for drug response, Geneformer and scGPT gave the highest PCC/SRCC and improved on baseline DeepCDR (scBERT gave no gain).
- Efficiency: Geneformer had the lowest runtime/GPU use (annotated 100k cells in under 1 h), scGPT close behind; scBERT and scFoundation were slowest. Fine-tuning gave consistent gains (largest in precision and macro F1) over zero-shot.
- scBERT lagged across all tasks, attributed to its smaller model size and limited training data.

## Why it matters for our work
This is a direct map for Track C (open-weights foundation models): it benchmarks the exact scFM candidates we would consider (scGPT, Geneformer, scFoundation, scBERT) on the tasks closest to the challenge and tells us where each wins. scGPT is the safe default for cell-level representation and annotation, while Geneformer/scFoundation are stronger for gene-level and regulatory tasks — relevant to gene-regulation up/down/none prediction in Tracks A/B. BioLLM's standardized loader and evaluation harness is also a template for how we could swap and score models consistently rather than hand-tuning per model.

## Limitations / open questions
- Benchmark covers only four (later five) scFMs; newer/larger models are not included.
- No batch-related information in pretraining hurts cross-technology integration — an open failure mode even for the best model (scGPT).
- Results are reported qualitatively (rankings, figures) rather than as a single reproducible metric table in-text; exact per-model scores live in supplemental figures.
- Task set is scRNA-seq-centric (annotation, GRN, drug response); it does not directly test the perturbation up/down/none regression framing of the BioReasoning tracks.
