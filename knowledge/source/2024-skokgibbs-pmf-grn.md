---
source_url: https://doi.org/10.1186/s13059-024-03226-6
source_type: papers
title: "PMF-GRN: a variational inference approach to single-cell gene regulatory network inference using probabilistic matrix factorization"
author: Skok Gibbs et al.
retrieved: 2026-07-16
doi: 10.1186/s13059-024-03226-6
---

# PMF-GRN: a variational inference approach to single-cell gene regulatory network inference using probabilistic matrix factorization

**Authors:** Claudia Skok Gibbs, Omar Mahmood, Richard Bonneau, Kyunghyun Cho
**Year:** 2024
**Venue:** Genome Biology, research article

## Abstract
Inferring gene regulatory networks (GRNs) from single-cell data is hampered by
heuristic model selection and a lack of uncertainty estimates. PMF-GRN
(Probabilistic Matrix Factorization for GRN inference) recasts GRN inference as
a probabilistic matrix factorization: single-cell expression is decomposed into
latent factors capturing transcription-factor activity (TFA) and TF–target-gene
regulatory interactions. Fitting the model with variational inference yields a
principled objective that supports hyperparameter search for model selection and
direct comparison to other generative models, and — because the model is
probabilistic — produces per-edge uncertainty estimates "for free." Benchmarked
on real (yeast, human PBMC) and synthetic (BEELINE) single-cell data, PMF-GRN
infers GRNs as accurately as or better than state-of-the-art methods while
offering well-calibrated uncertainty.

## Key contributions
- Reformulates single-cell GRN inference as probabilistic matrix factorization: observed expression W ≈ U·Vᵀ, with V = A⊙B (A = interaction existence, B = strength/direction), U = TFA.
- Decouples the generative model from the inference procedure, so new datasets/assumptions can be integrated without redesigning the algorithm — unlike regression methods (Inferelator, SCENIC, CellOracle) that couple the two.
- Uses variational inference with a coherent objective (validation AUPRC + importance-weighted marginal likelihood) for principled hyperparameter search and model selection instead of heuristic selection.
- Delivers per-edge posterior uncertainty; computational cost scales linearly in the number of cells.

## Methods
Prior-known TF–target interactions (from ATAC-seq + TF motifs or curated
databases) are encoded in the prior over the interaction-existence matrix A.
Hyperparameter selection holds out 20% of the prior network as validation:
inference runs on 80%, and validation AUPRC on the held-out entries is the
early-stopping and model-selection criterion. The configuration with the highest
validation AUPRC is then refit on the full prior, with an importance-weighted
estimate of the marginal log-likelihood as the early-stopping metric, giving the
final posterior over A. Predictions are evaluated by AUPRC against
database-derived gold standards ("keep-all-gold-standard" or "overlap" variants).
Calibration is assessed by cumulatively binning posterior means by their variance
and computing per-bin AUPRC.

## Key results
- On *S. cerevisiae*, PMF-GRN outperforms AMuSR, StARS, and SCENIC and is competitive with BBSR and CellOracle on consensus-network AUPRC; it beats BBSR when expression is not cleanly separated into tasks.
- Edge-consensus (IoU of top-25% edges): PMF-GRN 15.69% vs SCENIC 3.17%, StARS 11.78%, AMuSR 12.46%, BBSR 14.56%; CellOracle's higher 30.28% reflects its inability to predict edges outside the prior.
- Robust to noisy priors (AUPRC declines only slowly, matching CellOracle and beating BBSR/StARS/SCENIC), to expression downsampling (80/60/40/20%), and to cross-validation split size.
- Uncertainty is well-calibrated: AUPRC increases monotonically as posterior variance decreases; on human PBMCs, inferred TFA profiles cluster into 8 annotated cell types with literature-supported IRF-family edges; on all six BEELINE synthetic networks PMF-GRN beats the random baseline (weakest on "long linear").

## Why it matters for our work
For the BioReasoning Challenge, PMF-GRN is a concrete, uncertainty-aware way to
build the TF→target regulatory graph that underlies up/down/none directional
prediction (Tracks A/B). Its interaction-strength matrix B explicitly encodes
the *direction* (activation vs repression) of each edge — exactly the signal our
directional predictions need — and its calibrated per-edge uncertainty gives an
agent a principled confidence to gate abstention (relevant to our Track B
over-abstention failure). The variational, model/inference-decoupled design also
means priors from ATAC-seq or motif databases can be swapped in as features
without re-engineering, and posterior TFA estimates offer a latent regulatory
feature per cell type.

## Limitations / open questions
- Validated mainly on yeast, one PBMC dataset, and synthetic BEELINE data; direction (matrix B) is not yet benchmarked against ground-truth activation/repression.
- Underperforms on "long linear" trajectories, suggesting matrix factorization struggles with extended/high-dimensional regulatory cascades.
- Multi-task inference is handled by averaging separate posteriors rather than explicitly modeling multiple expression matrices and batch effects (flagged as future work); ATAC/motif prior information is not itself modeled probabilistically.
- Accuracy depends on gold-standard quality, which is incomplete for most organisms.
