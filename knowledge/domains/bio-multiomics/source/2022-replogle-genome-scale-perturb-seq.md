---
source_url: https://www.sciencedirect.com/science/article/pii/S0092867422005979
source_type: papers
title: "Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq"
author: Replogle et al. (senior: Weissman)
retrieved: 2026-06-08
---

# Mapping information-rich genotype-phenotype landscapes with genome-scale Perturb-seq

**Authors:** J. M. Replogle et al. (senior: J. S. Weissman)
**Year:** 2022
**Venue:** Cell 185:2559-2575 (DOI 10.1016/j.cell.2022.05.013)
Data portal: https://gwps.wi.mit.edu/

## Abstract

The first genome-scale Perturb-seq screens: a compact multiplexed **CRISPRi**
library assays thousands of loss-of-function perturbations with scRNA-seq. K562
genome-wide screen (~9,866 expressed genes) plus K562-essential (~2,057 genes)
and RPE1-essential screens. Yields an information-rich genotype-phenotype map of
gene function, regulatory relationships, and cell states.

## Key contributions

- Genome-scale CRISPRi Perturb-seq: ~2.5M cells, ~9,866 genes targeted (K562 GW).
- Same essential-gene perturbations profiled in **two cell types (K562 + RPE1)**.
- Demonstrates clustering of perturbations into pathways/complexes from
  transcriptional phenotypes alone.

## Methods

dCas9-KRAB (CRISPRi) knockdown with expressed guide barcodes; pooled screen read
out by scRNA-seq; per-perturbation pseudobulk profiles used for downstream maps.

## Key results

- Recovers known and novel gene-function relationships at genome scale.
- Pseudobulk per-perturbation signatures are the workhorse representation.

## Why it matters for our work

⭐ **Top augmentation candidate.** Same modality as the challenge (**CRISPRi
knockdown**), and K562 is a **myeloid** (CML) line — closer to macrophages than
most ([[housekeeping-transfer-hypothesis]]). Genome-wide coverage means many
perturbations overlap ours by ortholog. **Critically, it ran the same essential
perturbations in K562 AND RPE1** → a ready-made test of whether housekeeping-gene
perturbations are cell-type-invariant. Connects to our GO findings ([[track-a-eda]]).

## Limitations / open questions

- **Human** (K562/RPE1) vs our **mouse** macrophages → needs ortholog mapping.
- Full single-cell matrices are large (~tens of GB); pseudobulk is small — see
  compute notes.
- CRISPRi essential-gene focus skews toward strong-effect (often housekeeping)
  perturbations.
