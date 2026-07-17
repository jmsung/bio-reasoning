---
source_url: https://doi.org/10.1101/gr.259655.119
source_type: papers
title: "Dual threshold optimization and network inference reveal convergent evidence from TF binding locations and TF perturbation responses"
author: Kang et al.
retrieved: 2026-07-16
doi: 10.1101/gr.259655.119
---

# Dual threshold optimization and network inference reveal convergent evidence from TF binding locations and TF perturbation responses

**Authors:** Yiming Kang, Nikhil R. Patel, Christian Shively, Pamela Samantha Recio, Xuhua Chen, Bernd J. Wranik, Griffin Kim, R. Scott McIsaac, Robi Mitra, Michael R. Brent
**Year:** 2020
**Venue:** Genome Research (2020), doi:10.1101/gr.259655.119

## Abstract

A high-confidence map of each transcription factor's (TF) direct functional
targets needs convergent evidence from independent sources — principally TF
binding locations (ChIP) and transcriptional responses to TF perturbation.
Systematic data of both types exist for yeast and human, yet they rarely agree
on a common target set: when there are many nonfunctional binding sites and many
indirect targets, bound-and-responsive overlaps arise largely by chance. The
paper introduces **dual threshold optimization (DTO)**, a method that sets the
significance thresholds on binding and response data jointly to maximize the
significance of their overlap, and shows that DTO — especially combined with
network inference — greatly expands the high-confidence TF network in both yeast
and human.

## Key contributions

- **DTO**: for each TF, choose the (binding, response) rank-threshold pair that
  minimizes the hypergeometric p-value of the bound∩responsive overlap; a
  permutation null (1000 randomizations) tests significance.
- Enables comparing raw binding data against perturbation data **processed by
  network-inference algorithms** (NetProphet, Inferelator, GENIE3, MERLIN) that
  use no binding information — preserving independence of evidence.
- Introduces the **ZEV** rapid-induction perturbation data (15-min post-induction
  responses enriched for direct targets) and a new yeast **transposon calling
  cards** binding data set, compared to ChIP-exo and ChIP-chip.
- "Acceptable convergence" criterion: overlap significant (permutation p < 0.01)
  AND 80% sensitivity at ≤20% expected FDR theoretically achievable.

## Methods

Genes are ranked by binding signal (−log ChIP p-value) and by response strength
(|log fold change| or a network-inference score). DTO scans threshold pairs to
minimize the overlap's hypergeometric p-value, constrained so the binding p-value
stays ≤0.1 (and, in human, capping responsive-gene counts to avoid degenerate
"all genes responsive" thresholds). Yeast analysis compares Harbison ChIP-chip,
Venters ChIP, ChIP-exo, and calling cards against TFKO (knockout) and ZEV
(induced-overexpression) responses; human analysis compares ENCODE K562 ChIP-seq
against TFKD and CRISPRi+CRISPR-KO, plus HEK293 zinc-finger overexpression.

## Key results

- Baseline is poor: median response rate of bound genes is 18% in yeast; 26 of 97
  TFs had bound and responsive targets but zero overlap. Simple intersection gave
  only 27 acceptable TFs — ~85% of TFs had no high-confidence targets.
- DTO on TFKO+ZEV → **60 acceptable TFs** (2074 interactions, 1430 target genes).
- Adding NetProphet network inference → **84 acceptable TFs (46%)** in yeast.
- ChIP-exo and calling cards beat ChIP-chip; NetProphet-processed ZEV vs. ChIP-exo
  or calling cards gave **all** overlapping TFs acceptable convergence.
- Human: DTO + NetProphet 2.0 raised acceptable TFs from 3→71 (HEK293), 6→17
  (K562 TFKD). Combining all yeast data → 96 acceptable TFs, 3268 edges, 1686 genes.

## Why it matters for our work

The BioReasoning Challenge Tracks A/B ask whether a perturbed gene goes up, down,
or unchanged — a direct-vs-indirect target problem. This paper is a rigorous prior
on why binding≠regulation and why perturbation-response signal (especially early
timepoints) is the sharper evidence for *functional* targets. DTO's core insight —
jointly thresholding two noisy evidence sources to maximize overlap significance,
with a permutation null — is a reusable pattern for fusing binding priors with
expression response when predicting regulatory direction, and its yeast/human
gold-standard networks are candidate evaluation references.

## Limitations / open questions

- "Acceptable convergence" is a lower-bound FDR screen, not a guarantee that most
  bound-responsive genes are direct targets; it can even hold between one TF's
  bound set and another TF's responsive set (non-unique).
- Human convergence remained low even after DTO (median bound-gene response rate
  <0.5%), reflecting far more bound than responsive genes.
- Newer ChIP is not always better: 2011 Venters ChIP did not beat older Harbison
  data — data-set quality matters more than recency.
- Coverage is limited by overlapping assays (e.g. only 12 TFs had calling cards +
  ZEV + TFKO), so the "complete" network remains partial.
