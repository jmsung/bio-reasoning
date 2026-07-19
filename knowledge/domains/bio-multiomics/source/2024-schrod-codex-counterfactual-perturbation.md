---
source_url: https://doi.org/10.1093/bioinformatics/btae261
source_type: papers
title: "CODEX: COunterfactual Deep learning for the in silico EXploration of cancer cell line perturbations"
author: Stefan Schrod et al.
retrieved: 2026-07-16
doi: 10.1093/bioinformatics/btae261
---

# CODEX: COunterfactual Deep learning for the in silico EXploration of cancer cell line perturbations

**Authors:** Stefan Schrod, Helena U Zacharias, Tim Beißbarth, Anne-Christin Hauschild, Michael Altenbuchinger
**Year:** 2024
**Venue:** Bioinformatics

## Abstract
High-throughput screens (HTS) reveal causal effects of chemical and genetic perturbations on cancer cell lines, but the combinatorial explosion of possible interventions makes exhaustive experimental exploration intractable. CODEX is a counterfactual deep-learning framework for causal modeling of HTS data that links perturbations to downstream consequences. It predicts drug-specific cellular responses — both cell survival (drug synergy) and molecular alterations (perturbed transcriptomes) — and enables in silico exploration of drug combinations for bulk and single-cell HTS, including CRISPR-interference genetic modifications.

## Key contributions
- A single counterfactual DL architecture that unifies drug-synergy prediction, single-cell perturbation-profile prediction, and dosage-effect modeling.
- Perturbations are modeled as **structural network branches** (not covariates or chemical embeddings), letting the model learn each single-perturbation effect from observed *combinations* — enabling extrapolation to unseen combinations.
- A GO-based Jaccard similarity weighting scheme lets CODEX predict fully **unobserved** perturbations (e.g. new gene knockdowns) via proxy treatment branches of related genes.

## Methods
An unperturbed profile x is encoded to a shared latent state e(x); intervention-specific branches f_k transform it per active treatment; combinations are aggregated by summing active branch latents z = Σ t_i(j) f_j(e(x_i)) and passed through a shared decoder d that captures nonlinear combinatorial effects. Only active branches are evaluated (t=0 branches skipped). For synergy, an MSE loss on ZIP scores is used; for single-cell profiles, a Gaussian (mean + variance) loss per gene. Dosage enters as a categorical feature into each branch's first layer (not a separate branch), preserving dose extrapolation. Unseen perturbations use a normalized proxy vector t_i(j) = C·J_{j,j'} from GO pathway Jaccard similarity (similarities from GEARS/Roohani et al.).

## Key results
- **Drug synergy (DrugComb ZIP, 670 drugs / 2353 pairs / 75 cell lines, 5-fold CV):** CODEX had the highest PCC and lowest MSE for unseen cell lines and combinations; only MARSY beat it on SCC, with all other competitors substantially worse.
- **Combosciplex drug combinations:** CODEX raised median R² by 5.5% on top-50 DEGs vs CPA; linear ablation (lin-CODEX) already beats the linear baseline but is outperformed by CPA and CODEX, showing nonlinear decoding is crucial. Gains concentrated on weakly-supported held-out combinations (e.g. Alvespimycin).
- **Single-cell perturbation profiles (Norman two-gene knockouts):** CODEX beat CPA, GEARS, and GRN; top-20-DEG PCC of 0.98 (CODEX) vs 0.96 (lin-CODEX), 0.91 (CPA), 0.92 (GEARS), 0.82 (GRN).

## Why it matters for our work
CODEX is directly relevant to Track A/B-style perturbation-effect prediction: it predicts perturbed transcriptomes and the direction/magnitude of expression change for unseen genetic perturbations, which underlies our up/down/none prediction task. Its central idea — learn single-perturbation effects from combinations and share information across perturbations via a gene-gene prior (GO Jaccard) — is a concrete, non-foundation-model strategy for generalizing to unobserved knockdowns, complementing the gene-embedding and GRN-prior approaches in our wiki (GEARS, CPA). The counterfactual framing (predict the response you never observed) is exactly the BioReasoning generalization challenge.

## Limitations / open questions
- Requires the unperturbed control profile as input; assumes same-cell-line cultures act as technical replicates so counterfactuals are observable.
- Unseen-perturbation extrapolation hinges on the quality of the prior similarity (GO Jaccard); other priors (PPI, sequence) are suggested but untested.
- A distinct branch per perturbation still scales with the number of distinct interventions; combination generalization depends on redundancy across observed combinations.
- Focused on cancer cell lines and ZIP synergy / transcriptome outcomes; transfer to patient tumors is only motivated, not demonstrated here.
