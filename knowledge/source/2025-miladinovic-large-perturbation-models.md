---
source_url: https://doi.org/10.1038/s43588-025-00870-1
source_type: papers
title: "In silico biological discovery with large perturbation models"
author: Miladinovic et al. (GSK / Max Planck / ELLIS)
retrieved: 2026-07-16
doi: 10.1038/s43588-025-00870-1
---

# In silico biological discovery with large perturbation models

**Authors:** Djordje Miladinovic, Tobias Höppe, Mathieu Chevalley, Andreas Georgiou, Lachlan Stuart, Arash Mehrjou, Marcus Bantscheff, Bernhard Schölkopf, Patrick Schwab
**Year:** 2025
**Venue:** Nature Computational Science (preprint: bioRxiv 2024.10.29.620513)

## Abstract
The large perturbation model (LPM) is a deep-learning model that integrates
many heterogeneous perturbation screens by representing perturbation (P),
readout (R) and context (C) as three disentangled, symbolically-conditioned
dimensions. Rather than encoding observed expression, LPM is a decoder-only
model trained to predict an experiment's outcome from the symbolic (P, R, C)
tuple, letting it pool data across incompatible readouts (transcriptomics,
viability), perturbation types (CRISPRi/a, CRISPR-KO, chemical) and contexts
(single-cell, bulk) without requiring feature overlap. LPM beats existing
methods at predicting post-perturbation transcriptomes of unseen experiments,
links chemical and genetic perturbations by shared mechanism, and improves
gene–gene network inference.

## Key contributions
- **PRC-disentangled, encoder-free architecture:** perturbation, readout and
  context each become a learnable look-up embedding; a simple MLP over the
  concatenated embeddings predicts the scalar readout value Y.
- **Conditioning on readout R** is the key trick that lets one model absorb
  screens with non-overlapping and missing feature sets, instead of shrinking to
  the intersection of readouts across datasets.
- A single model serves multiple discovery tasks (effect prediction, mechanism
  identification, network inference) via transfer learning on its embeddings.
- End-to-end in-silico drug discovery case study for ADPKD, validated against
  real-world EHR data.

## Methods
LPM learns the causal model q(Y | do(P), R, C) by mapping discrete symbols
(e.g. `CRISPRi_STAT1`, `Transcript_PSMA1`) through learnable look-up tables to
embeddings Z_P, Z_R, Z_C, concatenated and fed to a ReLU MLP trained with Adam.
Multi-perturbations are handled by averaging component embeddings. Training data
pooled single-cell Perturb-seq (Replogle K562/RPE1, Norman CRISPRa) and bulk
LINCS L1000 (chemical + CRISPR-KO across ~26 contexts). Benchmarking used
leave-one-context-out cross-validation against CPA, GEARS, CatBoost+gene
embeddings (STRING/Reactome/Gene2Vec), Geneformer, scGPT, GenePT and a NoPerturb
control, scoring Pearson correlation of predicted vs. true expression change.

## Key results
- LPM **consistently and significantly outperformed** all baselines on
  post-perturbation expression prediction across 8 contexts, both perturbation
  types, and both preprocessing pipelines (one-sided Mann–Whitney, P ≤ 0.05).
- Its perturbation embeddings clustered matched compound–CRISPR pairs (e.g.
  statins near CRISPR-HMGCR) and achieved **higher recall of known target
  inhibitors** (N = 89 targets) than L1000-transcriptome embeddings.
- P-embeddings predicted gene-function annotations significantly better
  (P ≤ 0.01) than STRING, Reactome, Gene2Vec, Geneformer, scGPT and GenePT.
- LPM+Guanlab imputation significantly lowered false omission rate in gene–gene
  network inference vs. observed-data-only methods (N = 11 seeds).
- ADPKD case study: LPM predicted statins/triptolide upregulate PKD1; a
  retrospective Optum-EHR cohort found ≥1-yr simvastatin exposure cut ESRD
  progression (5-yr RR 0.86, P = 0.0405; 10-yr RR 0.74, P = 0.0003).
- Performance scales significantly with more perturbations and more contexts in
  training.

## Why it matters for our work
LPM is a strong reference architecture for perturbation-effect prediction
(Track A/B up/down/none). Its central lesson — treat perturbation, readout and
context as separate symbolic conditioning axes and condition on the readout so
heterogeneous screens can be pooled — is a cheap, encoder-free alternative to
transcriptome foundation models (Geneformer/scGPT), which it beats on both
effect prediction and gene-function recovery. That directly informs Track C
model selection and our gene-embedding strategy: learned perturbation embeddings
from pooled screens can outperform curated-database and LLM-derived gene
embeddings for functional tasks.

## Limitations / open questions
- **In-vocabulary only:** cannot extrapolate to unseen symbols (novel cell
  types/perturbations) without externally supplied pretrained embeddings — a
  hard limit for zero-shot generalization.
- Training data skew toward immortalized lines; primary/patient-derived samples
  underrepresented.
- Sensitive to hidden batch effects, inconsistent preprocessing, incomplete
  metadata.
- ADPKD result is retrospective (unobserved confounders); single marker only,
  no prospective validation.
- No extensive architecture search — MLP chosen for adequacy, not optimality.
