---
source_url: https://doi.org/10.1093/g3journal/jkad004
source_type: papers
title: "Identifying strengths and weaknesses of methods for computational network inference from single-cell RNA-seq data"
author: McCalla et al.
retrieved: 2026-07-16
doi: 10.1093/g3journal/jkad004
---

# Identifying strengths and weaknesses of methods for computational network inference from single-cell RNA-seq data

**Authors:** Sunnie Grace McCalla, Alireza Fotuhi Siahpirani, Jiaxin Li, Saptarshi Pyne, Matthew Stone, Viswesh Periyasamy, Junha Shin, Sushmita Roy
**Year:** 2023
**Venue:** G3: Genes|Genomes|Genetics

## Abstract
An expanded benchmark of eleven recent gene regulatory network (GRN) inference methods run on seven published scRNA-seq datasets spanning human, mouse, and yeast, evaluated against multiple gold-standard networks and metrics. The study measures both compute cost (time/memory, and thus scalability to genome-scale networks) and structural recovery, using global metrics (Area Under the Precision-Recall curve, F-score) and local metrics (how many regulators have accurately predicted target sets). The headline finding: most methods recover experimentally derived edges only modestly relative to random by global metrics, yet can capture biologically relevant targets of specific regulators, and adding prior knowledge plus transcription-factor-activity (TFA) estimation gives the best overall performance.

## Key contributions
- Head-to-head benchmark of 11 scRNA-seq GRN inference methods across 7 datasets in 3 species, with matched-condition bulk comparisons.
- Separates global topology recovery from local per-regulator recovery, showing they tell different stories.
- Quantifies the (non-)benefit of imputation and the effect of sequencing depth vs. cell count on inference quality.

## Methods
Eleven inference methods were benchmarked, grouped by whether they use expression only (e.g. SCENIC, PIDC, MERLIN, simple Correlation, GENIE3-style regressors) versus methods that add prior biological knowledge and estimate TF activity (Inferelator, MERLIN with priors). Algorithms were profiled for time and memory on datasets of varying size to flag those unlikely to scale to genome-scale GRNs. Predicted networks were scored against experimentally derived gold standards using AUPR and F-score (global) and per-regulator target recovery (local). The authors also tested imputation as a preprocessing step and compared single-cell-inferred networks against bulk-inferred networks for comparable conditions.

## Key results
- By global metrics (AUPR, F-score), all methods showed only modest recovery relative to a random predictor.
- Local metrics reversed the picture: methods correctly predicted targets for several regulators relevant to the biological system.
- Top expression-only methods were SCENIC, PIDC, MERLIN, and Correlation; simple correlation performed as well as or better than many purpose-built inference algorithms.
- Best overall performance came from methods adding prior knowledge + TFA (Inferelator and MERLIN with priors), outperforming expression-only methods.
- Imputation did not help most methods and was often detrimental to accuracy.
- Networks inferred from scRNA-seq were often better than or on par with those from matched bulk datasets; sequencing depth affected inference more than the number of cells.

## Why it matters for our work
The BioReasoning Challenge Tracks A/B ask us to predict a gene's up/down/none response, which is fundamentally a regulatory-relationship prediction. This benchmark is a sober prior: global edge-recovery from expression alone is near-random, so a purely expression-driven regulatory signal is weak and should not be over-trusted (echoing our Track B over-abstention lesson). Two actionable takeaways: (1) simple correlation is a strong, cheap baseline worth beating before adding complexity, and (2) injecting prior biological knowledge (curated TF-target priors) plus TF-activity estimation is what actually moves the needle — a strong argument for feeding curated regulatory priors into our direction-prediction features rather than relying on learned expression structure alone.

## Limitations / open questions
- Global metrics may under-credit methods because gold-standard networks are incomplete and noisy — the paper explicitly calls for better gold standards.
- Findings are on 2023-era methods; foundation-model / deep GRN approaches (relevant to Track C) are not covered.
- "Best" depends on metric choice and dataset depth, so no single method wins universally — method selection remains context-dependent.
