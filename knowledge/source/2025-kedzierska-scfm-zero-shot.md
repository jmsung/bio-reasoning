---
source_url: https://doi.org/10.1186/s13059-025-03574-x
source_type: papers
title: "Zero-shot evaluation reveals limitations of single-cell foundation models"
author: Kedzierska et al.
retrieved: 2026-07-16
doi: 10.1186/s13059-025-03574-x
---

# Zero-shot evaluation reveals limitations of single-cell foundation models

**Authors:** Kasia Z. Kedzierska, Lorin Crawford, Ava P. Amini, Alex X. Lu (Oxford; Microsoft Research)
**Year:** 2025
**Venue:** Genome Biology (short report) — 10.1186/s13059-025-03574-x

## Abstract
Single-cell foundation models such as scGPT and Geneformer are usually reported
fine-tuned, and had not been rigorously evaluated **zero-shot** — where the
pretrained embedding is used directly with no task-specific training. Zero-shot
performance matters for discovery settings where labels are unknown and
fine-tuning is impossible. Evaluating Geneformer and scGPT zero-shot on cell-type
clustering, batch integration, and their own pretraining reconstruction task, the
authors find both models are unreliable and are often **outperformed by simpler
methods**, arguing zero-shot evaluation is a critical step for developing and
deploying single-cell foundation models.

## Key contributions
- First rigorous **zero-shot** benchmark of scGPT and Geneformer as cell-embedding generators (vs. their usual fine-tuned evaluation).
- Compares against lightweight baselines: highly variable genes (HVG, 2000), scVI, and Harmony, across 5 human tissue datasets (Pancreas, two PBMC sets, cross-tissue Immune atlas, Tabula Sapiens).
- Ablates scGPT pretraining-set size (random init, 814k kidney, 10.3M blood, 33M human) to test whether more pretraining data helps.
- Probes the pretraining objective itself (gene-expression reconstruction) to separate "MLM doesn't yield good embeddings" from "the model failed to learn the task."

## Methods
Geneformer (BERT-style, ranked-gene input, MLM over gene ranks, 27.4M
transcriptomes) and scGPT (50-bin expression + gene tokens, MLM predicting masked
bins, ~3x more parameters) are run zero-shot; their cell embeddings feed
clustering and integration metrics. Cell-type separation is scored with Average
Silhouette Width (ASW) and AvgBIO (mean of ASW, NMI, ARI over optimized Louvain
resolutions); batch mixing with a batch-integration silhouette score and principal
component regression (PCR). Note the baselines are advantaged — scVI and Harmony
are trained on each target dataset (and use batch labels), reflecting the
practical reality that lightweight models are cheap to train.

## Key results
- On cell-type clustering (AvgBIO), both scGPT and Geneformer **underperform HVG, scVI, and Harmony**; HVG beats both foundation models across all metrics. scGPT only clearly wins on PBMC (12k) — the one dataset *not* seen in its pretraining.
- Datasets that *were* in pretraining (Tabula Sapiens, Immune for scGPT; Pancreas for Geneformer) did **not** get consistently better clustering — an unclear link between the pretraining objective and cell-type structure.
- Pretraining-size ablation: pretraining helps over random init and median score rises with data, but **scGPT-human (33M) slightly underperforms scGPT-blood (10.3M)** even on non-blood tissues — bigger/more-diverse pretraining plateaus.
- Batch integration: Geneformer ranks **last across all metrics** and its embeddings explain *more* batch variance than the raw data; scGPT beats scVI/Harmony only on complex datasets (which were in its pretraining, so confounded).
- Pretraining task: scGPT's reconstruction is **worse than predicting the per-gene mean bin**; Geneformer's rank predictions reach only median Pearson 0.56 (best 0.95).

## Why it matters for our work
Directly relevant to **Track C foundation-model selection** (`docs/foundation-models.md`):
it is concrete, cited evidence that scGPT/Geneformer embeddings are weak
**zero-shot** and can lose to HVG/scVI/Harmony — so for any zero-shot or
frozen-embedding use we should benchmark against cheap baselines rather than
assume the FM wins. It also cautions against trusting fine-tuned-only reports and
against assuming "bigger pretraining = better." For Track A/B up/down/none
prediction, the finding that these models poorly reconstruct their own expression
targets tempers expectations that their internal representations encode reliable
gene-regulation signal without task supervision.

## Limitations / open questions
- Baselines (scVI, Harmony) are trained on target data with batch labels while FMs run zero-shot — not a strictly matched comparison (authors defend it as the practical setting).
- Pretraining/eval overlap (Pancreas, Tabula Sapiens, Immune) confounds several "wins"; reviewers also flagged under-specified preprocessing/QC, HVG-selection, and clustering-resolution details.
- Only two, now somewhat dated, models tested; newer FMs (e.g., protein-informed gene representations, UCE) may address these gaps — but many don't release pretraining code.
- Whether these embeddings are useful for downstream tasks beyond clustering/integration (e.g., perturbation prediction) is left open.
