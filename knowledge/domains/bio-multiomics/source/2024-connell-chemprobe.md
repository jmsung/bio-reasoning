---
source_url: https://doi.org/10.1038/s42003-024-06865-4
source_type: papers
title: "Learning chemical sensitivity reveals mechanisms of cellular response"
author: William Connell et al.
retrieved: 2026-07-16
doi: 10.1038/s42003-024-06865-4
---

# Learning chemical sensitivity reveals mechanisms of cellular response

**Authors:** William Connell, Kristle Garcia, Hani Goodarzi, Michael J. Keiser
**Year:** 2024
**Venue:** Communications Biology

## Abstract
ChemProbe is a deep neural network that predicts cellular sensitivity to hundreds of molecular probes and drugs by learning to combine basal transcriptomes with chemical structure. Trained on ~5.8 million cell line–compound–concentration examples, it infers chemical sensitivity of cancer cell lines and tumor samples, is retrospectively evaluated for precision breast cancer treatment (I-SPY2), and prospectively validated in new cellular models including a genetically modified line. Integrated-gradient interpretation surfaces transcriptome features reflecting compound targets and protein-network modules, including genes driving ferroptosis. The result is an interpretable in silico screening tool for measuring cellular response to diverse compounds.

## Key contributions
- A **conditional neural network** that predicts cell viability `y = f(x | n)`, where transcriptome `x` is modulated by chemical features `n` via learned linear (FiLM-style scale/shift) transformations rather than plain concatenation.
- A large training corpus: CTRP drug-response × CCLE transcriptomes → 545 compounds/pairs, 860 cell lines, ~5.85M labeled concentration-level examples.
- **Differential attribution analysis (DAA)**: an integrated-gradient + cell-line-effect correction method that yields ranked gene lists tied to compound mechanism of action.

## Methods
Compounds are encoded as 512-bit Morgan fingerprints (radius 2) plus micromolar concentration (513-length vector); cells as 19,144 protein-coding gene expression values. The network learns a gene-expression embedding conditioned by parameters from the compound embedding (scale γ, shift β), implemented in PyTorch with Optuna hyperparameter search. Evaluation uses 5-fold cross-validation **stratified by cell line** to avoid leakage. Predictions are fit with log-logistic dose-response curves to derive IC50s. Interpretation uses integrated-gradient saliency with soundness checks (random-init and label-permuted control models) and cell-line normalization to decouple attributions from raw expression magnitude.

## Key results
- Conditioning beats concatenation: R² = 0.607 (concat) vs 0.706 (shift), 0.711 (scale), 0.709 (FiLM); structural ablation collapses to 0.302.
- Retrospective I-SPY2: predicted lower sensitivity for responders in 4/5 drugs; per-drug auROC 0.60–0.73, macro-average 0.65; ChemProbe +/− classification significantly beat I-SPY2 (p < 5e-2), cutting false-positive rate from 0.70 to 0.37.
- Prospective: predicted HCC1806-Par more sensitive than MDA-MB-231-Par for 88.16% (201/228) of compounds; all 6 selected compounds confirmed in vitro; predicted vs observed IC50 differences correlated (p = 0.035).
- Interpretation recovered ferroptosis biology: GPX4, SCD, SLC7A11, FSP1, LRP8 among top-attributed genes; correctly predicted LRP8-KO cells more sensitive to ferroptosis inducers (ML210, RSL-3, ML162, CIL56).

## Why it matters for our work
ChemProbe is a direct template for the BioReasoning Challenge's perturbation-response task: it predicts a **directional cellular response** (viability up/down) from a basal transcriptome conditioned on a perturbation, exactly the up/down/none framing of Tracks A/B. Two lessons transfer: (1) cross-validation **stratified by cell line** is essential to avoid inflated CV — echoing our own Track B lesson that small/leaky CV misleads; (2) conditioning gene expression on the perturbation (scale/shift/FiLM) beats naive concatenation, a useful architectural prior for any perturbation-prediction model. The DAA interpretation method also offers a route to biologically-grounded gene-regulation reasoning that judges could probe.

## Limitations / open questions
- Trained only on cancer cell lines / bulk transcriptomes; I-SPY2 microarray inputs were partly out-of-distribution and required mean-imputation of ~10% of genes.
- Raw integrated-gradient attributions correlate with expression magnitude and fail soundness tests until cell-line-corrected — interpretation is fragile.
- Predicts viability from a chemical fingerprint + concentration; does not model nonlinear gene-regulatory network interactions or genetic perturbations natively.
- auROC on the clinical retrospective (0.65 macro) is modest; clinical utility comes mainly from reduced false positives, not high sensitivity.
