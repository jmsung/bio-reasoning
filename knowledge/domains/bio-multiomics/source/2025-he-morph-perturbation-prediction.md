---
source_url: https://doi.org/10.1101/2025.06.27.661992
source_type: papers
title: "MORPH Predicts the Single-Cell Outcome of Genetic Perturbations Across Conditions and Data Modalities"
author: Chujun He et al.
retrieved: 2026-07-16
doi: 10.1101/2025.06.27.661992
---

# MORPH Predicts the Single-Cell Outcome of Genetic Perturbations Across Conditions and Data Modalities

**Authors:** Chujun He, Jiaqi Zhang, Munther Dahleh, Caroline Uhler (Broad Institute / MIT)
**Year:** 2025
**Venue:** bioRxiv (preprint), doi:10.1101/2025.06.27.661992

## Abstract
MORPH (MOdular framework for predicting Responses to Perturbational cHanges) predicts the single-cell distribution of cellular responses to genetic perturbations. It couples a discrepancy-based conditional variational autoencoder with a cross-attention mechanism, taking a control cell plus a prior-knowledge embedding of the perturbed gene and predicting the perturbed-cell distribution. Its modular design handles both single-cell transcriptomics (Perturb-seq) and imaging read-outs, and it generalizes to unseen perturbations, unseen combinations, and perturbations in new cell contexts. The attention weights are interpretable, yielding gene interaction and regulatory-network inference, while learned gene embeddings guide the design of informative perturbation experiments.

## Key contributions
- A modality-agnostic VAE + cross-attention model predicting the full *distribution* of single-cell perturbation responses, not just the mean, from *unpaired* control/perturbed data.
- Encodes perturbations via biological prior-knowledge embeddings (control expression, Geneformer, GenePT, DepMap) rather than one-hot IDs, enabling zero-shot generalization to unseen genes.
- A causally-grounded attention framework (with identifiability guarantees) that reconstructs a bipartite perturbation-module -> gene-program regulatory network.
- An active-learning / lab-in-the-loop acquisition scheme using learned representations to select the most informative perturbations to screen next.

## Methods
A control cell X_0 and a gene embedding v_g are passed through separate MLP encoders into latent space; a cross-attention block queries a learned, cell-type-shared gene-program matrix (keys/values) before an MLP decoder emits the predicted perturbed cell. Training uses a variational lower bound plus a maximum mean discrepancy (MMD) between predicted and true perturbed-cell distributions, sidestepping the need for paired data. Cross-cell-line transfer is done by fine-tuning only on control cells of the new line. Evaluated with MMD, RMSE, and Pearson correlation over the top-50 DE genes, on standard 5-fold and a harder "outlier distribution" split.

## Key results
- On three Replogle et al. Perturb-seq screens (K562 essential, RPE1 essential, genome-wide K562), MORPH beat GEARS and a linear model across MMD, RMSE, and Pearson, including the outlier split. DepMap embeddings were consistently the best prior.
- Cross-line transfer: trained on RPE1 then fine-tuned on K562 controls reached the accuracy of training on ~1,500 K562 perturbations using only ~7% (100) of them; prediction loss correlated with cell-line pathway disagreement (Pearson 0.52, p<0.05).
- Combinatorial (Norman et al. double perturbations): improved MMD by 33% and RMSE by 22% over SOTA; ~40% better on redundant gene-interaction types; highest AUC-ROC for classifying interaction types.
- Imaging (optical pooled Ebola screen, ~5.2M HeLa cells, 20,336 genes, ViT features): outperformed baselines by 33% at identifying top infection-state-altering perturbations.
- Recovered the true bipartite regulatory network on simulated data, capturing positive and negative regulation.

## Why it matters for our work
Directly relevant to Track A/B perturbation-outcome prediction. MORPH frames the task as predicting the full single-cell response distribution to an unseen perturbation, and its finding that the *choice of gene prior* dominates accuracy (DepMap functional embeddings > Geneformer > GenePT language embeddings) is actionable for how we build gene representations for up/down/none direction calls. Its zero-shot generalization via biological embeddings, cross-context transfer with minimal target data, and interpretable attention-based gene-interaction inference are all patterns we can borrow when designing our own perturbation predictors and foundation-model priors (Track C).

## Limitations / open questions
- A preprint benchmarked only against GEARS, a linear model, SALT, and mean-shift baselines; no comparison to newer perturbation foundation models.
- Cross-line transfer degrades for cell-type-specific pathways (e.g. erythroid differentiation); generalization is bounded by pathway similarity between contexts.
- Potentiation/redundancy gene-interaction types remain hard for all methods, MORPH included.
- Best prior (DepMap) is itself experimental perturbation data, which may not exist for arbitrary new contexts; the mixture-of-experts over priors gave no substantial gain.
