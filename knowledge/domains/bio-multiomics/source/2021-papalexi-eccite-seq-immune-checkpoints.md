---
source_url: https://pmc.ncbi.nlm.nih.gov/articles/PMC8011839/
source_type: papers
title: "Characterizing the molecular regulation of inhibitory immune checkpoints with multi-modal single-cell screens (ECCITE-seq, THP-1)"
author: Papalexi et al. (senior: Satija)
retrieved: 2026-06-08
---

# Characterizing the molecular regulation of inhibitory immune checkpoints with multi-modal single-cell screens

**Authors:** E. Papalexi et al. (senior: R. Satija)
**Year:** 2021
**Venue:** Nature Genetics 53:322-331

## Abstract

Uses **ECCITE-seq** (CRISPR screen + scRNA-seq + surface-protein readout) in
**THP-1** cells to dissect the regulatory networks controlling inhibitory immune
checkpoints, notably **PD-L1**. Introduces **mixscape**, a computational method
that removes confounding variation and identifies cells that escaped perturbation,
sharpening single-cell CRISPR signal.

## Key contributions

- Multi-modal CRISPR screen (RNA + protein) in a myeloid context.
- **mixscape** method for denoising single-cell perturbation screens.
- Maps regulators of PD-L1 / immune-checkpoint expression.

## Methods

CRISPR perturbation with guide capture; joint mRNA + antibody-derived-tag
readout; mixscape classifies perturbed vs escaping cells before downstream analysis.

## Key results

- Identifies known and novel regulators of immune-checkpoint expression.
- mixscape substantially improves signal-to-noise vs naive analysis.

## Why it matters for our work

⭐ **Closest cell-type match.** **THP-1 is a monocyte/macrophage model** — the
nearest common line to our macrophage challenge. Genetic CRISPR perturbation with
an immune/innate focus. The **mixscape** denoising idea is also relevant if we
ever touch raw single-cell data.

## Limitations / open questions

- **Human** THP-1 vs our **mouse** macrophages → ortholog mapping.
- Smaller perturbation set than genome-scale screens.
- Cancer-derived (leukemia) line, not primary macrophages.
