---
source_url: https://doi.org/10.1101/2024.03.14.585078
source_type: papers
title: "Modeling interpretable correspondence between cell state and perturbation response with CellCap"
author: Yang Xu et al.
retrieved: 2026-07-16
doi: 10.1101/2024.03.14.585078
---

# Modeling interpretable correspondence between cell state and perturbation response with CellCap

**Authors:** Yang Xu, Stephen Fleming, Matthew Tegtmeyer, Steven A. McCarroll, Mehrtash Babadi
**Year:** 2024
**Venue:** bioRxiv (preprint)

## Abstract
CellCap is a deep generative model for end-to-end analysis of single-cell perturbation experiments (Perturb-seq / CROP-seq). Unlike methods that predict only the *average* cellular response and discard response heterogeneity, CellCap deconstructs cell-state-specific perturbation responses into a sparse dictionary of transcriptional "response programs" that individual perturbations and individual cells use to varying degrees. Two design choices give it interpretability: dot-product cross-attention between cell states and response programs, and a linearly-decoded latent space. On simulations plus two real datasets (pathogen-exposed monocytes; large-scale genetic Perturb-seq), CellCap recovers the correspondence between basal cell state and perturbation response and surfaces insights missed by prior analyses.

## Key contributions
- A linearly-decoded VAE that pushes nonlinearity out of the decoder and into latent-space algebra (attention), keeping outputs interpretable in gene-expression space.
- Sparse dictionary learning of shared/unique transcriptional "response programs" `w_qk`, reused across perturbations, with automatic relevance determination (ARD) to learn as few programs as needed.
- A scaled multi-head dot-product attention mechanism (basal state = query, perturbation keys `κ_pqk` = key, program usage = value) that models *why* a given cell responds a given way — the correspondence between basal state and response.

## Methods
CellCap is a probabilistic (negative-binomial) generative model. A deep nonlinear encoder infers each cell's "basal state" `z_basal` (intrinsic pre-perturbation cell state), with adversarial classifiers stripping perturbation and known covariate (batch/donor) information out of it — an idea borrowed from CPA. The perturbation shift `Δz_pert = Σ_q h_nq w_qk` is a linear combination of response programs, where usage `h_nq = β_nq · v_nq` comes from attention: `β_nq = softmax_q(κ_pq · z_basal)`. A single-layer linear decoder maps latent quantities (basal states and response programs alike) back to gene space, trading a small reconstruction-error increase for interpretability. Training balances reconstruction, adversarial, and ARD losses; a hyperparameter controls the accuracy-vs-conciseness (fewer programs) trade-off.

## Key results
- On 3 simulated scenarios (2 perturbations each, cell state co-varying with pseudotime), ARD correctly turned off unneeded programs and CellCap identified shared vs. unique programs; recovered per-cell response amplitudes correlated with ground truth (Pearson 0.884 / 0.859 for unique programs; −0.842 / −0.846 for the shared program's negative pseudotime correlation).
- Reanalyzing Oelen et al. pathogen-exposed monocytes, CellCap found the top PC of response-program usage was *time post-exposure* (3h vs 24h), not pathogen identity; 3h responses were interferon-driven in non-classical monocytes (FCGR3A, HES4), reproducing the original multi-step finding in one end-to-end model. It newly identified a monocyte sub-population with macrophage-differentiation potential (APOE, APOC1, RNASE1) 24h after *P. aeruginosa* exposure.
- On Norman et al. Perturb-seq (105 single + 131 combinatorial CRISPRa perturbations), CellCap turned 50 candidate programs down to 10; clustering of perturbation signatures agreed with Norman et al. and GEARS. It showed program Q43 (granulocyte, CEBPA/B/E) has per-cell response heterogeneity explained by basal granulocyte-marker expression and anti-correlated with M/G1 cell-cycle score (marker genes CENPA/E/F) — nuance missed by prior reanalyses.

## Why it matters for our work
CellCap is directly relevant to the BioReasoning Challenge perturbation-response tracks (Track A/B up/down/none prediction). It reframes the task away from a single average per-perturbation direction toward *cell-state-conditioned* responses: the same perturbation can up-regulate a program in one sub-population and not another, and basal state predicts which. That argues our up/down/none predictions may benefit from conditioning on cell state / basal context rather than treating a perturbation's effect as uniform, and its interpretable response-program decomposition offers a structured vocabulary (shared vs. perturbation-specific programs) for reasoning about mechanism. It also flags that bulk/averaged differential-expression labels can mask heterogeneity that changes the sign of a gene's response.

## Limitations / open questions
- Interpretation is sensitive to hyperparameters — especially the ARD weight (how many programs) and `γ` (basal-state alignment); the "shared vs. unique program" boundary can be ambiguous.
- CellCap is designed to *interpret* an existing dataset, not to *predict* unseen perturbations/combinations (CPA is stronger there) — so it is not a drop-in generalization engine.
- Requires a well-designed control group covering all pre-perturbation cell states; fails when perturbed cells undergo heavy reprogramming so their basal state no longer matches controls. Best trained on a single cell type for fine cell-state resolution.
- Evaluated only as a preprint on two datasets; no held-out predictive benchmark against GEARS/CPA on prediction metrics.
