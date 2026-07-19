---
source_url: https://doi.org/10.1101/2025.10.31.685892
source_type: papers
title: "Empirical Evaluation of Single-Cell Foundation Models for Predicting Cancer Outcomes"
author: Haitham Elmarakeby et al.
retrieved: 2026-07-16
doi: 10.1101/2025.10.31.685892
---

# Empirical Evaluation of Single-Cell Foundation Models for Predicting Cancer Outcomes

**Authors:** Haitham Elmarakeby, Ahmed Roman, Shreya Johri, Eliezer M. Van Allen (Dana-Farber Cancer Institute)
**Year:** 2025
**Venue:** bioRxiv (preprint)

## Abstract
Single-cell foundation models (scFMs) pretrained on large-scale scRNA-seq data promise to advance translational cancer research, but their value for clinically relevant, patient-level tasks is underexplored. This study systematically benchmarks nine scFMs against three non-pretrained baselines across six cancer-specific tasks under zero-shot, continual-training, and fine-tuning regimes (1,170 supervised + 130 unsupervised experiments). The headline finding: while scFMs excel at some analyses (notably tumor-microenvironment cell annotation), they offer limited advantage over simpler baselines for predicting clinical/biological outcomes, underscoring the need for domain adaptation, rigorous benchmarking, and larger cancer cohorts before translational deployment.

## Key contributions
- Systematic head-to-head benchmark of 9 scFMs vs 3 baselines across 6 oncology tasks and 3 training paradigms.
- Evidence that model scale alone does not confer patient-level predictive advantage; simple baselines stay competitive.
- Quantifies that the cell-to-patient aggregation strategy can matter as much as the choice of embedding model.

## Methods
Twelve models were evaluated: Geneformer variants (GF-V1, GF-V2, GF-V2[cancer], GF-V2-Deep, GF-V1[continue]), scGPT and scGPT[cancer], scFoundation, SCimilarity, CellPLM, plus three baselines — Highly Variable Genes (top 4096 HVGs), PCA (top 100 PCs), and scVI (100-dim VAE latent). Three paradigms were tested: zero-shot (frozen embeddings), continual (unsupervised) domain adaptation, and end-to-end fine-tuning. Frozen embeddings fed a random forest (100 trees, depth 5) or a neural net; fine-tuning trained the whole model with a classifier head. Unsupervised embedding quality used ARI, NMI, ASW; supervised tasks used AUC, AUPRC, F1, accuracy, precision, recall over five CV folds. Cell-to-patient aggregation was tested via majority-vote, pseudo-bulk averaging, and multiple-instance learning (MIL).

## Key results
- **TME cell annotation (unsupervised):** scGPT[cancer] achieved the best NMI overall; GF-V1[continue] was the best Geneformer variant — continual domain adaptation let a smaller model beat larger ones. HVG was the weakest.
- **Patient-level prediction (pseudo-bulk):** scGPT[cancer] led (mean AUPRC ~0.89 ± 0.11), followed by SCimilarity (~0.88) and GF-V2-Deep (~0.87). Cancer-adapted GF-V2[cancer] (~0.86) beat generic GF-V2 (0.81).
- **Baselines stay competitive:** HVG reached ~0.90 ± 0.15 AUPRC, slightly outperforming the best scFMs on average; scVI (~0.87) matched top scFMs; PCA lagged (0.75).
- **Scale ≠ performance:** 316M GF-V2-Deep was matched/surpassed by smaller cancer-adapted GF-V2[cancer] (104M) and scGPT[cancer] (53M); 31M SCimilarity beat GF-V2-Deep without cancer training.
- **Aggregation matters:** choice of aggregation shifts AUPRC as much as the embedding model. MIL gave highest mean (0.866 ± 0.041) but largest variance; pseudo-bulk avg (0.844) comparable; majority vote most stable (0.842 ± 0.023).
- **Fine-tuning:** end-to-end fine-tuning of GF-V1/GF-V2 gave no consistent gain over frozen embeddings (Wilcoxon p ≈ 0.88 / ≈1.00) and did not decisively beat strong baselines, reflecting the small-sample cancer regime.

## Why it matters for our work
Directly informs Track C foundation-model strategy: it is a rigorous, negative-leaning benchmark showing that off-the-shelf scGPT/Geneformer/scFoundation embeddings do not reliably beat cheap baselines (HVG/PCA/scVI + random forest) on patient-level oncology prediction. The practical takeaways transfer to our up/down/none prediction pipelines — invest in domain-specific continual pretraining and in the aggregation/readout head rather than merely picking the biggest model, and always benchmark scFMs against simple feature-selection baselines before trusting them.

## Limitations / open questions
- Single modality only — transcriptional data; ignores copy-number and other tumor-genomic signals.
- Neural-net models deliberately used no hyperparameter tuning, adaptive LR, or early stopping; thresholded metrics used a fixed 0.5 cutoff.
- Small, imbalanced cancer cohorts limit fine-tuning and inflate metric variance; larger single-cell oncology cohorts are needed.
- Aggregation limited to standard schemes; biologically informed integration of cell-level signal remains open.
