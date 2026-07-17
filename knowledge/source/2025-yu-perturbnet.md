---
source_url: https://doi.org/10.1038/s44320-025-00131-3
source_type: papers
title: "PerturbNet predicts single-cell responses to unseen chemical and genetic perturbations"
author: Yu et al. (Welch Lab, U-Michigan)
retrieved: 2026-07-16
doi: 10.1038/s44320-025-00131-3
---

# PerturbNet predicts single-cell responses to unseen chemical and genetic perturbations

**Authors:** Hengshi Yu, Weizhou Qian, Yuxuan Song, Joshua D Welch
**Year:** 2025
**Venue:** Molecular Systems Biology

## Abstract
PerturbNet is a deep generative model that predicts the full *distribution* of
single-cell gene expression states induced by an unseen perturbation, given only
the perturbation's features. It handles chemical perturbations (from SMILES
structure), CRISPRa/CRISPRi (from gene ontology annotations), and — for the first
time — missense coding variants (from ESM protein-sequence embeddings). It
accounts for covariates like dose and cell type, outperforms prior methods
especially for completely unseen genes, and was used to score all 7,847 point
mutations of GATA1, nominating large-effect variants that concentrate in the
DNA-contact region.

## Key contributions
- A modular three-network architecture: a perturbation encoder, a cell-state
  encoder, and a **conditional invertible neural network (cINN / normalizing
  flow)** mapping between them — approximating arbitrary conditional distributions.
- Predicts the **distribution** of post-perturbation cell states, not just the
  mean response — a departure from CPA/GEARS/Biolord.
- One framework spanning three perturbation modalities via swappable encoders:
  ChemicalVAE (drugs), GenotypeVAE (GO-annotation VAE over ~177M gene combos),
  and ESM embeddings (coding variants).
- First demonstration that amino-acid sequence embeddings predict expression
  changes from missense mutations.

## Methods
Representation networks are pretrained separately on large unpaired corpora
(ChemicalVAE on 250K ZINC molecules; GenotypeVAE on all 1- and 2-gene
combinations of 18,832 GO-annotated genes; ESM pretrained on 250M UniParc
sequences). The cINN is then trained on paired Perturb-seq data to translate
perturbation latents → cell-state latents, with optional covariates (dose, cell
type). Cell encoders use a VAE with Gaussian (normalized) or ZINB (raw count)
likelihood; ZINB on raw counts improved generalization. Evaluated on 5
train/test splits per dataset (LINCS-Drug, sci-Plex, Norman CRISPRa, Ursu
TP53/KRAS, Jorge GATA1) against chemCPA, Biolord, GEARS, a linear baseline, KNN,
and mean/median baselines.

## Key results
- **LINCS-Drug (unseen drugs):** best mean/median R² and Pearson — median R²
  0.919 vs 0.912 (KNN) / 0.899 (chemCPA).
- **sci-Plex (covariate-adjusted):** median R² 0.984 / mean 0.968, top of all
  models; DEG mean R² 0.865.
- **Norman CRISPRa (unseen genes):** highest mean/median R² on all genes and top-50
  DEGs; beats GEARS and baselines on all 5 splits, comparable to Biolord; clearest
  advantage on completely unseen genes and non-additive genetic interactions.
- **Coding variants:** on Jorge GATA1, significantly beats all baselines on
  large-effect genes; on Ursu it beats all but KNN.
- **GATA1 scan:** predicted 3 mutation classes (erythroid-depleted/-intermediate/
  -enriched); 8 of top-10 large-effect mutations sit in/near DNA-contact residues
  in the crystal structure, 4 of 10 at positions unseen in training; large
  side-chain volume changes correlate with disruptive effect.

## Why it matters for our work
PerturbNet is the distribution-level, generative counterpart to our up/down/none
Track A/B task. Its GenotypeVAE (GO-annotation gene embeddings) and its emphasis
on *unseen-gene generalization* speak directly to our gene-embedding and
direction-prediction work — GO-term representations are a concrete feature source
to try. The paper also validates that a strong **linear baseline** (Ahlmann-Eltze
et al) rivals deep methods on CRISPRa/CRISPRi, reinforcing our own finding that
naive baselines are hard to beat and that small CV can mislead. Its explicit
warning that mean/baseline models win when most perturbations have weak effects
mirrors our Track B over-abstention problem.

## Limitations / open questions
- Cannot predict effects of unseen perturbations on **unseen cell types**, nor
  coding variants in **unseen proteins**.
- Predicts distributions but assumes interventions are successful and non-toxic.
- On weak-effect perturbations, gains over simple baselines are only moderate —
  needs larger paired datasets to widen the gap.
- Distribution prediction ≠ our discrete up/down/none label; adapting it to the
  challenge metric is non-trivial.
