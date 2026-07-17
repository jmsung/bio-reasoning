---
source_url: https://doi.org/10.1101/2025.01.28.635153
source_type: papers
title: "sciLaMA: A Single-Cell Representation Learning Framework to Leverage Prior Knowledge from Large Language Models"
author: Hongru Hu et al.
retrieved: 2026-07-16
doi: 10.1101/2025.01.28.635153
---

# sciLaMA: A Single-Cell Representation Learning Framework to Leverage Prior Knowledge from Large Language Models

**Authors:** Hongru Hu, Shuwen Zhang, Yongin Choi, Venkat S. Malladi, Gerald Quon
**Year:** 2025
**Venue:** bioRxiv preprint (Microsoft Research / UC Davis / Mayo Clinic)

## Abstract
sciLaMA (single-cell interpretable Language Model Adapter) is a representation-learning framework that bridges VAEs and LLMs for scRNA-seq analysis. VAEs handle tabular gene-expression matrices well but cannot ingest external prior knowledge (variable-length sequences or text); single-cell transformer LLMs encode rich prior knowledge but are computationally expensive and unreliable zero-shot. sciLaMA integrates *precomputed static gene embeddings* from pretrained multimodal LLMs with scRNA-seq data through a paired-VAE architecture, producing context-aware embeddings for both cells and genes. It outperforms SOTA methods on batch correction, cell clustering, gene imputation, and cell-state-specific marker/module discovery while remaining computationally efficient. Code: github.com/microsoft/sciLaMA.

## Key contributions
- An adapter framework that injects external LLM-derived gene knowledge into scRNA-seq analysis without training gene embeddings de novo.
- Extends siVAE's paired cell+gene VAE; a gene encoder takes fixed static LLM embeddings (D-dim) as input instead of scaling with cell count, removing siVAE's large-dataset limitation.
- Improves performance *and* cuts compute versus fine-tuning single-cell foundation models.

## Methods
Two paired encoder-decoders. The cell encoder maps each cell's M-gene expression vector to a K-dim latent posterior; the gene encoder maps each gene's D-dim static LLM embedding into the same K-dim contextual space. Reconstruction is the inner product of cell and gene decoder outputs (siVAE-style). Training is stepwise: (1) pretrain cell VAE, (2) freeze it and pretrain the gene encoder/decoder to adapt LLM embeddings to expression context, (3) joint ELBO optimization with an alignment regularizer (γ=0.05) tying cell and gene latent dimensions for interpretability. Prior-knowledge variants swap the input gene embeddings: sciLaMA-GenePT, -ProtTrans, -CellPLM, -ChatGPT, -ESM, -scGPT. A "self-informed" baseline sciLaMA (s.i.) learns gene embeddings from the transposed expression matrix alone (no LLM prior).

## Key results
- Cell clustering (5 pancreatic datasets): avg ARI 0.522, NMI 0.745 — beats scVI-batch by 16.78%/3.76% and fine-tuned scGPT by 8.07%/5.82%; ~1.5x the ARI/NMI of best zero-shot foundation models.
- Batch correction: batch-ASW 0.865, iLISI 0.238 — surpassing next-best by 16.26% and 96.69%.
- sciLaMA-scGPT beat fine-tuned scGPT by 6.82% on ARI/NMI with better batch integration, at **25x lower runtime**.
- Gene imputation (leave-one-gene-out, spatial osmFISH): +27.39% PCC, +15.58% SCC, +32.86% (1-JSD), +3.32% (1/RMSE) over the average of competing methods.
- Trajectory clarity on P0 mouse cortex: +20.65% over scVI. Contextual embeddings recovered a PPBP/Megakaryocyte gene module validated by GO enrichment.
- sciLaMA (s.i.), random, and shuffled baselines all underperformed — meaningful LLM priors act as regularization and prevent overfitting.

## Why it matters for our work
This is a Track C-relevant recipe for using foundation models *lightly*. Rather than fine-tuning a heavy single-cell LLM, sciLaMA freezes static gene embeddings (from scGPT, ESM, GenePT, etc.) and adapts them with a cheap paired-VAE — getting better accuracy at a fraction of the cost. For our gene-regulation prediction tasks it suggests a pattern: precompute gene embeddings from open-weight models once, then contextualize them with expression data through a small trainable head. The finding that arbitrary meaningful priors beat self-informed baselines (and that shuffled priors hurt) is a concrete argument for grounding predictions in external gene knowledge — directly relevant to how we might inject prior knowledge into Track A/B up/down/none perturbation predictions.

## Limitations / open questions
- bioRxiv preprint, not peer-reviewed; evaluated mainly on pancreas, PBMC, and mouse-cortex datasets — no large-scale atlas or perturbation benchmark.
- Uses *static* precomputed embeddings; quality is bounded by the upstream LLM and its gene coverage. Genes absent from the LLM vocabulary are unaddressed.
- No direct perturbation-response (Track A/B-style) task tested; benefit for predicting expression *change under perturbation* is unproven.
- Reported gains are relative percentages over baselines; absolute headroom and statistical significance across seeds are only partly reported.
