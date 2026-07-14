<!-- synced from knowledge-base — do not edit here; change upstream and re-pull -->
---
type: source
kind: paper
confidentiality: public
visibility: global
primary: bio-foundation-models
domains: [bio-foundation-models]
title: Enhancing efficiency of protein language models with minimal wet-lab data through few-shot learning
authors: [Ziyi Zhou, Liang Zhang, Yuanxi Yu, Banghao Wu, Mingchen Li, Liang Hong, Pan Tan]
year: 2024
doi: 10.1038/s41467-024-49798-6
source_url: https://doi.org/10.1038/s41467-024-49798-6
drive_file_id: TODO
text_source: paperclip
ingested_by: agent
---

# Enhancing efficiency of protein language models with minimal wet-lab data through few-shot learning

## TL;DR
FSFP is a training strategy that fine-tunes pre-trained protein language models (PLMs) for mutational-fitness prediction using only ~20–100 labeled single-site mutants, combining meta-transfer learning, learning-to-rank, and LoRA to beat both zero-shot PLMs and supervised baselines on 87 deep-mutational-scanning datasets and to improve a real Phi29 DNA polymerase engineering campaign.

## Key findings
- **Problem framing.** Zero-shot PLMs (ESM-1v, ESM-2, SaProt) predict fitness without labels but cap out in accuracy and can't capture non-natural catalytic properties; supervised models need large mutagenesis datasets. FSFP fuses both regimes under extreme data scarcity.
- **Three components, all additive.** (1) **LoRA** parameter-efficient fine-tuning (rank r=16, ~1.84% of params trainable) prevents catastrophic overfitting that full fine-tuning (MSE) suffers — naive MSE fine-tuning actually *degrades* below zero-shot. (2) **Learning-to-rank** (ListMLE listwise loss) instead of regression, because relative mutant ranking matters more than absolute fitness in directed evolution; regression methods show poor MAE and unusable absolute outputs. (3) **Meta-transfer learning** (MAML) builds auxiliary tasks from the two most-similar ProteinGym proteins (by PLM embedding cosine similarity) plus a third task of GEMME MSA-derived pseudo-labels, giving a good LoRA initialization.
- **Benchmark gains.** Across ProteinGym's 87 DMS assays (~1.5M missense variants, 11 multi-site), FSFP boosts average Spearman by **~0.1 over zero-shot using only 20 labeled mutants**; gains grow with training size and are larger for multi-site mutants. SaProt (FSFP) is the top performer; ESM-1v and ESM-2 comparable. Significance: largest P=0.0079 (two-sided Mann–Whitney U) vs all baselines.
- **Beats ridge regression** (the Hsu et al. one-hot + density baseline), which fails to noticeably exceed zero-shot at n=20 and even hurts GEMME/ESM on multi-site mutants. FSFP also has much smaller standard errors → more stable.
- **Extrapolation.** FSFP keeps beating baselines on held-out positions (single-site mutants at unseen positions; multi-site mutants with no overlapping individual mutations), where ridge regression shows no clear gain even at n=100.
- **Robust to weak zero-shot.** On HIV Env, α-synuclein, GB1, TDP-43 — where some PLMs have near-zero or negative zero-shot correlation — FSFP still yields large gains; GEMME (the pseudo-label source) is not dominant, so FSFP generalizes rather than overfitting auxiliary tasks.
- **Wet-lab validation (Phi29 DNA polymerase thermostability).** Trained ESM-1v on the 20 zero-shot top mutants' measured Tm, then re-predicted: average Tm of top-20 improved >1 °C and **positive rate improved by 25%** (Fig. 5b). 9 of the new positive mutants were absent from training data.
- Meta-learning helps most when auxiliary datasets are large (≥500 mutants) and similar to the target; the MSA task buffers against dissimilar retrieved proteins. Embedding-similarity, MMseqs2, and Foldseek retrieval all perform comparably.

## Methods (brief)
In-silico benchmark on ProteinGym substitution set; training sets of 20/40/60/80/100 single-site mutants, rest as test, 5 random seeds, evaluated by Spearman and NDCG. Fitness scored as log-likelihood ratio of mutant vs wild-type residues (Meier et al.; SaProt variant adds 3Di structure tokens). MAML uses first-order approximation, inner step α=0.005, 5 inner steps; Monte Carlo cross-validation for early stopping. Wet-lab: codon-optimized Phi29 in pET28a/BL21(DE3), Ni-NTA purification, Tm by differential scanning fluorimetry (SYPRO Orange).

## Limitations
Demonstrated on stability/activity/expression DMS phenotypes and one wet-lab thermostability case (Phi29, N=20 per round); benefit depends on availability of similar auxiliary DMS datasets in ProteinGym and on GEMME-quality MSAs. Absolute fitness values are not reliable (only rankings). Proteins >1024 aa are truncated for ESM-1v. Tested only on ESM-1v/ESM-2/SaProt at 650M.

## Citations of interest
- Meier et al. 2021 (ESM-1v) — zero-shot variant-effect scoring and the log-likelihood-ratio fitness score FSFP builds on.
- Hsu et al. 2022 (Nat Biotechnol) — ridge regression on one-hot + density features; FSFP's primary supervised baseline.
- Laine et al. 2019 (GEMME) — MSA-based epistatic model used to generate pseudo-labels for the third meta-task.
- Finn et al. 2017 (MAML) — model-agnostic meta-learning algorithm for the meta-transfer stage.
- Hu et al. 2022 (LoRA) — low-rank adaptation enabling overfitting-resistant fine-tuning.
- Notin et al. 2022 / ProteinGym — the 87-dataset DMS benchmark used throughout.
- Su et al. 2024 (SaProt) — structure-aware PLM that is FSFP's top performer.
