---
source_url: https://doi.org/10.1038/s41592-023-01969-x
source_type: papers
title: "Learning single-cell perturbation responses using neural optimal transport"
author: Bunne, Stark, Gut, et al.
retrieved: 2026-07-16
doi: 10.1038/s41592-023-01969-x
---

# Learning single-cell perturbation responses using neural optimal transport

**Authors:** Charlotte Bunne, Stefan G. Stark, Gabriele Gut, Jacobo Sarabia del Castillo, Mitch Levesque, Kjong-Van Lehmann, Lucas Pelkmans, Andreas Krause, Gunnar Rätsch
**Year:** 2023
**Venue:** Nature Methods (2023)

## Abstract
Single-cell assays destroy the cell being measured, so we only ever observe
**unpaired** distributions of perturbed vs. non-perturbed cells — never the same
cell before and after. CellOT frames predicting a cell's perturbation response as
learning a map between these two unpaired distributions using **neural optimal
transport (OT)**, parameterized by **input convex neural networks (ICNNs)**. It
predicts individual single-cell drug responses (scRNA-seq and 4i multiplexed
protein imaging), and generalizes to unseen settings: holdout lupus patients
(IFN-β), glioblastoma patients (panobinostat), cross-species LPS responses, and
hematopoietic developmental trajectories.

## Key contributions
- Casts single-cell perturbation prediction as an **unpaired distribution-matching /
  OT map-learning** problem — no paired before/after cells required.
- **CellOT**: learns the Monge OT map via a pair of dual ICNN potentials (f, g),
  trained adversarially/iteratively; applied on autoencoder latents for scRNA-seq.
- Captures **higher moments** (heterogeneity, bimodality) of the perturbed
  population, not just the mean shift.

## Methods
OT gives both a distance (Wasserstein) and a geometry-aware coupling between two
distributions. CellOT parameterizes the convex Brenier potentials with ICNNs
(4 hidden layers, width 64; batch 256; lr 1e-4). The dual potentials f and g are
learned iteratively — f fixed while g runs an inner loop of 10 updates, Adam
optimizer, identical hyperparameters across all modalities/tasks. For
high-dimensional scRNA-seq, OT is applied in an autoencoder latent space.
Evaluation is distributional (no single-cell ground-truth pairing): **MMD** (RBF
kernel, top-50 marker genes for scRNA), **ℓ2 feature-mean distance**, and **r²**
correlation of feature means, with an "identity" baseline (return untreated) and an
"observed" lower bound (a second draw of real perturbed cells).

## Key results
- Benchmarked against scGEN, cAE, and PopAlign on melanoma 4i (35 treatments) and
  SciPlex-3 scRNA-seq: **CellOT outperforms baselines on MMD and r², typically by
  ~one order of magnitude**, approaching the "observed" lower bound while baselines
  barely beat identity.
- Autoencoder baselines capture only the population mean; CellOT recovers
  heterogeneous / bimodal marker-gene marginals (e.g. CXCL11, CCL2, APOBEC3A in
  lupus; Nfkb1, Oasl1, Mmp12, Cxcl5 across species).
- Generalizes **out-of-sample** (holdout lupus patients, IFN-β) and
  **out-of-distribution** (cross-species LPS: rat/mouse holdout; hematopoietic
  differentiation day-2 → day-4/6), with a smaller performance drop than baselines.

## Why it matters for our work
Directly relevant to the challenge's core question — predicting cellular response to
perturbation. CellOT is a strong classical (non-LLM) baseline for perturbation-effect
prediction and reframes the problem the way the data actually arrive: **unpaired
control vs. perturbed populations**. Its insistence on matching the *full
distribution* (MMD, higher moments) over the average effect is a useful evaluation
lens for Track A/B up/down/none calls — a method that only nails the mean can still
miss the biology. The OT "minimal-effort" prior (correlation structure preserved
under mild perturbation) is a concrete inductive bias worth contrasting against
foundation-model / LLM approaches.

## Limitations / open questions
- OT assumptions break for **strong perturbations** where the population
  redistributes drastically (correlation structure not preserved) — accuracy drops,
  as does short-vs-long-range developmental prediction.
- O.o.d. prediction only works when a **similar sample was seen unperturbed AND a
  similar perturbation response exists in training** — fails on patients with unique
  responses (small glioblastoma cohort).
- Base CellOT is **unconditional** (one map per perturbation); conditioning on
  covariates/patient metadata is left to follow-up work (CondOT).
