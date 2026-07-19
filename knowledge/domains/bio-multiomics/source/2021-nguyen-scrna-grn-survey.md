---
source_url: https://doi.org/10.1093/bib/bbaa190
source_type: papers
title: "A comprehensive survey of regulatory network inference methods using single cell RNA sequencing data"
author: Hung Nguyen et al.
retrieved: 2026-07-16
doi: 10.1093/bib/bbaa190
---

# A comprehensive survey of regulatory network inference methods using single cell RNA sequencing data

**Authors:** Hung Nguyen, Duc Tran, Bang Tran, Bahadir Pehlivan, Tin Nguyen
**Year:** 2021
**Venue:** Briefings in Bioinformatics

## Abstract
Gene regulatory networks (GRNs) capture the interactions that dictate how cells develop and respond to their environment. Single-cell RNA sequencing (scRNA-seq) enables GRN inference at individual-cell resolution, recovering interactions hidden by the averaging inherent in bulk sequencing — but bulk-designed methods do not transfer, because they cannot resolve cell-type differences spatially/temporally and cannot cope with high sparsity (dropout) and large cell counts. This survey reviews 15 GRN inference methods built specifically for single-cell data, discussing their assumptions, inference techniques, usability, and trade-offs, and benchmarks them via simulation on accuracy, robustness to dropout, and time complexity.

## Key contributions
- In-depth review of 15 scRNA-seq GRN inference methods, grouped into four categories by how the network is built: (i) boolean models, (ii) differential equations, (iii) gene correlation, (iv) correlation ensemble over pseudo-time.
- A systematic simulation benchmark (139 datasets) evaluating each method on three metrics: reconstruction accuracy (AUROC vs. reference network), sensitivity to dropout/sparsity, and running time.
- A usability assessment (availability, documentation, input preparation, completion rate) to guide method selection.

## Methods
Reference networks were taken from the curated human TRRUST database, and scRNA-seq datasets were synthesized with GeneNetWeaver (the same generator used for DREAM4/DREAM5 gold-standard data), which uses ODEs/SDEs to produce data at multiple time points. Constructed networks were scored by AUROC against the reference. Three scenarios were run: (1) 200 samples with 20–3000 genes (30% dropout); (2) fixed 20 genes at sparsity levels 30/50/70/80/90%; (3) running-time scaling as genes (20→3000) and samples (200→1000) grow. Dropout was simulated by weighted random sampling that preferentially zeros low-expression values.

## Key results
- **Accuracy:** SCENIC (a GENIE3 random-forest method) had the highest median AUROC in essentially all gene-count settings — the best overall accuracy.
- **Scalability limits:** only 6 of 14 methods (SCODE, Information Measures, NLNET, SCENIC, LEAP, SCIMITAR) could analyze 3000-gene datasets; at 3000 genes all six collapsed to AUROC ~0.5 (random). Even at 20 genes peak AUROC was only ~0.62 (Information Measures).
- **Dropout robustness:** across 30–90% sparsity, only SCODE, SCOUP and SCENIC stayed consistently above AUROC 0.5; SCOUP was the most stable (SD 0.005 vs 0.013/0.026 for SCODE/SCENIC).
- **Speed:** LEAP and NLNET finished every analysis in minutes, even at 3000 genes / 1000 samples.
- **Usability:** SCODE, Information Measures, NLNET, SCENIC, LEAP scored 5/5; Inference Snapshot was unusable (never completed) and BTR had the lowest completion (27%, fails beyond 30 genes).

## Why it matters for our work
The BioReasoning Challenge asks systems to predict directional gene-perturbation effects (Track A/B up/down/none) and, in Track C, to leverage foundation models over gene regulation. This survey is a sober calibration of classical GRN inference: even the best method (SCENIC) degrades to random at realistic gene counts and high dropout, and no single method dominates all metrics. That argues against treating any off-the-shelf GRN tool as a reliable oracle for regulatory direction, and motivates our learned/foundation-model approaches — while flagging dropout, scalability, and the absence of cell-type-specific gold-standard networks as the core obstacles any predictor must confront.

## Limitations / open questions
- Benchmark uses simulated (GeneNetWeaver) data, which is "generally unsophisticated" and may embed distributions that favor certain methods — real biology is far more complex.
- Real-data validation relies on bulk-derived curated databases (TRRUST, RegulonDB, ESCAPE, CODEX) that lack cell-type specificity and cover only ~3000 of ~20,000 human genes, risking observer-expectancy bias.
- Methods remain sensitive to technical noise, scale poorly with gene/cell count, and the field lacks standard benchmarks — leaving the reliability of inferred single-cell GRNs an open question.
