---
source_url: https://doi.org/10.1186/s12864-025-11600-2
source_type: papers
title: "Benchmarking foundation cell models for post-perturbation RNA-seq prediction"
author: Csendes et al.
retrieved: 2026-07-16
doi: 10.1186/s12864-025-11600-2
---

# Benchmarking foundation cell models for post-perturbation RNA-seq prediction

**Authors:** Gerold Csendes, Gema Sanz, Kristóf Z. Szalay, Bence Szalai
**Year:** 2025
**Venue:** BMC Genomics (10.1186/s12864-025-11600-2)

## Abstract
The authors benchmark two single-cell foundation models — scGPT and scFoundation
— against simple baselines on the task of predicting post-perturbation RNA-seq
profiles. Across four Perturb-seq datasets, even the trivial "Train Mean"
baseline (predict the average training profile) beat both foundation models, and
a Random Forest using Gene Ontology features beat them by a large margin. They
trace the surprise to low perturbation-specific variance in standard benchmark
datasets, which lets trivial predictors score well and blunts the benchmarks'
ability to separate good from bad models.

## Key contributions
- Rigorous benchmark of scGPT & scFoundation vs. Train Mean, Elastic Net, kNN, Random Forest baselines on 4 Perturb-seq datasets (Adamson, Norman, Replogle K562, Replogle RPE1).
- Shows the Pearson Delta (differential-expression correlation) metric, not raw Pearson, is the meaningful evaluation metric.
- Diagnoses low intra-dataset heterogeneity as the root cause of misleadingly good trivial baselines.

## Methods
Data processed via GEARS' cell-gears package (normalized to 10k, log). Foundation
models fine-tuned per dataset (scGPT: 12 layers, dim 512, 15 epochs; scFoundation:
10 epochs) on A100 GPUs, using the GEARS Perturbation-Exclusive (PEX) train/test
split. Baselines used prior-knowledge embeddings of the perturbed gene (GO via
decoupler → PCA to 256 PCs, plus scGPT/scFoundation/scELMO embeddings) as features
and pseudo-bulk expression as target. Predictions aggregated to pseudo-bulk and
scored by Pearson, Pearson Delta, Pearson Delta on top-20 DE genes, and Pearson
Delta excluding CRISPR target genes.

## Key results
- **Train Mean beat foundation models on Pearson Delta** on all four datasets: 0.711 / 0.557 / 0.373 / 0.628 vs. scGPT 0.641 / 0.554 / 0.327 / 0.596 and scFoundation 0.552 / 0.459 / 0.269 / 0.471 (Adamson / Norman / Replogle K562 / RPE1).
- **Random Forest + GO features won overall**: 0.739 / 0.586 / 0.480 / 0.648 — outperforming foundation models by a large margin.
- RF on scGPT *pretrained* embeddings (0.727 / 0.583 / 0.421 / 0.635) beat *fine-tuned* scGPT, so fine-tuning, not representation, is a bottleneck; scELMO (LLM text) embeddings matched GO.
- In raw expression space all models scored Pearson > 0.95 (uninformative). scGPT's top-20-DE edge vanished once the CRISPR target gene (trivially predictable) was removed.
- Datasets have huge cell counts (~70k–160k) but few distinct perturbations (87 / 284 / 1093 / 1544); median pairwise DE correlation ranged 0.662 (Adamson, low heterogeneity) to 0.117 (Replogle K562), and higher heterogeneity correlated with better ability to distinguish models.

## Why it matters for our work
Directly relevant to Track C (foundation models) and to our up/down/none
perturbation-effect prediction. It is strong evidence that off-the-shelf scRNA-seq
foundation models do not beat trivial or prior-knowledge baselines on
post-perturbation prediction — so a GO/pathway-feature model (or ensembling FM
embeddings into a simple regressor) may be a better use of effort than fine-tuning
an FM. It also warns that small, low-variance CV sets mislead (echoing our own
Track B LB-vs-CV lesson): evaluate with Pearson Delta on high-heterogeneity data,
not raw correlation on homogeneous datasets.

## Limitations / open questions
- Only two foundation models (scGPT, scFoundation) tested; newer FMs may differ.
- Benchmarks assess only the PEX setup (new perturbations, one cell line); the CEX setup (new cell types) is untested — LINCS-L1000 / Mix-Seq suggested but need adaptation.
- All datasets are low-heterogeneity in vitro cell lines; single-cell data gave no advantage over pseudo-bulk here, an open question for more heterogeneous settings.
