<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: Rapid in silico directed evolution by a protein language model with EVOLVEpro
authors: [Kaiyi Jiang, Zhaoqing Yan, Matteo Di Bernardo, Samantha R. Sgrizzi, Lukas Villiger, Alisan Kayabolen, B. J. Kim, Josephine K. Carscadden, Masahiro Hiraizumi, Hiroshi Nishimasu, Jonathan S. Gootenberg, Omar O. Abudayyeh]
year: 2025
doi: 10.1126/science.adr6006
source_url: https://doi.org/10.1126/science.adr6006
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# Rapid in silico directed evolution by a protein language model with EVOLVEpro

## TL;DR
EVOLVEpro is a few-shot active-learning framework that pairs frozen ESM2-15B embeddings with a top-layer random-forest regressor to guide directed protein evolution in silico, yielding 2- to 515-fold activity gains across six therapeutic proteins with only a few rounds of low-N (≈10–16 variants/round) wet-lab testing.

## Key findings
- **Architecture.** Mean-pooled per-residue embeddings from a frozen ESM2-15B PLM feed a random-forest regressor (100 trees, Friedman-MSE splits) that ranks all single mutants; a top-N greedy selection policy picks the next round for experimental assay, iteratively retraining (Fig. 1A). No structure, MSA, alignment, or expert knowledge required — sequence in, ranked variants out.
- **Grid search (12 DMS benchmark datasets, 8 protein classes).** Winning config: random first round, raw (un-normalized) fitness, top-N selection, random-forest regressor, raw full-length embeddings. ESM2-15B beat all other embeddings (ESM-1, UniRep, ProtT5, ProteinBERT, Ankh, one-hot, integer) on 10/12 datasets (Fig. 1B). Random forest beat Gaussian-process and KNN regressors on 10/12. PCA dimensionality reduction did **not** help (full embeddings best on 9/12).
- **Active learning efficiency.** 5 rounds × 16 mutants ≈ pre-training on 160 mutants; 10 rounds ≈ 500 mutants. Significantly enhanced variants found by round 5 on every dataset, far exceeding zero-shot ESM2 and one-hot/integer baselines (Fig. 1C–D).
- **Antibodies (multi-objective: binding 4× weighted over expression).** C143 (anti–SARS-CoV-2 spike): best single mutant LC N28K → IC50 0.19 nM; best multi-mutant LC N28R/Q40K + HC R39K → **60 pM**. aCD71 (anti-TfR, >90% homology to Delpacibart): single HC S92A → 29 pM vs WT 551 pM; multi-mutant T70A/S92V → **19 pM** (35-fold vs WT; efficient-evolution only 8-fold). Notably 7/10 top C143 and all top aCD71 affinity gains sat in framework, not CDR, regions.
- **PsaCas12f miniature nuclease.** epPsaCas12f (I178A/K333V/K454P) reached ~50% indel at RNF2; averaged 23.3 ± 16.7% across 10 targets, 2.2–44-fold over other miniature effectors. Single-AAV in vivo edited mouse PCSK9 (~7% liver indels, ~50% serum PCSK9 drop at 14 d; max off-target 0.27%).
- **Prime editor (PE2 M-MLV RT).** Best mutant A660S generalized across 4 loci; surprisingly most gains clustered in the C-terminal RNase H domain. **Bxb1 integrase** → epBxb1 (T166R), up to 4-fold higher PASTE cargo insertion.
- **T7 RNA polymerase (3-objective: yield/translation/immunogenicity).** epT7 (T3M/G47A/E643G) gave up to ~57× translation and ~515× lower immunogenicity; 5-fold less dsRNA; ~2× circular-RNA yield; ~10× higher in vivo Fluc luminescence vs WT.
- **Fitness ≠ activity.** Across all six proteins, ESM2 masked-marginal "fitness" (pMMS) correlated weakly or negatively with measured activity (e.g. C143 −0.16; T7 −0.13), validating the necessity of the supervised top layer. Nominated mutations were rare/novel (median likelihood 0.01–0.04, below the 0.05 rare cutoff; 77–92% uncommon).

## Methods (brief)
Frozen ESM2-15B final-layer embeddings averaged over residues; scikit-learn random-forest regressor in an active-learning loop. Benchmarked on 12 published DMS datasets. Experimental readouts: ELISA IC50 (antibodies), NGS indel/insertion quantification (Cas12f, prime editor, Bxb1), luciferase translation + IFN-β/dsRNA ELISA (T7 RNAP). AlphaFold3 used post hoc to rationalize mutation mechanisms. Validation in cell lines, AAV/LNP delivery, and C57BL/6J mice (n=3 biological replicates typical).

## Limitations
Small per-assay N (typically n=3 replicates); greedy top-N selection risks missing distant fitness peaks; multi-mutant epistasis was only partly explored (1–2 combination rounds). Method requires a quantifiable, non-pooled assay per property; in vivo Cas12f editing was modest (~7%). Fitness–activity divergence was protein-dependent (Bxb1 showed weak positive correlation), so generality of the "fitness ≠ activity" claim is family-specific.

## Citations of interest
- Hie et al. 2024 (Nat. Biotechnol., ref 15) — zero-shot PLM antibody evolution; the primary baseline EVOLVEpro outperforms.
- Lin et al. 2023 / Rives et al. 2021 (ESM2, refs 7, 44) — the base PLM providing the embedding latent space.
- Biswas et al. 2021 (ref 30) — low-N protein engineering with UniRep; prior active-learning attempt that failed to generalize.
- Ruffolo et al. 2024 (OpenCRISPR, ref 19) — generative-PLM Cas9 reaching only WT-comparable activity, motivating the optimize-not-generate approach.
- Yarnall et al. 2022 (PASTE, ref 62) — Bxb1/LSR gene-insertion platform improved here via epBxb1.
- Dousis et al. 2023 (ref 68) — prior state-of-the-art low-immunogenicity T7 RNAP (G47A/884insG) benchmark beaten by epT7.
