<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: Accurate proteome-wide missense variant effect prediction with AlphaMissense
authors: [Jun Cheng, Guido Novati, Joshua Pan, Clare Bycroft, Akvilė Žemgulytė, Taylor Applebaum, Alexander Pritzel, Lai Hong Wong, Michal Zielinski, Tobias Sargeant, Rosalia G. Schneider, Andrew W. Senior, John Jumper, Demis Hassabis, Pushmeet Kohli, Žiga Avsec]
year: 2023
doi: 10.1126/science.adg7492
source_url: https://doi.org/10.1126/science.adg7492
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# Accurate proteome-wide missense variant effect prediction with AlphaMissense

## TL;DR
AlphaMissense fine-tunes AlphaFold on human/primate population-frequency data to predict the pathogenicity of every possible missense variant in the human proteome, achieving state-of-the-art accuracy across clinical, de novo, and experimental benchmarks without training on curated disease labels.

## Key findings
- **Resource scale.** Predicts all 71M possible single-nucleotide missense variants (and 216M possible amino-acid substitutions) across 19,233 canonical human proteins. At a 90%-precision ClinVar cutoff, classifies **32% (22.8M) likely pathogenic, 57% (40.9M) likely benign** — 89% of variants resolved.
- **Architecture & training.** AlphaFold-derived model (minor mods), trained in two stages: (1) AF structure pretraining + masked protein language modeling; (2) fine-tuning on a binary classification objective where benign = variants frequent in human/primate populations (PrimateAI approach), pathogenic = unobserved variants matched by trinucleotide context. Pathogenicity = log-likelihood difference between reference and alternate amino acid. Final prediction averages 6 models; scores calibrated on a balanced ClinVar set via logistic regression to approximate pathogenicity probability.
- **Clinical benchmarks.** ClinVar class-balanced auROC **0.940** (18,924 variants) vs 0.911 for next-best non-ClinVar-trained model EVE (P=0.001); beats even models trained directly on ClinVar despite their data-leakage advantage. Gene-level mean auROC **0.950** vs 0.921 (EVE) on 612 genes. DDD de novo variants auROC 0.809 (on par with PrimateAI 0.797). Cancer hotspots auROC **0.907** vs 0.885 (VARITY).
- **Confident-call expansion.** Fraction of ClinVar variants confidently classified at 90% precision rises **+25.8 points (67.1% → 92.9%)** vs EVE.
- **MAVE agreement.** Highest mean Spearman vs experimental deep-mutational-scanning: **0.514** on ProteinGym (72 proteins) and 0.450 on a new 20-protein benchmark; improves on next-best for 62/72 ProteinGym proteins. Captures functional sub-domains — e.g. correctly flags the SHOC2 RVxF/PP1C-binding region and ~23-residue LRR periodicity; GCK catalytic Asp205 is top-ranked (0.999).
- **Cell essentiality.** Gene-mean pathogenicity correlates with LOEUF (Spearman −0.48) and predicts cell-essential genes better than LOEUF, especially for **short genes underpowered for cohort methods** (auROC 0.88 vs 0.81; 5.9-fold enrichment among small genes). Resolves SF3b subunits (e.g. PHF5A/SF3B7) that LOEUF cannot.
- **Complex-trait genetics.** Likely-pathogenic missense variants carry ~2× the UK Biobank trait associations of synonymous variants, statistically indistinguishable from pLoF (P=0.43); combining pathogenic + pLoF sets adds ~7000 testable genes (3.2× more candidate deleterious rare variants).

## Methods (brief)
Deep learning: AlphaFold backbone (48-layer Evoformer, MSA + pair representations) with elevated masked-MSA loss weight. Weak-label training avoids human curation — benign from population frequency, pathogenic from unobserved variants; self-distillation filters likely-benign unobserved variants. Evaluated against 13 prior methods (REVEL, EVE, ESM1b/1v, PrimateAI, VARITY, etc.) on held-out ClinVar, DDD, cancer hotspots, ProteinGym, and a curated MAVE set. Ablations show both structure pretraining and fine-tuning are jointly essential.

## Limitations
Predictions are calibrated probabilities only near 0/1 — scores in the 0.2–0.8 range are less reliable. Reduced performance on disordered-region residues. Training labels are inherently noisy (many unobserved variants are truly benign). Cannot predict structural changes upon mutation, and misclassifies some gain-of-function variants (e.g. hyperactivating GCK T65I) as ambiguous/benign. Model weights were not released.

## Citations of interest
- Jumper et al. 2021 (*Nature*) — AlphaFold, the structural backbone AlphaMissense fine-tunes.
- Frazer et al. 2021 (*Nature*) — EVE, the leading unsupervised generative baseline outperformed here.
- Sundaram et al. 2018 (*Nat Genet*) — PrimateAI, source of the population-frequency weak-labeling scheme.
- Notin et al. 2022 — Tranception/ProteinGym, the primary MAVE benchmark collection.
- Karczewski et al. 2020 (*Nature*) — gnomAD/LOEUF constraint metric compared against for gene essentiality.
- Rives et al. 2021 / Lin et al. 2023 — ESM protein language models, the log-likelihood-ratio paradigm and competing predictors.
