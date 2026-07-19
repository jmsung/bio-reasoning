---
source_url: https://www.nature.com/articles/s41592-023-02144-y
source_type: papers
title: "scPerturb: harmonized single-cell perturbation data"
author: Peidli, Green, Shen, et al.
retrieved: 2026-06-08
---

# scPerturb: harmonized single-cell perturbation data

**Authors:** S. Peidli, T. D. Green, C. Shen, et al.
**Year:** 2024
**Venue:** Nature Methods 21:531-540
Resource: https://scperturb.org

## Abstract

A harmonized collection of **44+ publicly available single-cell perturbation-
response datasets** (transcriptomics, proteomics, epigenomics) with uniform QC and
harmonized feature annotations. Introduces **E-statistics / E-distance** as a
general distance measure between sets of single-cell profiles for quantifying
perturbation effect size and significance.

## Key contributions

- One harmonized, consistently-formatted hub for dozens of perturbation datasets.
- **E-distance** metric for perturbation effect size + significance testing.
- Public software + data at scperturb.org.

## Methods

Uniform QC pipeline and feature-annotation harmonization across heterogeneous
datasets; energy-statistics for set-vs-set comparison of single-cell profiles.

## Key results

- Enables apples-to-apples comparison and integration across datasets.
- E-distance provides a principled way to rank/quantify perturbation strength.

## Why it matters for our work

⭐ **The efficient entry point.** Instead of hunting individual GEO accessions,
scPerturb gives many candidate datasets (incl. several we care about) in one
consistent format — ideal for the augmentation audit (roadmap #2). **E-distance**
is directly useful: e.g., to test whether housekeeping-perturbation effects are
more conserved across cell types ([[housekeeping-transfer-hypothesis]]).

## Limitations / open questions

- An aggregator — still must filter for relevant modality (genetic) / lineage
  (myeloid) / species (mouse) per dataset.
- Harmonization choices may smooth over dataset-specific quirks.
