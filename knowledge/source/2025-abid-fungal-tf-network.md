---
source_url: https://doi.org/10.1101/2025.05.10.653149
source_type: papers
title: "Mapping the transcriptional regulatory network of a fungal pathogen by exploiting transcription factor perturbation"
author: Dhoha Abid et al.
retrieved: 2026-07-16
doi: 10.1101/2025.05.10.653149
---

# Mapping the transcriptional regulatory network of a fungal pathogen by exploiting transcription factor perturbation

**Authors:** Dhoha Abid, Holly Brown, Chase Mateusiak, Tamara L. Doering, Michael R. Brent
**Year:** 2025
**Venue:** bioRxiv (2025), doi:10.1101/2025.05.10.653149 (PMC12132429; PMID 40463179)

## Abstract

The authors build a genome-scale transcription-factor (TF) regulatory network for
*Cryptococcus neoformans*, a deadly fungal pathogen whose virulence depends on a
transcriptionally regulated polysaccharide capsule. They RNA-seq 120 single-TF-deletion
strains (plus wild-type controls) under capsule-inducing conditions, then apply
NetProphet3 to predict each TF's direct, functional targets from expression alone.
The resulting map is validated against physical binding (ChIP-seq) and GO functional
coherence. Two headline findings: (1) no TF primarily regulates capsule genes — capsule
regulators are broad, high-impact hubs that also control many other processes; (2)
comparing the map to a NetProphet3 *S. cerevisiae* network reveals functionally
orthologous TF pairs that sequence homology alone misses.

## Key contributions

- A **comprehensive TF-perturbation RNA-seq resource** for *C. neoformans*: 120 TF-deletion
  strains, avg ~4 replicates each, 122 WT samples; 6,746 genes detected including 163 of
  165 TFs (GEO GSE297962).
- A validated genome-scale **direct-functional TF network map** (16,300 top edges over 163
  TFs; browsable at cryptococcus.net; Zenodo 10.5281/zenodo.17193243), built with
  NetProphet3 in **cross-trained mode** — trained on *S. cerevisiae* binding+expression,
  applied to *Cryptococcus* expression with no local binding data.
- Evidence that **network-based functional orthology** finds TF ortholog pairs across a
  ~400-My divergence that BLASTP sequence homology alone does not.

## Methods

Strains were grown in YPD then shifted 90 min to capsule-inducing conditions (DMEM, 37 °C,
5% CO₂). DESeq2 gave log2 fold changes (deletion vs. all 122 WT). NetProphet3 combines a
differential-expression feature with LASSO and BART regression features (predicting each
gene's expression from all TFs), outputting a per-edge probability that the TF directly
binds and regulates the target. It was cross-trained on *S. cerevisiae*, with a separate
integration mode for the 10 *Cryptococcus* TFs that had ChIP-seq. Validation used a binding
metric (fraction of top edges with ChIP-seq support) and a GO-biological-process coherence
metric versus permuted random networks; cross-species orthology combined BLASTP with a
permutation-based Jaccard target-overlap P-value into a sequence-functional (SF) score.

## Key results

- For the most stringent network, **>50% of predicted edges had ChIP-seq binding support
  vs. ~4% random** expectation; NetProphet3 substantially **outperformed Genie3 and
  Inferelator3** on binding support, and matched them on GO coherence (better at
  intermediate network sizes). Predicted scores were well-calibrated to observed ChIP-seq
  validation rates, if anything slightly pessimistic.
- The network is highly **hub-dominated**: the top 16 TFs (10%) cover 41% of edges and
  regulate 81% of the 4,103 regulated genes. 10 of those 16, and 8 of 14 "hub" TFs, are
  capsule-implicated (hypergeometric p = 0.006 and 0.007).
- **No capsule-specific TF exists** — even major regulators (Gat201, Cir1, Nrg1) have only
  4–5% capsule-implicated targets (max any TF: 36%).
- Cross-species: of 63 sequence-homology TF pairs, only 3 had significant target overlap;
  the authors instead identified **17 sequence+function ortholog pairs**, 9 of which
  sequence homology alone had missed. Of 165 TFs, 93 have no *S. cerevisiae* ortholog by
  either method, and 29 of those regulate targets enriched for genes lacking yeast homologs.

## Why it matters for our work

This paper is a clean, mechanistic demonstration that **signed, direct TF→target regulation
can be recovered from perturbation expression data alone** — the exact up/down/none signal
BioReasoning Track A/B must predict. NetProphet3's recipe (DE + LASSO + BART features, then
ML calibrated to binding) is a concrete, non-foundation-model baseline for perturbation-to-
target inference, and its **cross-species transfer** (train on yeast, predict in
*Cryptococcus* with zero local labels) is directly relevant to our low-signal / zero-shot
regimes where our agentic Track B over-abstained. The finding that regulation is hub-
dominated and that sequence homology misleads on function is a useful prior when reasoning
about which perturbations propagate widely versus narrowly.

## Limitations / open questions

- Bulk RNA-seq under one condition/time point (90 min, capsule-inducing) — no single-cell,
  no cell-type context, no combinatorial perturbations.
- Only 120 of 165 TFs were deletable; the other 45 (some essential) get predictions from
  non-DE features only, so their edges are weaker.
- Cross-trained on *S. cerevisiae* and validated against binding for just 10 TFs (3,308
  edges); GO annotations were largely transferred from yeast by sequence homology, which
  partly couples the functional-coherence metric to the same homology it critiques.
- A network map, not a dynamical/causal model — edges are confidence-scored functional
  targets, not quantitative regulatory strengths.
