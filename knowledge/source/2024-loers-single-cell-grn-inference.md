---
source_url: https://doi.org/10.1093/bib/bbae382
source_type: papers
title: "A single-cell multimodal view on gene regulatory network inference from transcriptomics and chromatin accessibility data"
author: Loers & Vermeirssen
retrieved: 2026-07-16
doi: 10.1093/bib/bbae382
---

# A single-cell multimodal view on gene regulatory network inference from transcriptomics and chromatin accessibility data

**Authors:** Jens Uwe Loers, Vanessa Vermeirssen
**Year:** 2024
**Venue:** Briefings in Bioinformatics (Oxford), review article

## Abstract
This review surveys how gene regulatory network (GRN) inference is advanced by
integrating single-cell transcriptomics (scRNA-seq) and chromatin accessibility
(scATAC-seq). The central object is the enhancer GRN (eGRN): a directed graph
of transcription factors (TFs), regulatory elements (REs), and target genes (TGs)
with TF→RE→TG triple relationships, going beyond mere TF–TG expression correlation.
The authors dissect the shared components of state-of-the-art (e)GRN inference
pipelines — preprocessing, metacell/pseudobulk aggregation, computational omics
pairing, TF binding-site detection, linear vs 3D RE–TG linkage, and dynamic/causal
modeling — and argue that single-cell multimodal integration is now the standard
for mechanistic network inference.

## Key contributions
- Decomposes (e)GRN inference into a common pipeline (TF-RE, RE-TG, TF-TG steps) and maps state-of-the-art tools onto it.
- Catalogs and contrasts >30 methods across four modeling families: correlation, regression, probabilistic, deep learning.
- Frames three future priorities: quantitative modeling, causality, and richer multimodal integration.

## Methods
The review classifies methods by input coupling — paired same-cell multiome
(TRIPOD, scREG), independent same-sample cells (GRANIE, ANANSE), or algorithmically
coupled metacells (SCENIC+, FigR, Pando). It walks through sparsity mitigation
via pseudobulking and metacells (SEACells, Cicero), computational pairing of
unpaired modalities (SIMBA, DIRECT-NET, GLUE's variational-autoencoder guidance
graph), TFBS detection by PWM scanning (FIMO, HOMER, gimmemotifs) and footprinting
(TOBIAS, Dictys), and RE–TG linkage by genomic distance cutoffs (±100–250 kb) or
3D contacts (Hi-C, ChIA-PET). TF-RE-TG networks are built either transitively via
a shared RE node (SCENIC+, GRANIE) or in an integrated three-way model (TRIPOD,
Pando, LINGER). Dynamic eGRNs use pseudotime (IReNA, Dictys) or in-silico TF
perturbation propagated through the network (CellOracle, SCENIC+).

## Key results
- Expression-only GRN inference performs poorly — low AUPR across benchmarks, and methods often struggle to beat random predictors; adding chromatin accessibility and prior knowledge measurably improves reverse engineering.
- scATAC-seq is extremely sparse (only ~1–10% of peaks called per cell), forcing metacell/pseudobulk aggregation that trades single-cell resolution for count depth.
- SCENIC+ demonstrates the scale now possible: a collection of 1553 human TFs with characterized binding sites.
- RE–TG inference remains dominated by linear regression, with little modeling of sparsity or nonlinearity; distance thresholds strongly shape the network and miss long-range enhancers (e.g. an 850 kb limb-development RE in mouse).

## Why it matters for our work
For the BioReasoning Challenge, this review is the mechanistic backbone for
reasoning about *why* a gene goes up/down/none (Tracks A/B). It supplies the
vocabulary and causal structure — TF→RE→TG regulons, cistromes, eRegulons — that
an agent can use to justify directional predictions from a TF perturbation, and it
names the concrete tools (SCENIC+, CellOracle, GLUE, Pando) whose inferred networks
or in-silico perturbation logic could seed features or priors. The emphasis on
causality over correlation directly matches our need to predict *direction* of
regulatory effect rather than mere co-expression.

## Limitations / open questions
- It is a review, not a benchmark — no head-to-head performance numbers or a recommended single method.
- Ground-truth incompleteness and low AUPR mean inferred networks carry many false positives; individual edges still need experimental validation.
- 3D chromatin, TF footprinting, and paired multiome data are often unavailable for the same sample, and time-series/dynamic modeling remains supported by only a few tools.
