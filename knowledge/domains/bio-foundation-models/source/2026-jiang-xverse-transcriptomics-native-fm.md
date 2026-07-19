---
source_url: https://doi.org/10.64898/2026.04.12.718016
source_type: papers
title: "xVERSE: A transcriptomics-native foundation model for universal cell representation and virtual cell synthesis"
author: Jiang & Xie
retrieved: 2026-07-16
doi: 10.64898/2026.04.12.718016
---

# xVERSE: A transcriptomics-native foundation model for universal cell representation and virtual cell synthesis

**Authors:** Xiaohui Jiang, Jichun Xie
**Year:** 2026
**Venue:** bioRxiv (10.64898/2026.04.12.718016)

## Abstract
Single-cell foundation models (scFMs) largely repurpose language-model
architectures (BERT/GPT-style, e.g. scGPT, Geneformer, Nicheformer) whose
sequential priors are ill-suited to unordered, sparse, high-dimensional
transcriptomes — and often fail to beat task-specific tools. xVERSE is a
"transcriptomics-native" generative foundation model that couples
batch-invariant representation learning with probabilistic generation of
expression profiles. It reports outperforming the best foundation model by
17.9% and the leading batch-correction method by 11.4% on representation, beats
the second-best spatial-imputation method by 34.3%, and uniquely synthesizes
virtual cells statistically indistinguishable from real ones (classifier
AUROC ≈ 0.5). Those high-fidelity virtual cells act as a data-augmentation
engine — resolving rare cell types from as few as 4 cells and improving
cross-modality prediction generalization across disease states.

## Key contributions
- First scFM to explicitly model the whole-transcriptome joint distribution and synthesize virtual cells indistinguishable from real ones (AUROC ≈ 0.5), not just learn embeddings.
- Unifies a batch-invariant biological embedding space with a generative (Poisson) decoder in one architecture.
- Introduces a per-gene "Gene2Cell" interpretability score for cell-type-defining genes and gene-panel optimization.

## Methods
xVERSE learns adaptive global gene embeddings plus tissue-specific gene-embedding
lookup values, transforms them into cell embeddings, and decodes cell/gene-specific
**Poisson** distributions over the entire transcriptome (parameters μ_bio and μ_sid),
optimized with a Poisson negative-log-likelihood reconstruction loss. A
**conditional adversarial** module (a sample discriminator predicting sample ID from
the biological latent) disentangles biological signal from batch/platform
confounders, yielding panel-invariant representations. Fine-tuning disables the
adversarial and cell-type-classification modules and optimizes reconstruction only.
Pretraining used a curated pan-tissue, pan-disease, cross-technology corpus of
**>89 million** cells: >70M droplet scRNA/snRNA-seq (64 tissues, 138 disease states)
and ~19M imaging-based spatial cells (Xenium v1/Prime, MERFISH, CosMx; 13 tissues).

## Key results
- Representation (zero-shot ASW, held-out liver + ALS motor-cortex atlases published after pretraining): +17.9% over scGPT on average; +19.4% / +15.8% on restricted spatial gene panels; 59.7% faster inference than scGPT.
- Beats the task-specific batch-correction method Harmony by +11.4% ASW in zero-shot, where other scFMs underperformed Harmony.
- Virtual-cell fidelity: HVG-ranking Pearson +9.2% over scVI; classifiers can't separate xVERSE virtual from real cells (AUROC ≈ 0.5) vs scVI's >0.7.
- Spatial imputation (CosMx lung NSCLC, top-50 HVG masking): zero-shot Pearson 0.4130 with no external reference (fine-tuned 0.4785), +34.3% over the second-best method (SpaGE/gimVI), which are reference-sensitive.
- Rare cells: augmenting 5 virtual cells/seed recovers minor populations (4–10 of 60 cells) where Leiden gave ARI ≈ 0; improves DEG recall (~+0.1) for a 4-cell dendritic population.
- Cross-modality (train on stable PBMC, test on NGD/CAV cohorts): ADT MSE −7.2–9.1%, Pearson +6.3–13.2%; B-cell isotype CE −10.0–31.3%, AUROC +>20%.

## Why it matters for our work
xVERSE is directly relevant to Track C (open-weights foundation models) as a strong,
recent scFM claiming it beats scGPT/Geneformer/Nicheformer *and* task-specific tools
zero-shot — a rebuttal to the "scFMs don't beat baselines" line running through our
wiki (Ahlmann-Eltze, Csendes, Kedzierska). Its virtual-cell synthesis is a concrete
data-augmentation lever: for Track A/B up/down/none prediction on scarce or imbalanced
perturbation/cell-state data, synthesized cells could rescue statistical power in rare
populations and improve generalization to unseen states — worth testing against our
current featurization. The Gene2Cell score also offers an interpretable gene-panel /
feature-selection signal.

## Limitations / open questions
- All headline numbers are self-reported preprint benchmarks on a handful of datasets; no independent/third-party benchmark (contrast our Hou and Xu scFM-benchmark pages) and possible cherry-picking of comparators.
- Weights/code availability and reproducibility for Track C use are unstated here — needs verification before we can run it.
- Poisson decoding assumes count distributions it may not capture (zero-inflation, overdispersion); "indistinguishable" is only tested via a trained binary classifier on select datasets.
- No evaluation on perturbation-response prediction (our Track A/B task) — augmentation benefit there is an untested extrapolation.
