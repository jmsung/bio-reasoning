---
source_url: https://doi.org/10.1038/s12276-025-01547-5
source_type: papers
title: "Single-cell foundation models: bringing artificial intelligence into cell biology"
author: Seungbyn Baek et al.
retrieved: 2026-07-16
doi: 10.1038/s12276-025-01547-5
---

# Single-cell foundation models: bringing artificial intelligence into cell biology

**Authors:** Seungbyn Baek, Kyungwoo Song, Insuk Lee
**Year:** 2025
**Venue:** Experimental & Molecular Medicine (Nature Publishing)

## Abstract
A review of single-cell foundation models (scFMs): large, transformer-based, self-supervised models pretrained on tens of millions of single-cell profiles that learn latent representations at both the cell and gene level for downstream analysis of cellular heterogeneity and regulatory networks. It covers scFM concepts, architecture, pretraining, and applications, then critically assesses limitations (nonsequential omics data, inconsistent data quality, compute intensity, hard-to-interpret embeddings) and proposes directions for improving robustness, interpretability, and scalability.

## Key contributions
- Synthesizes the scFM landscape (scBERT, scGPT, Geneformer, scFoundation, SCimilarity, etc.) under a common "cells = sentences, genes = tokens" framing.
- Lays out the full pipeline: data aggregation → tokenization → transformer architecture → pretraining objective → adaptation → downstream deployment.
- Critically compares zero-shot vs. fine-tuned performance and flags the field's benchmarking gap.

## Methods
Narrative review. Cells are tokenized by treating genes/features as tokens; because expression is non-sequential, models impose order (rank genes by expression and feed top genes as a "sentence," or bin expression values), optionally adding special tokens for cell identity, modality, or gene metadata. Architectures split into BERT-like bidirectional encoders (masked-gene prediction, e.g. scBERT) and GPT-style decoders (autoregressive next-gene prediction with specialized attention masking, e.g. scGPT); encoder–decoder hybrids also exist, with no architecture yet clearly superior. Pretraining uses masked language modeling, autoregressive modeling, value/rank reconstruction, and contrastive learning. Adaptation is via continual pretraining, fine-tuning (often freezing most layers), and parameter-efficient methods (LoRA, quantization). Pretraining draws on CZ CELLxGENE (100M+ cells), the Human Cell Atlas, GEO/SRA, PanglaoDB.

## Key results
- Compute: models of tens-to-hundreds of millions of parameters take days-to-weeks on 4–12 NVIDIA A100/H100 GPUs; the largest need larger clusters for over a month.
- scFMs in **zero-shot mode often do not outperform task-specific tools** designed for a given task; fine-tuning generally yields substantial gains but is nontrivial (compute, hyperparameters, data, expertise).
- Reported zero-shot strengths: cell-type prediction, gene-function prediction, spatial imputation; weaknesses: expression imputation, cross-platform batch integration, gene-network inference.
- No unified benchmark exists; the scEval pipeline (8 canonical tasks under consistent conditions) is an early standardization effort.

## Why it matters for our work
Directly relevant to Track C (foundation models) and to the perturbation-prediction core of Tracks A/B. scGPT/Geneformer/scFoundation are the exact candidate open-weights scFMs; the review's "virtual cell" framing — traversing latent space to predict post-perturbation transcriptional changes — is the mechanism behind predicting whether a gene's expression goes up/down/none after a perturbation. Its central caution is load-bearing for us: **zero-shot scFMs frequently lose to purpose-built baselines**, so we should not assume an off-the-shelf scFM beats a simple task-specific model without fine-tuning, and should treat our own CV/benchmarks skeptically given the field's benchmarking immaturity.

## Limitations / open questions
- No unified benchmarking framework; success on one downstream task does not generalize, making head-to-head model comparison unreliable.
- Latent embeddings and attention weights are hard to interpret biologically; attention interpretability is contested.
- Non-sequential expression data forces arbitrary tokenization/ordering choices with no consensus best practice; data-quality inconsistency (depth, batch effects, dropout) limits pretraining.
- Fine-tuning and inference remain resource-intensive, raising accessibility concerns; multiomics/epigenomic and cross-species integration are still largely unrealized.
