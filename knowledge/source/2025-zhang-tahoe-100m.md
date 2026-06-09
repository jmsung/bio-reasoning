---
source_url: https://www.biorxiv.org/content/10.1101/2025.02.20.639398v1
source_type: papers
title: "Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas"
author: Zhang et al. (senior: Goodarzi, Yu)
retrieved: 2026-06-08
---

# Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling

**Authors:** J. Zhang, A. A. Ubas, R. de Borja, V. Svensson, N. Thomas, … H. Goodarzi, J. Yu
**Year:** 2025
**Venue:** bioRxiv (10.1101/2025.02.20.639398)

## Abstract

A giga-scale single-cell atlas of ~100M transcriptomic profiles measuring how
1,100 small-molecule perturbations affect cells across 50 cancer cell lines. The
"Mosaic" platform pools an optimally balanced "cell village" to reduce batch
effects and profile thousands of conditions in parallel at single-cell
resolution. Released publicly to accelerate AI frameworks for systems biology.

## Key contributions

- Largest single-cell perturbation dataset to date: ~100M cells.
- 1,100 small-molecule (drug) perturbations × 50 cancer cell lines.
- "Mosaic" platform + "cell village" multiplexing to cut batch effects and
  enable massively parallel condition profiling.
- Public release as a general-purpose perturbation atlas for AI / representation learning.

## Methods

Pooled, multiplexed scRNA-seq: many cell lines co-cultured ("cell village") and
treated across many compounds, then demultiplexed computationally. All conditions
share a run, controlling batch effects, and the design scales to thousands of
conditions.

## Key results

- Resource/dataset paper — the headline is the atlas itself (scale + balance),
  not a single predictive metric.
- Captures context-dependence: same drug, different cell line → different
  response, at scale.

## Why it matters for our work

A candidate augmentation / pretraining source (roadmap #2), but with a large
domain gap: Tahoe uses small-molecule (chemical) perturbations in cancer cell
lines, whereas Track A/B is genetic (CRISPRi) perturbation in macrophages.
Two team leads for extracting transferable signal despite the gap (see
findings + roadmap):

- **Housekeeping-gene perturbations** may produce cell-type-invariant responses,
  making them the most transferable slice across datasets/contexts (connects to
  our EDA: housekeeping perts skew targets up — [[track-a-eda]]).
- **Myeloid-lineage cell lines** in Tahoe (if present) are the closest context
  to macrophages and should be weighted most heavily for any transfer.

## Limitations / open questions

- Perturbation modality mismatch (drugs, not gene knockdowns) for our genetic task.
- Cell-context mismatch (cancer lines vs primary macrophages).
- Scale (~100M cells) implies nontrivial compute/storage to leverage.
- **To verify:** does Tahoe's 50-line panel include myeloid/monocytic lines
  (THP-1, U937, HL-60, K562, …)? Check the `cell_line_metadata` config.
- **To test on our data:** are housekeeping-gene perturbation effects
  cell-type-invariant? (the transferability hypothesis above)
