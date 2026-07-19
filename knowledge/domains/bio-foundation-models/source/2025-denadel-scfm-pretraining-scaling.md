---
source_url: https://doi.org/10.1101/2024.12.13.628448
source_type: papers
title: "Evaluating the role of pre-training dataset size and diversity on single-cell foundation model performance"
author: Alan DenAdel et al.
retrieved: 2026-07-16
doi: 10.1101/2024.12.13.628448
---

# Evaluating the role of pre-training dataset size and diversity on single-cell foundation model performance

**Authors:** Alan DenAdel, Madeline Hughes, Akshaya Thoutam, Anay Gupta, Andrew W. Navia, Nicolo Fusi, Srivatsan Raghavan, Peter S. Winter, Ava P. Amini, Lorin Crawford
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
Single-cell foundation models (scFMs) have been trained on ever-larger transcriptomic corpora, scaling from ~1M cells to atlases over 100M cells, on the assumption that more data yields better models. Using a 22.2M-cell corpus (scTab, a CELLxGENE subset), the authors pre-train 400 models and run 6,400 evaluation experiments to isolate the effect of pre-training dataset **size** and **diversity**. The central finding: current scFMs plateau in downstream performance using only a tiny fraction of available training data, so continued scaling of pre-training corpora is unlikely to pay off.

## Key contributions
- First systematic, controlled study of pre-training size × diversity for scFMs, holding architecture fixed while sweeping corpus fraction (1/10/25/50/75/100%) and downsampling scheme.
- Defines a "learning saturation point": the smallest corpus fraction reaching 95% of a model's max score.
- Tests five representative models across three tasks and adds model-axis (size/loss/hyperparameter) and Perturb-seq "spike-in" experiments.

## Methods
Five general-use models were evaluated: **Pre-trained PCA, scVI (VAE), SSL (masked autoencoder), Geneformer (transformer), and SCimilarity**, against simple baselines (raw HVGs, top-50 PCs, logistic regression). Three downsampling schemes probed diversity: uniform random, cell-type re-weighted, and geometric sketching (samples uniformly over transcriptional space). Three downstream tasks: zero-shot + fine-tuned cell-type classification (micro-F1) on 4 held-out datasets, zero-shot batch integration (AvgBIO: ASW/NMI/ARI), and fine-tuned perturbation prediction (R²/MSE) on a Tahoe-100M subset. Spike-in experiments replaced 10%/50% of scTab cells with Replogle et al. genome-wide Perturb-seq cells to test task-aligned pre-training data.

## Key results
- **Performance saturates early.** Fine-tuned classification typically saturated at **1%** of the corpus (~200,000 cells; <1 GB of raw counts) and never needed more than 10%. Zero-shot classification, batch integration, and perturbation prediction showed the same pattern across all architectures and datasets.
- **More diversity did not help.** Cell-type re-weighted and geometric-sketching downsampling gave no gains over random subsampling on any task.
- **Simple methods often win.** Pre-trained PCA, scVI, and baselines (PCA, logistic regression) frequently beat SSL and Geneformer in absolute terms; SCimilarity was the best classifier (its pre-training objective is aligned with cell-type representation).
- **Perturbation prediction is weak:** for all drugs except one, a "predict no change" baseline outperformed every fine-tuned model.
- **Spike-in didn't help.** Adding Perturb-seq cells did not improve classification or batch integration.
- **Model size vs. data:** larger scVI/Geneformer models improved absolute accuracy but still saturated at tiny data fractions; Geneformer scaled poorly on both data and model size.

## Why it matters for our work
Directly relevant to **Track C (foundation models)**: it argues that picking or scaling a bigger open-weights scFM is not a reliable win — task-aligned objectives, data quality, and even simple embeddings (PCA/scVI) can match or beat large transformers. For **Track B perturbation prediction**, the paper's finding that a "no-change" baseline beats fine-tuned scFMs corroborates our own over-abstention result and warns against trusting complex models on rank/effect metrics. Cheap embeddings + task-matched heads may be a stronger, more compute-efficient strategy than heavyweight scFM inference.

## Limitations / open questions
- scTab was used as-is with no QC/curation beyond downsampling; data-quality scaling laws (vs. raw size) were not directly optimized here.
- Only five architectures and a bounded 22.2M-cell corpus — does not rule out gains at 100M+ cells with better tokenization or biologically informed losses.
- No unified compute-data-parameter scaling law was derived; the authors flag this as the key open direction.
