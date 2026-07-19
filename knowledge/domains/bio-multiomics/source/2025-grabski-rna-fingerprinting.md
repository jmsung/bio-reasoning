---
source_url: https://doi.org/10.1101/2025.09.19.676866
source_type: papers
title: "Mapping transcriptional responses to cellular perturbation dictionaries with RNA fingerprinting"
author: Isabella N. Grabski et al.
retrieved: 2026-07-16
doi: 10.1101/2025.09.19.676866
---

# Mapping transcriptional responses to cellular perturbation dictionaries with RNA fingerprinting

**Authors:** Isabella N. Grabski, Junsuk Lee, John Blair, Carol Dalgarno, Isabella Mascio, Alexandra Bradu, David A. Knowles, Rahul Satija
**Year:** 2025
**Venue:** bioRxiv (preprint; Satija Lab / New York Genome Center)

## Abstract
RNA fingerprinting is a statistical framework that maps transcriptional responses from new single-cell experiments onto reference perturbation dictionaries (CRISPRi screens, drug atlases, cytokine stimulation panels). It learns denoised perturbation "fingerprints" via a multi-condition factor model, then probabilistically assigns query cells to one or more candidate perturbations using a Bayesian regression borrowed from statistical genetics, summarizing uncertainty as credible sets with Bayes factors. The method inverts the usual perturbation-prediction problem: rather than predicting a response from a perturbation, it infers the causal perturbation(s) from an observed transcriptome.

## Key contributions
- A reference-mapping (not response-prediction) framing that assigns causal perturbation identity to query single cells.
- Denoised, reproducible perturbation fingerprints from a rank-one multi-condition factor model, outperforming bulk log-fold-change as a signal.
- Probabilistic assignment with Bayesian credible sets + Bayes factors, allowing principled "unassigned" calls and combinatorial (multi-set) resolution.
- New ground-truth benchmarks for perturbation identification, including combinatorial CaRPool-seq masking.

## Methods
Each perturbation's effect is modeled as a denoised low-rank fingerprint over Pearson-residual expression, fit per condition. Query cells are mapped by Bayesian linear regression over the fingerprint dictionary; posterior coefficients yield credible sets (candidate perturbations) with Bayes factors quantifying evidence strength. Related fingerprints can be merged into "joint fingerprints" to borrow strength and test additive-vs-shared explanations. Performance is scored with per-perturbation F1 (harmonic mean of cell-level sensitivity and precision), counting "unassigned" as incorrect.

## Key results
- **Cross-context single-cell:** mapping K562-learned fingerprints onto HEK293FT queries, 37% of cells assigned, of which 81% had the correct perturbation in the top credible set.
- **Genome scale:** 4,098 fingerprints from a genome-wide screen; group-level assignment for 87% of query perturbations, 71% top-set accuracy (>90% for high-Bayes-factor calls), modal credible-set length of 1.
- **Single cell at scale:** 230,179 cells mapped; 55% of assigned cells correct in top set; 96% of held-out non-targeting cells correctly left unassigned (strong false-positive control).
- **Best F1** vs comparators (elastic net second); unlike elastic net, robust when target-gene knockdown signal is removed — showing it does not merely read out CRISPRi target dropout.
- **Combinatorial:** on CaRPool-seq dual perturbations, correctly recovered both perturbations in 80% (group level); resolved two credible sets in 69% of uncorrelated pairs; recovered heterogeneity at single-cell resolution.
- **Biology:** nominated RPL10/RPL24 as novel p53 regulators under ribosomal stress (validated by dsiRNA depletion + nutlin-3a rescue + western blot in A549); flagged HDAC6 inhibitors Ricolinostat/ACY-738 as non-selective (matching pan-HDAC fingerprints, confirmed by protein markers); resolved heterogeneous cytokine-driven B-cell responses in influenza-rechallenged mice using the Immune Dictionary.

## Why it matters for our work
This is directly relevant to the BioReasoning Challenge perturbation tracks (Track A/B up/down/none direction prediction). It is a complementary inverse task — inferring which perturbation produced a transcriptional state — but its core lessons transfer: (1) denoised fingerprints beat raw log-fold-change for weak/subtle perturbations, echoing our need to detect small direction signals; (2) principled abstention via Bayes factors is exactly the over/under-abstention lever we struggled with in Track B (LB 0.488, over-abstention); its calibrated "unassigned" with 96% non-targeting control is a model for when to predict "none"; (3) it reinforces that deep-learning perturbation-response models do not transfer to identification, and that simple linear/Bayesian baselines are strong — consistent with Ahlmann-Eltze's linear-baseline finding already in our wiki.

## Limitations / open questions
- Models only additive combinatorial effects; cannot capture synergistic responses, and accuracy degrades when one perturbation's signal dominates.
- Requires context-matched reference dictionaries; cross-cell-type divergence causes genuine failures (not just model error).
- RNA-only — no chromatin, splicing, protein, or morphology; authors propose multimodal extension.
- Linear/Bayesian by design; nonlinear/DNN variants are future work but would trade off interpretability and uncertainty quantification.
