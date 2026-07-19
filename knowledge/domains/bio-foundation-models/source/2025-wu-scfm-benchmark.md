---
source_url: https://doi.org/10.1186/s13059-025-03781-6
source_type: papers
title: "Biology-driven insights into the power of single-cell foundation models"
author: Jialu Wu et al.
retrieved: 2026-07-16
doi: 10.1186/s13059-025-03781-6
---

# Biology-driven insights into the power of single-cell foundation models

**Authors:** Jialu Wu, Qing Ye, Yilin Wang, Renling Hu, Yiheng Zhu, Mingze Yin, Tianyue Wang, Jike Wang, Chang-Yu Hsieh, Tingjun Hou
**Year:** 2025
**Venue:** Genome Biology

## Abstract
A biology-oriented benchmark of six single-cell foundation models (scFMs) — Geneformer, scGPT, UCE, scFoundation, LangCell, scCello — against well-established baselines (HVG selection, Seurat, Harmony, scVI, logistic regression) under realistic, zero-shot conditions. It spans two gene-level and four cell-level tasks (batch integration, cell type annotation, cancer cell identification, drug sensitivity prediction) across five integration datasets, seven cancer types, and four drugs, scored with 12 metrics including a novel cell-ontology-informed metric, scGraph-OntoRWR. Core finding: scFMs are robust, transferable, general-purpose embedders, but no single scFM wins across all tasks, and simpler ML models remain competitive — even superior — on individual datasets under resource limits.

## Key contributions
- Systematic zero-shot benchmark of six scFMs vs strong classical baselines on six biologically meaningful tasks.
- New biology-aware metrics: scGraph-OntoRWR (cell-ontology-consistency of the embedding space) and LCAD (severity-of-error via ontology distance between misclassified cell types).
- Introduces an unseen, leakage-free dataset (AIDA v2, ~201K immune cells, released April 2025) to validate conclusions.
- Uses the roughness index (ROGI) as a training-free proxy to recommend a model per dataset, and a non-dominated (Pareto) sorting scheme to aggregate metrics into task-specific and overall rankings.

## Methods
Zero-shot cell/gene embeddings are extracted from each pretrained scFM (no fine-tuning) and fed into task-specific heads (OnClass for annotation, SCAD for drug sensitivity, Cancer-Finder-style classifier for cancer ID). Batch integration is scored with scIB (bio-conservation + batch correction), scGraph-PCA, and scGraph-OntoRWR. scGraph-OntoRWR builds a dataset-independent reference graph from the expert Cell Ontology (~2700 cell types), weighting "is_a" edges by LangCell text similarity and running random-walk-with-restart, then correlating it with the embedding-derived cell-type centroid graph. Attention weights are probed for GRN inference as a proof-of-concept.

## Key results
- Under scIB metrics, scFMs do NOT surpass HVG/scVI baselines on batch integration — but under the biology-aware scGraph-OntoRWR, all scFMs exceed scVI/Harmony; leading scFM (scCello) beats scVI by +0.187 (+38.8%) in cell-type-relationship PCC.
- Cell type annotation: scFoundation and UCE top standard metrics (Accuracy@1, macro-F1); scCello wins ontology-aware metrics; logistic regression and scVI are strong baselines. Pairwise ensembles help rare types (Geneformer+scGPT: 67.4% → 75.6% accuracy).
- Cancer cell ID: scGPT (AUROC 0.824) ≈ UCE (0.823) > scVI (0.811); all scFMs beat raw-count baseline.
- Drug sensitivity: all scFMs beat the SCAD baseline; scFoundation (AUROC 0.755) and scGPT (0.737) lead.
- Performance gains track a smoother embedding landscape: model AUROC vs ROGI correlates r = −0.83, so ROGI predicts the best model with no training.
- Overall top performers: scFoundation and UCE (largest pretraining data / model size); no scFM dominates all tasks.

## Why it matters for our work
Directly informs Track C foundation-model selection: for the BioReasoning Challenge we should not assume one scFM is universally best — pick per task/dataset, and consider ROGI as a cheap, training-free selection proxy. It confirms zero-shot scFM embeddings as strong plug-and-play features while cautioning that simple baselines (HVG, scVI, logistic regression) can match or beat them on narrow tasks — a useful sanity check for our Track A/B up/down/none prediction and gene-regulation strategy. The attention-based GRN proof-of-concept and ontology-aware metrics also suggest evaluation angles beyond raw accuracy.

## Limitations / open questions
- Zero-shot only — no fine-tuning; task-optimal ranking could shift with adaptation.
- scIB vs scGraph vs scGraph-OntoRWR rankings are weakly correlated, so conclusions depend heavily on metric choice.
- Full-model ensembles underperform curated pairwise ensembles; how to auto-select complementary models is open.
- Bulk-vs-single-cell scale mismatch harms some models (e.g. UCE's gene sampling), and results cover a limited set of tasks/drugs/tissues.
