---
source_url: https://doi.org/10.1038/s41592-019-0690-6
source_type: papers
title: "Benchmarking algorithms for gene regulatory network inference from single-cell transcriptomic data"
author: Pratapa et al.
retrieved: 2026-07-16
doi: 10.1038/s41592-019-0690-6
---

# Benchmarking algorithms for gene regulatory network inference from single-cell transcriptomic data

**Authors:** Aditya Pratapa, Amogh P. Jalihal, Jeffrey N. Law, Aditya Bharadwaj, T. M. Murali (Virginia Tech)
**Year:** 2019
**Venue:** Nature Methods (2019), doi:10.1038/s41592-019-0690-6

## Abstract
BEELINE is a systematic evaluation of 12 state-of-the-art algorithms for inferring gene regulatory
networks (GRNs) from single-cell transcriptomic data. Ground truth comes from three sources:
synthetic networks with predictable trajectories, six literature-curated Boolean models, and
experimental scRNA-seq datasets compared against curated regulatory databases. The authors
introduce BoolODE, a simulator that turns synthetic and Boolean networks into single-cell
expression while avoiding pitfalls of earlier simulation methods. The headline finding is sobering:
AUPRC and early precision of all methods are only moderate, methods do better on synthetic than on
curated Boolean networks, and techniques that do *not* require pseudotime-ordered cells are
generally more accurate.

## Key contributions
- **BEELINE**, a reproducible Dockerized framework wrapping 12 GRN inference algorithms (each in R/MATLAB/Python/Julia/F#) behind a uniform pre-process → infer → evaluate pipeline.
- **BoolODE**, a principled SDE-based simulator that converts Boolean/synthetic networks into single-cell data preserving the correct number and identity of steady states.
- Three-tier ground truth: 6 synthetic networks, 4 curated Boolean models (mCAD, VSC, HSC, GSD), and 5 experimental scRNA-seq datasets (mouse + human) vs. ChIP-seq / STRING networks.
- Multi-axis evaluation: accuracy (AUPRC ratio, early precision ratio EPR), stability (across datasets, runs, dropouts, pseudotime), and scalability (time/memory).

## Methods
Algorithms were run on 50 simulated datasets per synthetic network and 120 datasets across the four
Boolean models (10 datasets × 2,000 cells, with dropout rates q=50 and q=70). Pseudotime was
inferred with Slingshot to mimic a real pipeline; six methods needed a per-dataset parameter sweep
tuned for best median AUPRC. Accuracy was measured as AUPRC ratio (AUPRC over a random predictor)
and EPR on top-k predictions; stability via Jaccard index of top-ranked edges and pseudotime
shuffling over 15/30/45% windows.

## Key results
- On synthetic networks methods were best on the Linear network (10/12 had AUPRC ratio > 2.0); the Trifurcating network was hardest (no algorithm reached AUPRC ratio ≥ 2.0). SINCERITIES led on 4 of 6 synthetic networks.
- The top synthetic performers (SINCERITIES, SCRIBE, SINGE) collapsed to near-random on curated Boolean models — they are highly sensitive to pseudotime accuracy (performance dropped most under shuffling).
- **GENIE3, GRNBoost2, and PIDC** were the most consistent: highest EPR on both curated models and experimental datasets. PIDC is notably the only single-cell method not requiring pseudotime ordering.
- Overall accuracy was modest: for curated models, in 29 cases with median EPR ≥ 1, EPR was ≥ 1.5 only 16 times. Ensembling algorithm outputs did *not* beat the single best method — contrary to bulk-GRN experience.
- Including all significantly-varying TFs significantly improved EPR, but adding more highly-varying genes (500 → 1,000) did not.

## Why it matters for our work
GRN inference is directly relevant to the BioReasoning Challenge's gene-regulation reasoning:
Track A/B ask whether a perturbed gene drives another up, down, or not at all — a signed,
directed regulatory-edge question. BEELINE is a cautionary baseline: purpose-built single-cell
GRN methods achieve only moderate accuracy and are fragile to pseudotime quality, so we should not
over-trust inferred network priors as ground truth. Its concrete recommendations — prefer
pseudotime-free methods (PIDC), favor consistently robust learners (GENIE3, GRNBoost2), include all
varying TFs, and distrust ensembles — are useful defaults if we build or consume regulatory-graph
features. It also supplies curated Boolean ground-truth networks that could seed evaluation of an
agent's regulatory-direction predictions.

## Limitations / open questions
- Only 12 algorithms circa 2019; excludes deep-learning / foundation-model approaches now central to Track C.
- Simulated data (BoolODE) may not capture all real scRNA-seq noise despite explicit dropout modeling.
- Ground-truth regulatory databases (ChIP-seq, STRING) are themselves incomplete and cell-type-agnostic, capping measurable precision.
- Best methods still only moderately accurate — leaves open whether richer priors or LLM reasoning can push single-cell GRN inference substantially higher.
