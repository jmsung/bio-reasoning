---
source_url: https://doi.org/10.1101/2024.05.24.595391
source_type: papers
title: "Genome-wide nucleosome and transcription factor responses to genetic perturbations reveal chromatin-mediated mechanisms of transcriptional regulation"
author: Kevin Moyung et al.
retrieved: 2026-07-16
doi: 10.1101/2024.05.24.595391
---

# Genome-wide nucleosome and transcription factor responses to genetic perturbations reveal chromatin-mediated mechanisms of transcriptional regulation

**Authors:** Kevin Moyung, Yulong Li, Alexander J. Hartemink, David M. MacAlpine
**Year:** 2024
**Venue:** bioRxiv preprint (2024), doi:10.1101/2024.05.24.595391 (PMC11142231, PMID 38826400)

## Abstract
Most perturbation-response studies measure gene expression, leaving the chromatin-level
regulatory code largely unexplored. This work uses a factor-agnostic reverse-genetics
approach: MNase-seq profiles genome-wide transcription factor (TF) and nucleosome
occupancy simultaneously, at near-nucleotide resolution, after the individual deletion of
201 transcriptional regulators in *Saccharomyces cerevisiae* — assaying nearly one million
mutant-gene interactions. The authors quantify chromatin changes genome-wide, find that
they recapitulate known expression pathways, identify distinct chromatin signatures of up-
vs. down-regulation, show chromatin features are predictive of transcriptional activity,
and reconstruct transcriptional regulatory networks (TRNs) from chromatin data alone.

## Key contributions
- A single MNase-seq assay that captures **TF and nucleosome occupancy together** at high
  resolution across 201 knockouts (~1M mutant-gene interactions) in yeast.
- A **Jensen-Shannon (JS) divergence** metric to quantify genome-wide chromatin change from
  the 2D distribution of reads (generalizes to ATAC-/ChIP-seq).
- **Direction-specific chromatin signatures**: activator loss → TF loss + nucleosome gain +
  down-regulation; repressor loss → the opposite.
- An interpretable **regression predictor** of expression change from chromatin features,
  and **chromatin-only TRN reconstruction** that recovers (and extends) expression TRNs.

## Methods
For each gene, nucleosome occupancy change is the log2 fold-change in nucleosome-sized
fragments (140-200 bp) over the +1/+2/+3 nucleosomes downstream of the TSS and 250 bp
upstream (promoter), between control and mutant. TF occupancy, promoter nucleosome
occupancy, gene-body nucleosome occupancy, PAS nucleosome occupancy, and nucleosome
disorganization are computed per interaction. Overall chromatin change is summarized with
JS divergence. Expression is predicted by ordinary-least-squares regression on five
chromatin features plus NET-seq transcription rate. TRN edges are drawn for significant
mutant-gene pairs, colored by predicted up/down-regulation, and classified direct (TF
occupancy log2FC < -0.5 with an annotated binding site in the target promoter) vs. indirect.

## Key results
- Promoter TF occupancy change correlates with expression change (R = 0.43, p < 2.2e-16);
  gene-body/promoter nucleosome occupancy correlates negatively (R = -0.23, R = -0.13);
  nucleosome disorganization positively (R = 0.2); PAS nucleosome occupancy R = -0.38.
- The combined OLS model (5 chromatin features + NET-seq rate) predicts expression
  fold-change well across all significant interactions (**R = 0.62, p < 2.2e-16**).
- Chromatin-only TRNs recapitulate most expression-based edges; *sir1Δ, pdr8Δ, lys14Δ,
  dal80Δ* had **100% of targets recovered**, and the *bas1Δ* chromatin TRN revealed two
  extra targets (GCV2, HIS5) missed by expression due to low differential expression.
- Identifies pioneer-TF candidates (Htl1, Ace2, Bas1, Cbf1, Sub1); deleting the pioneer TF
  drops target expression by ≥2-fold (log2FC < -1).

## Why it matters for our work
The BioReasoning Challenge Tracks A/B ask models to predict the **direction** (up/down/none)
of a gene's response to a perturbation. This paper is direct evidence that mechanistic
chromatin state — not just expression — carries a clean directional signal: TF-loss +
nucleosome-gain predicts down-regulation and the reverse predicts up-regulation, and a
simple interpretable model reaches R = 0.62. It suggests chromatin/occupancy features (or
priors encoding "activator vs. repressor" and pioneer status) as inputs or reasoning scaffolds
for direction prediction, and its chromatin-based TRN reconstruction is a template for
gene-regulation strategy where expression-only networks conflate direct and indirect effects.

## Limitations / open questions
- Yeast single-gene deletions only; transfer to mammalian / multi-perturbation settings is
  untested.
- Chromatin and expression changes are not perfectly correlated — some genes change
  expression with no chromatin change (and vice versa), so signatures are probabilistic.
- The regression is correlational; it cannot resolve whether chromatin change drives
  transcription or follows it.
- Requires high-resolution MNase-seq occupancy data, which is not available for most systems.
